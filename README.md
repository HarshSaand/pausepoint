# PausePoint

## Inspect an actual output

![The credential request triggers a warning](docs/output-showcase.png)

Synthetic four-turn fixture processed by the real rule-based streaming engine. The risk index is not a calibrated fraud probability; llm_review is a routing label, not a claim an LLM ran.

[Open the result record](docs/output-example.json) · [Open the HTML report](docs/output-showcase.html)

Reproduce the underlying output:

```sh
python -m pausepoint.cli --conversation data/demo_conversation.jsonl
```


PausePoint follows a conversation message by message and identifies when ordinary-looking contact develops into social engineering. It is designed around early detection: the system records *when* risk became actionable, not only whether a completed conversation contained a scam.

## Use case

```text
"I'm calling from your bank's fraud team."
"We need to act immediately."
"Do not discuss this with anyone."
"Read the six-digit OTP to me."
```

After each message, PausePoint updates the conversation stage, risk score and supporting evidence. Explicit credential or payment cues can trigger a `warn_and_verify` routing label; intermediate scores produce `llm_review`. The runnable engine does not execute an LLM or deliver a user warning.

## Proposed learned-system flow (not the runnable baseline)

```mermaid
flowchart LR
    A[Incoming message] --> B[Normalise and redact]
    B --> C[Fast feature extraction]
    C --> D[Compact transformer]
    D --> E[Rolling conversation state]
    E --> F{Risk band}
    F -- Low --> G[Continue monitoring]
    F -- Medium --> H[Selective LLM analysis]
    F -- High --> I[Policy engine]
    H --> J[Evidence validation]
    J --> I
    I --> K[Monitor, warn or verify]
```

## Architecture: implemented baseline and proposed extensions

### Pre-processing

The runnable baseline applies Unicode NFKC normalisation, lowercasing and whitespace cleanup. It de-obfuscates spaced or punctuated terms such as `O.T.P`, masks URLs and extracts signals for phone numbers, currency amounts, OTPs, authority claims, urgency, secrecy, credential requests and transfers. A proposed extension would add a spaCy entity pass and PII placeholders before model inference.

### Fast path

The engine processes each new message and carries forward a decayed risk state; it retains up to eight recent records. The implemented scorer combines linguistic indicators with an exponentially weighted risk state. It predicts five interpretable stages: `benign`, `authority`, `urgency`, `isolation`, and `credential_or_payment`.

A proposed learned version would replace the rule score with `microsoft/deberta-v3-small`, fine-tuned as a multitask classifier for stage, scam risk and evidence spans, then exported to ONNX. Temperature scaling calibrates its probabilities. The target for the local fast path is p95 latency below 150–200 ms.

### Proposed selective LLM path (not implemented)

The proposed extension would send uncertain or escalating conversations to `Qwen2.5-7B-Instruct`, configured with temperature `0` and constrained JSON output over numbered conversation turns, extracted entities and fast-path scores. Required fields include `claimed_identity`, `requested_action`, `pressure_tactics`, `scam_stage` and `supporting_messages`.

The proposed validator would reject a response if its schema is invalid, a cited turn does not exist or the cited text does not support the extracted action. The LLM contributes evidence but never directly issues a warning or blocks a transaction.

### Post-processing

The implemented policy uses three threshold-based risk bands and a decayed risk state; it does not implement separate enter/exit thresholds for hysteresis. Explicit credential or transfer requests receive additional weight. A proposed full model would combine calibrated classifier probability, validated LLM fields and deterministic indicators with logistic regression. The baseline emits routing labels rather than rendered warnings; every decision records the score, stage, evidence and processing time.

## Candidate data for future training

- [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) for genuine single-message auxiliary training
- [Scam Conversation Corpus](https://zenodo.org/records/15212527) for multi-turn scammer interactions
- Reproducible, manually reviewed conversation scenarios for stage and early-detection evaluation

Single-message and constructed multi-turn results will be reported separately. Complete conversations are replayed one turn at a time, so the streaming model cannot use evidence from future messages.

## Planned evaluation (not completed benchmark results)

- stage macro-F1 and scam PR-AUC
- recall at a fixed false-positive rate
- first detection turn and early-detection AUC
- calibration error and Brier score
- evidence attribution accuracy
- LLM escalation and unsupported-evidence rates
- median and p95 latency
- messages per second and concurrent conversations
- compact-only versus LLM-only versus hybrid comparison

## Demonstration result

The included four-turn conversation moves from an authority claim to urgency, isolation and finally an OTP request. The streaming engine changes from monitoring to the `llm_review` routing label on turn three and `warn_and_verify` on turn four. Each decision records its evidence and local processing time.

The recorded replay is available in [`results/demo_stream.jsonl`](results/demo_stream.jsonl).

![PausePoint result preview showing the conversation stages and the warning decision](results/result-preview.png)

## Run the streaming replay

Requires Python 3.10+ and no external packages.

```bash
python3 -m pausepoint.cli --conversation data/demo_conversation.jsonl
```

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

## Limitations

- Public multi-turn scam data is smaller and less representative than production traffic.
- Legitimate fraud warnings can contain the same urgent language used by scammers.
- Code-switching, slang and adversarial spelling can reduce recall.
- Offline replay measures detection timing but not whether a warning prevents loss.
