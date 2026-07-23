"""
Verify an LND ``signmessage`` signature without running a Lightning node.

A publsp LSP signs its Nostr pubkey with its LN node key and advertises the
result as ``lsp_sig`` (see ``marketplace/lsp.py``), binding the Nostr identity
that publishes an ad to the LN node that will receive payment. The customer
runs no node, so this module verifies that signature in pure Python.

LND's signature is a zbase32-encoded 65-byte recoverable ECDSA signature over
``sha256d("Lightning Signed Message:" + msg)``; the leading byte carries the
recovery id. Recovery uses ``secp256k1`` (already a dependency, via
``ln/invdecoder.py``).
"""
import hashlib
import logging
from typing import Optional

import secp256k1

logger = logging.getLogger(name=__name__)

# Zooko's base32 alphabet, as used by LND's SignMessage/VerifyMessage.
_ZBASE32 = "ybndrfg8ejkmcpqxot1uwisza345h769"
_LND_MSG_PREFIX = b"Lightning Signed Message:"
_SIG_LEN_BYTES = 65


def _zbase32_decode(s: str) -> bytes:
    bits = value = 0
    out = bytearray()
    for ch in s:
        idx = _ZBASE32.find(ch)
        if idx < 0:
            raise ValueError(f"invalid zbase32 character: {ch!r}")
        value = (value << 5) | idx
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((value >> bits) & 0xFF)
    return bytes(out)


def recover_signer_pubkey(message: str, zbase32_sig: str) -> Optional[str]:
    """
    Recover the compressed pubkey (hex) that produced an LND signmessage
    signature over ``message``. Returns ``None`` if the signature is malformed
    or recovery fails — never raises.
    """
    try:
        raw = _zbase32_decode(zbase32_sig)
        if len(raw) != _SIG_LEN_BYTES:
            raise ValueError(f"expected {_SIG_LEN_BYTES} bytes, got {len(raw)}")
        # header byte = 27 + recid (+4 when the signing key is compressed, as
        # LND's always is), so the recovery id is the low two bits.
        recid = (raw[0] - 27) & 0x03
        # LND hashes sha256d(prefix + msg); secp256k1.ecdsa_recover applies a
        # single sha256, so feed it the inner sha256 to reach the double hash.
        inner = hashlib.sha256(_LND_MSG_PREFIX + message.encode()).digest()
        pk = secp256k1.PublicKey()
        recoverable = pk.ecdsa_recoverable_deserialize(raw[1:_SIG_LEN_BYTES], recid)
        pk.public_key = pk.ecdsa_recover(inner, recoverable)
        return secp256k1.PublicKey(pk.public_key).serialize(compressed=True).hex()
    except Exception as e:
        logger.debug(f"could not recover signer pubkey: {e}")
        return None


def verify_lnd_signature(
        message: str,
        zbase32_sig: str,
        expected_pubkey: str) -> bool:
    """
    ``True`` iff ``zbase32_sig`` is a valid LND signmessage signature over
    ``message`` produced by ``expected_pubkey`` (compressed-hex node pubkey).
    """
    if not zbase32_sig or not expected_pubkey:
        return False
    recovered = recover_signer_pubkey(message, zbase32_sig)
    return recovered is not None and recovered.lower() == expected_pubkey.lower()
