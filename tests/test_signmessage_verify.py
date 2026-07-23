"""
Tests for the node-less LND signmessage verifier (flaw #5).

publsp LSPs sign their Nostr pubkey with their LN node key (`lsp_sig`) so a
customer can confirm an ad's advertised `lsp_pubkey` really controls the Nostr
identity that published it. The customer runs no node, so verification is done
in pure Python — these vectors are real `lncli signmessage` outputs, each
independently confirmed by LND's own `verifymessage` (valid=true,
pubkey=identity). No node is needed to run the tests.
"""
from publsp.ln.signmessage import recover_signer_pubkey, verify_lnd_signature

IDENTITY = "0337cc53cf8df4236806595e61fe08c23b754e6a11ba5ceee204e34b3b304a32e1"

# vector 1: a fixed test string
VEC1_MSG = "publsp signmessage test vector 2026-07-23"
VEC1_SIG = (
    "dhtmp3kyyarjdnewr7d56pgqk6xzz7ohz9xpo3qd66p1rufyn35kh"
    "ymfmxm537hnmesazqzky3ochsebnjikbud7387fasgmbp73jwro"
)
# vector 2: signing a 64-hex pubkey (the publsp lsp_sig pattern)
VEC2_MSG = IDENTITY
VEC2_SIG = (
    "rd7a6jgxrtc3wzj1s4cg35fy7179qmga5dpcyqooawtbkrt3batz"
    "cdeppipmq5nkrmceqkbh9p6h4nj8bjyz43eh45iir34dj3t1xtbn"
)


def test_recovers_signer_from_real_vectors():
    assert recover_signer_pubkey(VEC1_MSG, VEC1_SIG) == IDENTITY
    assert recover_signer_pubkey(VEC2_MSG, VEC2_SIG) == IDENTITY


def test_valid_signature_verifies():
    assert verify_lnd_signature(VEC1_MSG, VEC1_SIG, IDENTITY)
    assert verify_lnd_signature(VEC2_MSG, VEC2_SIG, IDENTITY)


def test_pubkey_comparison_is_case_insensitive():
    assert verify_lnd_signature(VEC1_MSG, VEC1_SIG, IDENTITY.upper())


def test_tampered_message_fails():
    assert not verify_lnd_signature(VEC1_MSG + "x", VEC1_SIG, IDENTITY)


def test_wrong_expected_pubkey_fails():
    # recovery still succeeds, but the recovered key isn't the claimed one
    other = "02" + "11" * 32
    assert not verify_lnd_signature(VEC1_MSG, VEC1_SIG, other)


def test_malformed_signature_is_false_not_raised():
    assert not verify_lnd_signature(VEC1_MSG, "not-valid-zbase32!", IDENTITY)
    assert not verify_lnd_signature(VEC1_MSG, "short", IDENTITY)
    assert not verify_lnd_signature(VEC1_MSG, "", IDENTITY)
    assert recover_signer_pubkey(VEC1_MSG, "short") is None


def test_empty_expected_pubkey_fails():
    assert not verify_lnd_signature(VEC1_MSG, VEC1_SIG, "")
