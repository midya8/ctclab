# CTCLab

Inspect how CTC combines frame paths into transcript probabilities. The target
atlas shows alignment posteriors and logit gradients with an exhaustive
finite-path reference. A separate rational prefix inspector tracks what beam
pruning keeps and discards.

Both use small supplied synthetic controls. There is no acoustic model,
speech dataset or recognition-quality claim.

[Live atlas](https://midya8.github.io/ctclab/) | [Equations, limits and sources](METHOD.md)

CTC is established work by Graves et al. This project makes its hidden sums inspectable. It does not train an acoustic model, use speech data, call a model API, or claim recognition-quality improvements.

## Inspect the target atlas

- Every normalized log probability, blank-expanded target state and allowed transition.
- Every log-space alpha/beta cell, target-conditioned state/symbol posterior and logit gradient.
- Every complete frame path, collapsed transcript and aggregated transcript mass. Nothing is sampled or pruned.
- A concrete counterexample: with two uniform blank/A frames, greedy emits empty output (mass 0.25), while A has total mass 0.75.
- Repeated-label minimum lengths, nonzero blank index, empty input/target and likelihood underflow with finite log-loss.
- Editable full specification, complete cell records, paginated exhaustive paths/transcripts, current JSON export and stale-input invalidation.

## Two input contracts

The original target atlas accepts floating-point logits and computes log-space
CTC quantities. The prefix mode accepts exact rational frame laws and audits
permanent path pruning. They use separate APIs and report formats; a rational
prefix result is not a claim that the original floating-point output is exact.

The current suite has 34 Python tests and six Node/actual-Chrome tests,
including the earlier target-atlas checks. Each mode has its own installed-
package reproduction command below.

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

The original 25 Python tests, retained in the current suite, include 90-digit Decimal enumeration of 90 small random controls and 300 central finite-difference logit-gradient checks. Twenty retained complete reports compare 5,764 numeric and 650 other leaves against independent scalar JavaScript. Actual Chrome verifies every displayed state/gradient/path/transcript row, all 176 complete cell records, 142 full gradient records, 449 full path records and 143 full transcript records, 176 circle positions/posteriors, 205 transition lines, exports, stale/invalid input and 320/390/1280 containment. The isolated installed-wheel check runs outside the checkout.

No production-scale, speed, speech/OCR quality, causal-importance or new-algorithm claim. All data are original synthetic controls. Python uses only the standard library; the inspector uses built-in browser APIs. MIT.


## Inspect rational prefix pruning

[Open the rational prefix inspector](https://midya8.github.io/ctclab/prefix.html) · [Method, proof and limits](PREFIX.md)

The original floating-point target atlas stays unchanged. The separate mode audits finite CTC prefix pruning with exact supplied rational frame laws: blank/nonblank transitions, surviving and discarded path mass, greedy versus full transcript MAP, and a sufficient unique-MAP bound. An independent native checker enumerates paths; the browser uses a separate BigInt engine. Twelve original controls include a selected case where width 4 chooses a lower-probability transcript than width 3. This is a tiny bounded search audit, not a trained recognizer, held-out speech result, new CTC algorithm, confidence estimate or scalable decoder. Strict permanent path pruning deliberately does not restore previously discarded contributions.

```sh
python -m ctclab.prefix_cli audit --input examples/prefix-selection.json --output report.json
python -m ctclab.prefix_cli verify --input report.json
bash tools/prefix_wheel_smoke.sh
```

The prefix interface accepts 2-4 symbols, 0-6 independent categorical frames and width 1-64. Every rational row sums exactly to one. Reports retain every positive candidate, transition and final transcript. Editing clears stale browser evidence. See [PREFIX.md](PREFIX.md) for recurrence, conservation proof, the L > R + D bound, source-variant boundaries, controls and independent checks.
