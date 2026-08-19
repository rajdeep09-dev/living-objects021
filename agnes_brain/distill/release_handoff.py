"""D5 guarded GGUF release-handoff preflight entrypoint."""

from agnes_brain.d5_gguf_handoff import gguf_handoff_preflight, main

__all__ = ["gguf_handoff_preflight"]

if __name__ == "__main__":
    main()
