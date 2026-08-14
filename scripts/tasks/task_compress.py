from .common import LocalTaskDescriptor

TASK = LocalTaskDescriptor(
    "compress", "Compression research profile", "evolve a text compression strategy",
    ("fixed 10,000-character corpus", "round-trip preservation contract", "no network"),
    {"corpus_path": "data/gutenberg_excerpt.txt", "bytes": 10_000},
)
