from __future__ import annotations

import os

import pytest

from evolution.audit_trail import AuditTrailIntegrityError, HmacAuditTrail
from evolution.containment import containment_capabilities
from evolution.fitness import SortingEvaluator
from evolution.gp_engine import CONVENIENCE_PRIMITIVES
from evolution.gp_population import GPPopulation
from evolution.primitive_registry import PrimitiveApprovalError, require_approved_primitives


def test_default_profile_rejects_sorting_convenience_primitive_but_explicit_legacy_profile_allows_it() -> None:
    sort1 = next(primitive for primitive in CONVENIENCE_PRIMITIVES if primitive.name == "sort1")
    with pytest.raises(PrimitiveApprovalError, match="does not approve: sort1"):
        require_approved_primitives((sort1,))
    assert require_approved_primitives((sort1,), profile_name="legacy-artifact") == (sort1,)


def test_population_rejects_undeclared_convenience_profile() -> None:
    sort1 = next(primitive for primitive in CONVENIENCE_PRIMITIVES if primitive.name == "sort1")
    with pytest.raises(PrimitiveApprovalError, match="does not approve: sort1"):
        GPPopulation(SortingEvaluator(), primitives=(sort1,), population_size=4, seed=12)


def test_local_audit_chain_is_owner_only_and_detects_tampering(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    trail = HmacAuditTrail(path, b"v12-local-audit-signing-key")
    first = trail.append({"action": "primitive-profile", "profile": "default"})
    second = trail.append({"action": "evaluator-gate", "evaluator": "game-strategy", "allowed": False})
    assert first.previous_digest == "0" * 64
    assert second.previous_digest == first.digest
    assert [event.sequence for event in trail.verify()] == [0, 1]
    if os.name == "posix":
        assert path.stat().st_mode & 0o077 == 0
    path.write_text(path.read_text(encoding="utf-8").replace("default", "legacy-artifact"), encoding="utf-8")
    with pytest.raises(AuditTrailIntegrityError, match="mismatch"):
        trail.verify()


def test_containment_report_distinguishes_local_controls_from_absent_kernel_isolation() -> None:
    report = containment_capabilities()
    assert report.ast_validation and report.subprocess_boundary and report.wall_clock_timeout
    assert report.network_disabled_by_policy and report.filesystem_disabled_by_policy
    assert not report.kernel_network_namespace
    assert not report.seccomp_filter
    assert "not a kernel-enforced container" in report.non_claim
