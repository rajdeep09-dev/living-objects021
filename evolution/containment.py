"""Truthful capability report for the local generated-code containment boundary."""
from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass

from evolution.sandbox import ResourceLimits


@dataclass(frozen=True)
class ContainmentCapabilities:
    ast_validation: bool
    subprocess_boundary: bool
    wall_clock_timeout: bool
    output_cap: bool
    network_disabled_by_policy: bool
    filesystem_disabled_by_policy: bool
    posix_resource_limits_available: bool
    kernel_network_namespace: bool
    seccomp_filter: bool
    cgroup_quota: bool
    dedicated_os_user: bool
    read_only_root_filesystem: bool
    non_claim: str


def containment_capabilities(limits: ResourceLimits | None = None) -> ContainmentCapabilities:
    """Describe enforced local controls and explicitly list absent kernel controls."""
    active_limits = limits or ResourceLimits()
    return ContainmentCapabilities(
        ast_validation=True,
        subprocess_boundary=True,
        wall_clock_timeout=active_limits.max_cpu_ms > 0,
        output_cap=active_limits.max_output_bytes > 0,
        network_disabled_by_policy=not active_limits.allow_network,
        filesystem_disabled_by_policy=not active_limits.allow_filesystem,
        posix_resource_limits_available=(os.name == "posix" and not sys.platform.startswith("android")),
        kernel_network_namespace=False,
        seccomp_filter=False,
        cgroup_quota=False,
        dedicated_os_user=False,
        read_only_root_filesystem=False,
        non_claim=(
            "This local worker is not a kernel-enforced container. Deploy network namespaces, seccomp, "
            "cgroups, a dedicated OS user, and a read-only root filesystem before making that claim."
        ),
    )


def containment_capabilities_dict(limits: ResourceLimits | None = None) -> dict[str, object]:
    """Return the report as JSON-compatible evidence for an audit artifact."""
    return asdict(containment_capabilities(limits))


__all__ = ["ContainmentCapabilities", "containment_capabilities", "containment_capabilities_dict"]
