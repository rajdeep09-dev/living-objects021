"""Dependency-optional D3 LoRA entrypoint.  It only performs preflight checks."""

from agnes_brain.d3_lora_guard import lora_preflight, main

__all__ = ["lora_preflight"]

if __name__ == "__main__":
    main()
