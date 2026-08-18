from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v11_federation_secret_guidance_and_shipped_key_boundary_are_explicit() -> None:
    guidance = (ROOT / "docs" / "v11-federation-secret-safety.md").read_text(encoding="utf-8")
    federation = (ROOT / "evolution" / "v9_federation.py").read_text(encoding="utf-8")
    cli = (ROOT / "living_objects" / "cli.py").read_text(encoding="utf-8")

    assert "Never commit a federation secret" in guidance
    assert "environment variable" in guidance
    assert "Plaintext configuration-file parser" in guidance
    assert "open(" not in federation
    assert "os.getenv" in cli
