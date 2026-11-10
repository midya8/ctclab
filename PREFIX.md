# Exact prefix evidence

CTCLab 0.2 adds a rational prefix-beam inspector alongside the unchanged floating-point target atlas. It asks a different question: which paths survive each search cut, and how much probability is lost? This is an implementation of established CTC decoding ideas, not a new decoding algorithm or a trained speech recognizer.

## Reproduce

```sh
python -m unittest discover -s tests -v
npm test
PYTHONPATH=. python tools/build_prefix_controls.py
bash tools/prefix_wheel_smoke.sh
python -m ctclab.prefix_cli audit --input examples/prefix-selection.json --output report.json
python -m ctclab.prefix_cli verify --input report.json
# Installed console entrypoint: ctclab-prefix audit --input request.json
```

`examples/prefix-selection.json` is the width-3 selected counterexample request. `prefix_controls.definitions()` supplies all twelve controls. The browser's Download evidence button exports the same complete report, which the native verifier can replay. Browser computation is local; there are no network API calls or uploads.

## The supplied law and its bounds

A request has exactly `symbols`, `blank`, `frames`, and `beam_width`. Symbols are 2-4 distinct printable nonspace ASCII strings of length 1-12. Blank is an integer token index; no spelling is reserved. There are 0-6 frames. Each frame has one canonical nonnegative rational string per symbol, each at most one, with numerator and denominator at most 1,000,000; its exact sum must be one. Beam width is an integer 1-64. This gives at most 4^6 = 4,096 complete frame paths.

Frames are independent categorical draws. A path's mass is the product of its frame probabilities. CTC collapse merges consecutive equal tokens and then removes blanks, so A,A becomes A while A,blank,A becomes A,A. Different token-index transcripts remain distinct even if their labels could be concatenated ambiguously. Tables separate labels with a centered dot; evidence uses index arrays.

Serialized requests are capped at 65,536 UTF-8 bytes. Serialized reports and CLI outputs are capped at 8 MiB. Duplicate keys, nonfinite values, JSON float/exponent tokens, noncanonical fractions, extra keys, booleans in integer fields, malformed shapes and out-of-bound inputs are refused. Library validation enforces the structural and numeric limits; byte limits belong to serialized entrypoints. CLI errors return 2, write no stdout report, and preserve any existing output. File writes use a temporary sibling and atomic replacement; input/output aliases are refused. Atomic replacement is not a crash-durability guarantee.

## Prefix recurrence

For prefix p, retain two exact masses: B(p), paths ending in blank, and N(p), paths ending in a nonblank run. Start with B(empty)=1, N(empty)=0. For frame law q and blank index b:

- Blank adds (B(p)+N(p))*q[b] to B'(p).
- If nonblank c equals p's last token, N(p)*q[c] adds to N'(p) (continuing the run), while B(p)*q[c] adds to N'(p+c) (repeat after blank).
- Otherwise (B(p)+N(p))*q[c] adds to N'(p+c).

All incoming contributions are summed before ranking. Zero contributions and zero-mass entries are omitted. Rank by decreasing B'+N', breaking exact ties with lexicographic token-index tuples. Keep the first `beam_width` prefixes. Blank and nonblank masses of a prefix are kept or discarded together. There is no score normalization, token threshold, language model, length bonus or additional pruning.

**Strict path survival:** once a path's collapsed prefix fails a cut, that path is gone permanently. A discarded prefix may later reappear through new paths from surviving prefixes, but its old paths are never restored. This choice is important: some published prefix-search variants recover contributions from previously discarded prefixes. This implementation does not implement those recovery variants.

An unpruned prefix recurrence computes the complete transcript law separately. Candidate `full_mass` is this unpruned marginal at that frame, before the current cut. `missing_mass` is full mass minus candidate surviving mass, so it measures earlier lost contributions, not the new cut. Final tables enumerate every positive-mass transcript, including ones absent from the final beam. `exact_rank` is a sequential position with lexicographic tie-breaking, not a competition rank; `exact_winners` separately lists every MAP tie.

## Conservation and a sufficient bound

Since each frame row sums to one, candidate mass equals incoming surviving mass. If S_t is retained mass after frame t and S_-1=1, the mass first discarded at that cut is S_(t-1)-S_t. Lost sets are disjoint by first discarded cut. Their sum D=1-S_final equals the sum of missing final transcript masses. No renormalization hides the loss.

Let w be the final beam winner, L its retained mass, R the largest retained mass of any other final transcript (zero for absent ones), and D total discarded mass. For every y != w, full(y) <= retained(y)+D <= R+D; full(w) >= L. Thus L > R+D proves w is the **unique MAP transcript of the supplied law**. This is a sufficient condition, not necessary. False means no certificate, not an incorrect answer. Exact ties cannot pass. The inspector also computes the true full-law regret, best full transcript mass minus full(w), using its small unpruned oracle. Neither the certificate nor regret says anything about acoustic correctness, calibration, authenticity or real speech recognition quality.

Greedy chooses each frame's largest emission, with smaller token index on ties, then collapses. It optimizes a path, not summed transcript probability. Two uniform blank/A frames give greedy empty (full mass 1/4) while A has full mass 3/4. At width one, lexicographic tie-breaking retains empty and discards total mass 3/4. Width two retains the whole law.

## Original controls and wider-beam counterexample

The twelve synthetic controls include greedy failure, complete retention, repeats separated by blank, repeated-run collapse, a nonzero blank index, empty input, width-3/4/64 versions of a selected five-frame case, a correct but uncertified narrow answer, a sufficient certificate and an exact MAP tie. They are development controls, not held-out evaluation.

The five-frame case was found in an original seeded search (seed 20839, selected at sample 7) over positive three-symbol rational rows. There is no claim that this is typical:

```
2/19 9/19 8/19
7/17 5/17 5/17
2/5  2/5  1/5
1/5  3/10 1/2
5/14 1/14 4/7
```

With symbols blank,A,B, width 3 chooses A,B with full mass 47403/226100 (the true MAP); width 4 chooses B,A,B with full mass 11691/56525, a smaller full mass, even though width 4 retains more total path mass. Width 64 retains the full law and has zero regret. Finite-width beam sets are not nested: paths newly retained at an early wider cut can displace other prefixes later. This is a concrete counterexample to monotonic finite-width quality, not a speed benchmark or a general ranking of widths.

## Independent checks

- Python generator uses Fraction prefix recurrence with a separate unpruned recurrence.
- Python verifier does not import the generator. It enumerates every frame path at each length, tracks first-cut survival, groups collapse and endpoint masses, and reconstructs the report and every positive transition from path semantics. It rejects unknown or altered report fields by exact structural comparison.
- Browser BigInt engine uses an independently written endpoint-state transition loop. Complete reports are compared against Python and then submitted to the native path verifier.
- Tests cover 120 seeded complete-path cases (43,110 complete paths), 384 exhaustive three-frame binary laws/blank-index/width cases, larger denominators, the maximum four-symbol/six-frame boundary, all twelve controls, 270 individually altered nonrequest primitive report leaves, strict parsing and atomic CLI refusal.
- JS tests compare 155 complete reports (2,763 candidates, 4,049 transitions, 3,322 transcripts). Actual Chrome exercises 36 control/width reports at 1280/390/320 pixels, 114 frame views, 477 candidate rows, 774 transition rows and 339 final-transcript rows, plus boundary/error/stale-state checks. Twelve trusted completed downloads pass native verification.
- A fresh wheel is installed into an isolated environment and tested outside the checkout. Nine module origins must be in site-packages; both new CLI entrypoints reproduce all twelve controls and reject 24 forged reports. The original target atlas's twenty reports and CLI are checked too.

Browser tests run sequentially, explicitly bring the page to the foreground before trusted pointer input, and wait for the debugger endpoint. Computation assertions and failed downloads are never silently retried. These checks support bounded implementation consistency, not a proof of arbitrary unbounded decoder correctness.

## Sources and variant boundaries

1. [Graves et al., Connectionist Temporal Classification, ICML 2006](https://www.cs.toronto.edu/~graves/icml_2006.pdf), especially the path law, collapse and section 3.2 decoding. Original prefix search is not identical to this finite strict-pruning inspector.
2. [Hannun, Sequence Modeling With CTC, Distill 2017](https://distill.pub/2017/ctc/), especially inference and blank/nonblank repeat handling. Used for the standard distinction between best path and summed transcript search.
3. [Hannun et al., First-Pass Large Vocabulary Continuous Speech Recognition using Bi-Directional Recurrent DNNs, 2014](https://arxiv.org/abs/1408.2873), section 3 and Algorithm 1 ([paper](http://arxiv.org/pdf/1408.2873)). Its algorithm includes discarded-prefix contribution recovery. We do not claim literal Algorithm 1 equivalence. The extracted repeated-token continuation line also differs from the endpoint path semantics used here; the implementation follows the recurrence above and independent path enumeration rather than transcribing that pseudocode.
4. [Borgholt, CTC Networks and Language Models: Prefix Beam Search Explained](https://medium.com/corti-ai/ctc-networks-and-language-models-prefix-beam-search-explained-c11d1ee23306), especially step 6, explicitly describes recovery of discarded prefixes. This is a variant boundary, not evidence that recovery happens here.
5. [Scheidl, Beam Search Decoding in CTC-trained Neural Networks](https://harald-scheidl.medium.com/beam-search-decoding-in-ctc-trained-neural-networks-5a889a3d85a7), used to cross-check additive blank/nonblank transitions and repeated-run continuation.
6. [Blank Collapse, 2022](https://arxiv.org/html/2210.17017), section 2.2, used to cross-check collapse/recurrence and why casual blank skipping is not automatically exact. This inspector does not skip frames.
7. [Recursive AI CTC documentation](https://recursiveai.org/onemodel/docs/ctc/), decoder discussion, a secondary cross-check of greedy versus prefix decoding.

No third-party implementation code or datasets were copied. Exact arithmetic removes rounding error for the supplied rational law, not search approximation. This bounded inspector is not optimized for long sequences, continuous training, model inference or production-scale decoding.
