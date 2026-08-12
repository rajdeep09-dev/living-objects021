# P1 Continuity — Mimo Version

**Status:** 8/8 tests passing
**Improvements over Kimi:**
- Fixed `test_event_audit_trail` bug (now calls `load()` properly)
- Added `test_surprise_and_dormancy` — tests surprise-driven cognition and dormancy lifecycle
- Added `test_peer_communication` — tests peer-to-peer object communication
- All 8 tests passing

## What Mimo Improved
1. **Bug fix:** `test_event_audit_trail` now properly calls `load()` before checking for "loaded" event
2. **New test:** Surprise-driven cognition and dormancy lifecycle
3. **New test:** Peer-to-peer communication between objects
4. **Better assertions:** More specific checks, better error messages

## How to Run
```bash
cd prototypes/mimo/p1_continuity
python -m pytest test_living_object.py -v
```
