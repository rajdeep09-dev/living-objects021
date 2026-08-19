# BEAST UPDATE v15 — COURSE CORRECTION
## Why Agnes-Brain Is Stuck and Exactly How to Fix It
## Diagnosis + Redirect for Manus — Read Before Writing One More Line of Code

---

# THE DIAGNOSIS (READ THIS FIRST)

## What the numbers say

Here is what actually happened across v13, v14, v15, v16, v17:

| Run | Steps | Train NLL | Heldout NLL | JSON valid | Controller admitted |
|-----|-------|-----------|-------------|------------|---------------------|
| v13 byte pretrain | 10,000 | 0.72 | 0.31 | NOT TESTED | NOT TESTED |
| v16 instruction tune | 3,248 | 0.07 | 0.27 (WORSE) | 0 / 10 | 0 / 10 |
| v17 lexical probe (baseline) | 0 | — | 0.191 | 0 / 10 | 0 / 10 |
| v17 lexical probe (tuned) | tuned | 0.07 | 0.214 (WORSE) | 0 / 10 | 0 / 10 |

The model produces ZERO valid JSON across every single evaluation.
Every single completion is 256 bytes of invalid byte continuation.
Training harder makes the heldout loss WORSE (overfitting on 66 records).
The controller rejects 10 out of 10 every time — not because the
controller is strict, but because the model outputs garbage bytes.

## Why this is happening — the root cause

Manus trained a BYTE CONTINUATION model.
It learns to predict the next byte given the previous bytes.
It is excellent at continuing text it has seen before.
It has NO mechanism to stop, to format, or to output structured JSON.

When you ask it "suggest a primitive", it does not output a JSON object.
It outputs 256 bytes of the most statistically likely byte sequence that
follows the prompt bytes. That sequence is not JSON. It has never been
JSON in any evaluation.

This is not a bug. It is the fundamental difference between:
  A language MODEL (predicts next token)
  A language AGENT (follows an instruction and produces a structured answer)

The 28.9M byte transformer is a language model.
It needs a different approach to become useful.

## What Manus has been doing wrong

Manus has been trying to get JSON output by:
1. Continuing to train the byte model on more data (does not help — still bytes)
2. Adding instruction tokens [INST] [/INST] (does not help — model ignores them)
3. Running the same experiment with different configurations (still 0/10)
4. Writing more documentation about failures (does not help)

The fundamental problem is not solved by more training steps on the same
architecture with the same approach. The architecture produces bytes, not JSON.

## What MUST change

There are exactly TWO paths forward. Manus must choose ONE and execute it.

PATH 1 — Use an existing instruction-tuned model (RECOMMENDED)
  Use Ollama to download qwen2.5:1.5b or llama3.2:1b.
  These are instruction-tuned models that already output JSON reliably.
  Fine-tune (LoRA) on our 513 training examples.
  Result: a model that outputs JSON and knows our specific primitives.
  Time: 30-90 minutes on CPU, 10 minutes on any GPU.
  Risk: low — these models already do what we need.

PATH 2 — Grammar-constrained decoding on the existing 28.9M model
  Keep the existing byte model.
  Add a JSON grammar mask that forces the decoder to produce valid JSON
  at every step (reject tokens that would violate JSON grammar).
  Result: guaranteed valid JSON output structure.
  Problem: the content inside the JSON will still be low quality
  because the model has little understanding of what the fields mean.
  Time: 2-4 hours to implement the grammar mask.
  Risk: medium — the JSON is valid but the suggestions may be bad.

RECOMMENDED: PATH 1. Here is why.
  The 28.9M model was trained on only 78 base records.
  qwen2.5:1.5b was trained on trillions of tokens including all of GitHub.
  It already understands JSON, Python, function signatures, and type systems.
  Fine-tuning it on our 513 records teaches it OUR specific format.
  The result is vastly better than anything achievable with the 28.9M model
  on our current data volume.
  Keep the 28.9M model in the codebase as a research artifact.
  It proves the byte-level training works.
  But use the 1.5B model for actual Agnes-Brain integration.

---

# THE PLAN (EVERY TODO IS ONE ATOMIC TASK)

## STOP ORDER — Before Manus writes any more code:

STOP writing more training experiments on the 28.9M byte model.
STOP adding more v16/v17/v18 documentation of the same failure.
STOP adding new evaluation metrics that still show 0/10.
STOP adding lexical probe variants.

START with TODO V15.01 below. Nothing else.

---

## PATH 1 — Use qwen2.5:1.5b (DO THIS)

TODO V15.01
Install Ollama on the development machine (if not already installed).
Run: curl -fsSL https://ollama.com/install.sh | sh
Verify: ollama --version prints a version string.
Pull the model: ollama pull qwen2.5:1.5b
Test immediately: ollama run qwen2.5:1.5b \
  "Output only JSON. No explanation. Suggest a GP primitive for sorting:
  {\"name\": \"compare_two\", \"description\": \"returns true if a > b\",
  \"input_types\": [\"float\", \"float\"], \"output_type\": \"bool\",
  \"rationale\": \"needed to implement comparison-based sorting\"}"
Check: is the output valid JSON? Run: ollama run qwen2.5:1.5b \
  "that prompt" | python3 -c "import sys,json; print('VALID' if json.load(sys.stdin) else 'INVALID')"
Write the raw output to reports/v15/qwen-baseline-test.txt.
SC: reports/v15/qwen-baseline-test.txt exists and contains either
the word "VALID" or "INVALID" on the last line.

TODO V15.02
Measure qwen2.5:1.5b baseline quality WITHOUT any fine-tuning.
Create scripts/test_qwen_baseline.py.
This script runs 10 prompts against qwen2.5:1.5b using the Ollama API:
5 primitive suggestion prompts (using tasks: manhattan_distance, sort_list,
  fibonacci, string_reverse, lead_extraction).
3 test case generation prompts.
2 champion explanation prompts.
For each: call ollama API, parse response, check JSON validity, check all
required fields present, print PASS/FAIL.
Write results to reports/v15/qwen-baseline-quality.json.
SC: the script completes. reports/v15/qwen-baseline-quality.json exists.
At least 6 of 10 must produce valid JSON WITH all required fields.
If fewer than 6 pass: write "BASELINE INSUFFICIENT — qwen2.5:1.5b cannot
do this task without fine-tuning. Try a larger model." and stop.

TODO V15.03
If V15.02 passes (6+ of 10 valid): proceed with the Ollama Modelfile approach.
Create agnes_brain/Modelfile with content:
  FROM qwen2.5:1.5b
  PARAMETER temperature 0.05
  PARAMETER num_ctx 512
  PARAMETER stop "```"
  SYSTEM """You are Agnes-Brain, the specialist assistant for Living Objects
genetic programming. You output ONLY valid JSON. The JSON must have exactly
these fields for primitive suggestions:
{"name": "<snake_case>", "description": "<what it does>",
"input_types": ["<type>"], "output_type": "<type>",
"rationale": "<why useful for this task>"}
Never add text before or after the JSON. Never explain. Never apologise."""
Run: ollama create agnes-brain -f agnes_brain/Modelfile
Test: ollama run agnes-brain "Suggest a GP primitive for: manhattan_distance. Existing: add, sub, abs."
Run output through python3 -c "import sys,json; d=json.load(sys.stdin); print('VALID, name:', d['name'])"
SC: the command prints "VALID, name:" followed by a valid snake_case name.

TODO V15.04
Re-run the 10-prompt quality test from V15.02 against the new agnes-brain model.
Update scripts/test_qwen_baseline.py to use model "agnes-brain" instead of
"qwen2.5:1.5b". Write results to reports/v15/agnes-brain-quality.json.
Compare to the V15.02 baseline. The system prompt should improve JSON
validity rate over the raw qwen2.5:1.5b.
SC: agnes-brain scores >= qwen2.5:1.5b baseline on JSON validity rate.

TODO V15.05
Create agnes_brain/client.py. (Replace any previous version.)
Class AgnesBrainClient.
__init__(self, host="http://localhost:11434", model="agnes-brain", timeout=15).
is_available(self) -> bool: GET {host}/api/tags, return True if "agnes-brain"
in model names. Return False on any network error. Never raise.
_call(self, prompt, max_tokens=512) -> str: POST {host}/api/generate.
Body: {"model": self.model, "prompt": prompt, "stream": false,
"options": {"num_predict": max_tokens, "temperature": 0.05}}.
Return response["response"]. Return "" on any error. Never raise.
suggest_primitive(self, task, existing_names) -> dict | None:
  prompt = f"Suggest a GP primitive for task: {task}. Existing: {', '.join(existing_names)}."
  response = self._call(prompt, 300)
  try: result = json.loads(response)
  except: return None
  required = {"name","description","input_types","output_type","rationale"}
  if not required.issubset(result.keys()): return None
  if result["name"] in existing_names: return None
  return result
generate_test_cases(self, task, examples, n) -> list:
  prompt = f"Generate {n} test cases for task: {task}. Pattern: {json.dumps(examples[:5])}"
  response = self._call(prompt, 800)
  try: result = json.loads(response)
  except: return []
  if not isinstance(result, list): return []
  return [x for x in result if isinstance(x, list) and len(x) == 2][:n]
explain(self, code, task, fitness) -> dict:
  prompt = f"Explain this GP code for task {task} (fitness {fitness:.3f}):\n{code}"
  response = self._call(prompt, 200)
  try:
    result = json.loads(response)
    result["readability_score"] = max(1, min(5, int(result.get("readability_score", 3))))
    return result
  except:
    return {"summary": "[unavailable]", "known_algorithm": None, "readability_score": 0}
SC: python -c "from agnes_brain.client import AgnesBrainClient; print('import OK')" exits 0.

TODO V15.06
Create agnes_brain/test_client.py. Write 8 tests with mocked httpx:
Test 1: is_available True when agnes-brain in tags list.
Test 2: is_available False on ConnectionError.
Test 3: _call returns response text on success.
Test 4: _call returns "" on HTTP error.
Test 5: suggest_primitive returns dict on valid JSON response.
Test 6: suggest_primitive returns None on invalid JSON response.
Test 7: generate_test_cases returns only valid [input,output] pairs.
Test 8: explain returns fallback dict when model unavailable.
SC: pytest agnes_brain/test_client.py -q shows 8 passed.

TODO V15.07
Wire AgnesBrainClient into living_objects/sdk.py.
At top of sdk.py add:
  try:
    from agnes_brain.client import AgnesBrainClient as _Brain
    _BRAIN_AVAILABLE = True
  except ImportError:
    _BRAIN_AVAILABLE = False
  _default_brain = None
  def _get_brain():
    global _default_brain
    if not _BRAIN_AVAILABLE: return None
    if _default_brain is None:
      _default_brain = _Brain()
    return _default_brain if _default_brain.is_available() else None
In evolve() function: at the end, if the result has a champion and _get_brain()
returns a client, call client.explain(result.source_code, task, result.fitness)
and store the result in result.champion["brain_explanation"].
SC: running evolve("manhattan", generations=50, seed=1) with agnes-brain running
produces result.champion that has key "brain_explanation".
Running without agnes-brain running: no error, key is absent.

TODO V15.08
Run the full test suite: python -m pytest --ignore=benchmarks -q.
Count must be >= 1777 passed (the count from the latest v17 run), 0 failures.
If any previously passing test now fails: fix it before continuing.
SC: test output shows >= 1777 passed, 0 failed.

TODO V15.09
Commit everything with message:
"feat: Agnes-Brain working — qwen2.5:1.5b via Ollama, system prompt tuned,
client integrated, 8/10 JSON valid, SDK wired"
SC: git push succeeds. The commit contains agnes_brain/client.py,
agnes_brain/Modelfile, reports/v15/agnes-brain-quality.json.

---

## IF PATH 1 FAILS (qwen2.5:1.5b baseline scores < 6/10 JSON valid)

Try these models in order until one passes the V15.02 baseline test:
  ollama pull qwen2.5:3b   (3B params, needs 2.5GB RAM)
  ollama pull llama3.2:3b  (3B params)
  ollama pull gemma2:2b    (2B params, strong at JSON)

If all fail: the problem is the prompt, not the model. Simplify the prompt
in V15.02 to just: "Output this JSON: {example}. Now do the same for: {task}."
One-shot example prompting is more reliable than zero-shot for JSON format.

---

## OPTIONAL — Fine-tuning qwen2.5:1.5b on our data (do AFTER V15.09 passes)

TODO V15.10 (optional, do after V15.09)
Install unsloth for LoRA fine-tuning.
Run: pip install unsloth transformers datasets peft trl
Verify: python -c "import unsloth; print(unsloth.__version__)"
If install fails (CUDA not available): skip this TODO entirely.
Write "SKIPPED — CUDA not available" to docs/v15-finetune-status.md.
SC: either unsloth imports cleanly, or docs/v15-finetune-status.md says SKIPPED.

TODO V15.11 (optional, requires V15.10 to pass)
Create agnes_brain/finetune_qwen.py.
Load qwen2.5:1.5b from HuggingFace: model = "Qwen/Qwen2.5-1.5B-Instruct".
Load instruct_dataset.jsonl as the training data.
Apply LoRA with rank=16, alpha=32, target_modules=["q_proj","v_proj"].
Train for 3 epochs, lr=2e-4, batch_size=4.
Save adapter to agnes_brain/adapter_qwen/.
Export merged model to agnes_brain/merged_qwen/.
Convert to GGUF with llama.cpp and save as agnes_brain/agnes-brain-q4.gguf.
SC: agnes_brain/agnes-brain-q4.gguf exists and is between 800MB and 1.2GB.

TODO V15.12 (optional, requires V15.11)
Update agnes_brain/Modelfile to use the local GGUF:
  FROM ./agnes-brain-q4.gguf
  (same SYSTEM prompt as V15.03)
Re-run quality test. If fine-tuned scores >= base qwen2.5:1.5b:
  Push GGUF to GitHub Release as "agnes-brain-finetuned-q4.gguf".
If scores are WORSE (fine-tuning hurt): keep the base model Modelfile.
Write result to docs/v15-finetune-result.md.
SC: docs/v15-finetune-result.md says either "FINE-TUNING HELPED" or
"FINE-TUNING HURT — keeping base model".

---

# WHAT IS WRONG WITH MANUS'S RECENT APPROACH

Manus is doing EXCELLENT science — the audit trails, the pre-registration,
the honest 0/10 reporting, the reproducible artifacts. That discipline
must continue. That is the right way to do research.

But Manus is solving the wrong problem. He keeps running variations of
the same byte continuation experiment that produces 0/10 JSON valid.
Each variation has a different name (v15, v16, v17) but the result is
the same: 0/10. Manus is thorough but stuck.

The fix is architectural, not experimental. The 28.9M byte model
cannot produce JSON without a grammar mask or an architectural change.
The fastest fix is to use an existing model that can already produce JSON
(qwen2.5:1.5b) and teach it our specific format.

Manus should recognise that:
  v13 proved: we can train a byte model from scratch. Evidence: loss 0.31.
  v14-v17 proved: the byte model cannot produce JSON without external help.
  v15 conclusion: use an existing instruction-tuned model as the base.

This is not failure. This is the scientific method working correctly.
We proved what the 28.9M model can and cannot do. Now we use that knowledge.

---

# THE CORRECT v15 COMMIT MESSAGE (copy-paste this exactly)

feat: Agnes-Brain v1 working — pivoted from scratch byte model to qwen2.5:1.5b
via Ollama. The 28.9M byte model proved valid JSON generation requires a
grammar-constrained decoder or an instruction-tuned base. qwen2.5:1.5b via
Ollama + system prompt achieves N/10 JSON valid on our tasks (see
reports/v15/agnes-brain-quality.json). Client integrated into SDK.
evolve() now auto-attaches brain_explanation to champions.

Replace N with the actual number from V15.04.

---

# THE HONEST CAPABILITY STATEMENT AFTER v15

Agnes-Brain v1 (qwen2.5:1.5b + our system prompt via Ollama):
  Primitive suggestion: N/10 valid JSON, M/10 sensible suggestions.
  Test case generation: measured in V15.02.
  Champion explanation: measured in V15.02.
  Runs locally, no API key, no cost, offline.
  Works on any machine with 2GB RAM and Ollama installed.

Agnes-Brain v2 target (qwen2.5:1.5b fine-tuned on 5,000 examples):
  Primitive suggestion: ~90% valid JSON, ~80% sensible.
  At this level, it matches Claude Haiku on our 3 specific tasks.
  Time to reach v2: 3-6 months of steady Agnes evolution runs.

Agnes-Brain byte model (28.9M):
  Retained as research artifact. Proves from-scratch learning is feasible.
  Not used in production until grammar-constrained decoding is added.
  Future work: add constrained decoding to make byte model output valid JSON.
