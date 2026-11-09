# CTCLab

**One transcript. Many alignments.** CTC target marginalization, alignment posteriors and logit gradients from scratch, with an exhaustive finite-path oracle and an independent browser inspector.

[Live atlas](https://midya8.github.io/ctclab/) | [Equations, limits and sources](METHOD.md)

CTC is established work by Graves et al. This project makes its hidden sums inspectable. It does not train an acoustic model, use speech data, call a model API, or claim recognition-quality improvements.

## What you can inspect

- Every normalized log probability, blank-expanded target state and allowed transition.
- Every log-space alpha/beta cell, target-conditioned state/symbol posterior and logit gradient.
- Every complete frame path, collapsed transcript and aggregated transcript mass. Nothing is sampled or pruned.
- A concrete counterexample: with two uniform blank/A frames, greedy emits empty output (mass 0.25), while A has total mass 0.75.
- Repeated-label minimum lengths, nonzero blank index, empty input/target and likelihood underflow with finite log-loss.
- Editable full specification, complete cell records, paginated exhaustive paths/transcripts, current JSON export and stale-input invalidation.

## Run offline

```bash
python -m pip install .
ctclab --spec examples/repeat.json --json audit.json
# Or without installing:
python -m ctclab --spec examples/repeat.json --json audit.json
python -m http.server 8000 --directory docs
```

Specs have exactly `symbols`, `blank`, `logits`, `target`. Symbols are 2..4 unique printable ASCII labels; blank/target are indices. At most six frames, six target labels and 1,024 exhaustive paths. Logits are finite with magnitude at most 1,000,000. Native JSON is limited to 64KiB and rejects duplicate keys. Browser JSON.parse computes the parsed record and does not detect duplicate keys.

A valid diagnostic exits 0 even for an impossible target. Malformed input exits 2. Impossible loss/gradients are null, not silently zeroed. Probability zero can also mean underflow while the log probability remains finite. No batch or target-length reduction is applied.

Transcript canonical ranking uses 10^-8-nat log-score buckets, then lexicographic index order. Raw log scores are retained; greedy gap uses the raw maximum. This is an explicit numerical tie convention, not exact real-number ordering or a new decoder.

## Reproduce

```bash
python -m unittest discover -s tests -v
python tools/build_audits.py
npm test
bash tools/wheel_smoke.sh
```

25 Python tests include 90-digit Decimal enumeration of 90 small random controls and 300 central finite-difference logit-gradient checks. Twenty retained complete reports compare 5,764 numeric and 650 other leaves against independent scalar JavaScript. Actual Chrome verifies every displayed state/gradient/path/transcript row, all 176 complete cell records, 142 full gradient records, 449 full path records and 143 full transcript records, 176 circle positions/posteriors, 205 transition lines, exports, stale/invalid input and 320/390/1280 containment. The isolated installed-wheel check runs outside the checkout.

No production-scale, speed, speech/OCR quality, causal-importance or new-algorithm claim. All data are original synthetic controls. Python uses only the standard library; the inspector uses built-in browser APIs. MIT.
