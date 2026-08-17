# BEAST v10 manuscript reproduction appendix

## Evidence status

This appendix accompanies the manuscript source as ancillary material. It is an evidence map, not a claim that the manuscript has been submitted, accepted, peer reviewed, or assigned an arXiv identifier.

The manuscript reports the frozen **BEAST v8 foundation revision `e2ea116`**. The current repository may contain later engineering changes; the historical revision is named here so the underlying evidence is reproducible without silently substituting later code.

## Frozen evidence map

| Repository path | Evidence role |
|---|---|
| `docs/v8-experiment-preregistration.md` | Declared seed list, protocol, and promotion rule. |
| `reports/v8/manhattan-distance/seed_*/trial.json` | Per-generation history, final tree, fresh suite, and execution boundary for each Manhattan trial. |
| `reports/v8/manhattan-distance/summary.json` | Aggregate five-seed Manhattan result. |
| `reports/v8/clean-sorting/summary.json` | Retained five-seed clean-sorting negative result. |
| `docs/v8-contamination-audit.json` | Task-level primitive-contamination classifications. |
| `docs/v8-benchmark-ledger.json` | Contamination-adjusted benchmark ledger. |
| `scripts/run_v8_multiseed.py` | Declared-trial runner. |
| `scripts/build_v9_paper_figure.py` | Figure generator that reads persisted histories. |

## Reproduction commands

The commands below are execution instructions, not an instruction to run an unbounded or externally connected system.

```bash
# Check out the evidence revision and run core integrity contracts.
git checkout e2ea116
APP_ENV=dev JWT_SECRET='v7-local-test-secret' pytest -q \
  evolution/test_checkpoint_fidelity.py evolution/test_clean_sorting.py \
  evolution/test_proof_benchmark.py

# Re-execute the declared Manhattan study only after allocating the required compute.
APP_ENV=dev JWT_SECRET='v7-local-test-secret' \
  python scripts/run_v8_multiseed.py manhattan-distance --output-dir /tmp/v8-reproduction

# On the later v9 release tree, regenerate the manuscript figure from committed evidence.
python scripts/build_v9_paper_figure.py
```

## Reproduction boundaries

The original evidence concerns one bounded Manhattan-distance evaluator and a retained clean-sorting negative outcome. It does not demonstrate general intelligence, autonomous production modification, a public live service, a PyPI publication, an arXiv submission, or a 100,000-generation clean-sorting campaign.
