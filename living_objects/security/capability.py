"""
Capability-based security model.

Objects communicate via explicit capability tokens.
No ambient authority. No global namespace.
"""

import hashlib
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Capability:
    """A capability token granting specific permissions on a target object."""

    holder_id: str
    target_id: str
    rights: List[str]
    token: str

    def __init__(self, holder_id: str, target_id: str, rights: List[str]):
        object.__setattr__(
            self,
            "token",
            hashlib.sha256(
                f"{holder_id}:{target_id}:{':'.join(sorted(rights))}".encode()
            ).hexdigest()[:32],
        )
        object.__setattr__(self, "holder_id", holder_id)
        object.__setattr__(self, "target_id", target_id)
        object.__setattr__(self, "rights", rights)


class CapabilityRegistry:
    """In-memory capability registry. Production would use persistent storage."""

    def __init__(self):
        self._caps: Dict[str, List[Capability]] = {}

    def grant(self, holder_id: str, target_id: str, rights: List[str]) -> Capability:
        cap = Capability(holder_id, target_id, rights)
        self._caps.setdefault(holder_id, []).append(cap)
        return cap

    def check(self, holder_id: str, target_id: str, right: str) -> bool:
        caps = self._caps.get(holder_id, [])
        for cap in caps:
            if cap.target_id == target_id and right in cap.rights:
                return True
        return False

    def revoke(self, holder_id: str, target_id: str, right: str) -> bool:
        caps = self._caps.get(holder_id, [])
        for cap in caps:
            if cap.target_id == target_id and right in cap.rights:
                caps.remove(cap)
                return True
        return False
