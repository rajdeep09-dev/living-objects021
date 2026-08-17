from __future__ import annotations

from copy import deepcopy

from evolution.v9_federation import SignedDiscoveryExchange, available_discoveries


PUBLISHER_KEY = b"publisher-key-for-v9-tests-00001"
RECEIVER_KEY = b"receiver-key-for-v9-tests-000002"


def _peers() -> tuple[SignedDiscoveryExchange, SignedDiscoveryExchange]:
    publisher = SignedDiscoveryExchange("publisher-a", PUBLISHER_KEY)
    receiver = SignedDiscoveryExchange("receiver-b", RECEIVER_KEY, trusted_peers={"publisher-a": PUBLISHER_KEY})
    return publisher, receiver


def test_exchange_lists_only_actual_persisted_eligible_discoveries() -> None:
    records = available_discoveries()

    assert len(records) == 5
    assert all(record["task"] == "manhattan-distance" for record in records)
    assert all(record["promotion_eligible"] is True for record in records)
    assert all(record["fresh_suite"]["correctness"] == 1.0 for record in records)


def test_trusted_peer_imports_signed_record_only_after_independent_local_evidence_check() -> None:
    publisher, receiver = _peers()
    record_id = available_discoveries()[0]["record_id"]
    envelope = publisher.publish(record_id, nonce="nonce-001", issued_at="2026-08-17T00:00:00+00:00")

    admission = receiver.import_envelope(envelope)

    assert admission.accepted is True
    assert admission.local_verification == "passed"
    assert receiver.admitted_records()[0]["record_id"] == record_id
    assert receiver.evidence_summary()["execution_boundary"]["generated_source_executed"] is False


def test_exchange_rejects_tampered_signature_and_replayed_envelope() -> None:
    publisher, receiver = _peers()
    record_id = available_discoveries()[0]["record_id"]
    envelope = publisher.publish(record_id, nonce="nonce-002")
    tampered = deepcopy(envelope)
    tampered["record"]["tree_sha256"] = "0" * 64

    assert receiver.import_envelope(tampered).reason == "signature verification failed"
    assert receiver.import_envelope(envelope).accepted is True
    assert receiver.import_envelope(envelope).reason == "replayed signed envelope"


def test_exchange_rejects_a_validly_resigned_payload_that_disagrees_with_local_evidence() -> None:
    publisher, receiver = _peers()
    record_id = available_discoveries()[0]["record_id"]
    envelope = publisher.publish(record_id, nonce="nonce-003")
    envelope["record"]["tree_sha256"] = "0" * 64
    envelope["signature"] = publisher._signature(PUBLISHER_KEY, envelope)

    admission = receiver.import_envelope(envelope)

    assert admission.accepted is False
    assert admission.reason == "remote record differs from independently verified local evidence"
    assert admission.local_verification == "failed"


def test_exchange_rejects_unknown_issuer_before_record_admission() -> None:
    publisher = SignedDiscoveryExchange("untrusted", b"untrusted-signer-key-000000000000")
    receiver = SignedDiscoveryExchange("receiver", RECEIVER_KEY)
    envelope = publisher.publish(available_discoveries()[0]["record_id"], nonce="nonce-004")

    admission = receiver.import_envelope(envelope)

    assert admission.accepted is False
    assert admission.reason == "issuer is not trusted"
    assert receiver.admitted_records() == []
