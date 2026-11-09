# CTC contract and reproduction

## Established method

CTC (Graves et al., 2006) marginalizes latent frame alignments for an ordered transcript. For finite logits z[t,k], compute log p[t,k] by log-softmax. Each complete path pi has log probability sum_t log p[t,pi[t]]. Merge adjacent repeated indices first, then remove blanks. Thus [A,A,blank,A] collapses to [A,A], not [A]. The target probability is the sum over all paths collapsing to that target.

This project implements the established algorithm, not a new objective. Symbols are abstract class labels, not a tokenizer or learned vocabulary. There is no acoustic network, audio corpus, language model, training loop or external API.

## Forward/backward convention

Expand target y into e=[blank,y0,blank,y1,...,blank]. A state may stay, advance one position, or advance two only when the destination is not blank and differs from the source. Start in state 0 or state 1; finish in the last or penultimate state (only the last state for an empty target).

Alpha[t,s] includes the emission at t. In log space:

```
alpha[t,s] = log p[t,e[s]] + logsumexp(alpha[t-1,q] for allowed q -> s)
```

The target log probability is logsumexp over terminal alpha cells. Beta[t,s] excludes the current emission: initialize terminal beta to zero and other terminal cells to -infinity, then sum allowed next-state emission plus next beta. This differs from presentations where both alpha and beta include the current emission. Under this project's convention, state posterior is exp(alpha+beta-log P(y)); there is no extra emission division. Symbol posterior sums all states carrying the same symbol.

The unreduced single-example negative-log-likelihood gradient with respect to logits is p[t,k] minus target-conditioned symbol posterior[t,k]. This is not the derivative with respect to an unconstrained probability or an already-log-softmax tensor. No batching, padding masks, mean reduction or target-length normalization is implemented.

Adjacent repeats in the target require intervening blanks: minimum input frames = target length + number of adjacent equal target pairs. Finite logits give positive real probability for every symbol, so structural reachability determines whether the target has positive real probability. Empty input has mass one for the empty target and zero otherwise.

## Output and numerical contract

- `audit(spec)` is the validated public entry point. It returns input spec, complete dynamic witness, every exhaustive path, every transcript aggregate, greedy path, canonical best transcript and raw greedy log gap.
- Specs require exactly symbols/blank/logits/target. Symbols: 2..4 unique printable non-whitespace ASCII labels, 1..12 characters. Blank is an index; target excludes blank and has at most six labels. Integral JSON numbers such as 1.0 are accepted as indices consistently with JavaScript; Booleans and fractional indices are rejected.
- At most six frames and C^T <= 1,024 paths. Rectangular logits must be finite numeric values, excluding Booleans, with absolute value <= 10^6. There are no zero-probability masks or infinite logits.
- Native input files are <=64KiB with duplicate-key and nonfinite-token rejection. Browser text has the same size bound for ASCII specs but JSON.parse accepts duplicate keys and keeps the last parsed value. No claim of byte-identical parser behavior.
- Unreachable alpha/beta cells serialize as null, representing -infinity. Impossible target log probability, loss and posteriors/gradients serialize as null. The mathematical loss is infinite and its gradient is not defined by this implementation. We do not apply a zero-infinity convention.
- Ordinary probability fields may underflow to zero despite finite log probability/loss. The extreme-logit control demonstrates this explicitly. Exponentiated posterior rows can have ordinary floating-point error. Native and JS use independent arithmetic, checked within tolerance rather than bitwise equality.
- Canonical transcript ranking uses integer buckets floor(log_mass * 10^8 + 0.5), descending, then lexicographic numeric index order. This makes a declared 10^-8-nat tie resolution visible; raw scores are never overwritten. Close scores in the same bucket can have different raw masses. `greedy_is_canonical_best` refers to this convention. `greedy_log_gap` uses the maximum raw aggregate log mass minus greedy transcript raw log mass, not the canonical winner's rounded score. Bucket-boundary cases remain floating-point sensitive.
- Greedy frame ties use the smallest index. Complete path order is lexicographic indices. Paths and output masses are exhaustive, not prefix beam approximations. The chart shortens labels to six characters; tables and cell records retain complete labels. Human-readable tables use seven significant digits; JSON keeps full binary-float values.
- CLI exit 0 means a valid computation completed, including a valid impossible-target diagnostic. Invalid input exits 2. There is no quality gate.

## Independent evidence

The native forward/backward recursion is checked against separately enumerated paths and 90-digit Decimal softmax/path products on 90 seeded small controls. Symbol posteriors are independently accumulated from matching path probabilities. All per-frame gradients are compared to that reference, and 300 central finite differences check derivatives of the actual loss. Forty additional independently enumerated state-sequence controls check every state posterior and matching-path count. Collapse is independently checked with adjacent group enumeration through six frames. Empty, repeat, blank permutation, extreme-logit, normalization, transition and strict-input controls remain explicit.

Twenty complete native witnesses are retained. Independent scalar JavaScript compares 5,764 numeric and 650 other leaves. Actual Chrome verifies 176 state rows, 142 gradient rows, 449 exhaustive path rows and 143 transcript rows; all 176 complete cell records, 142 full gradient records, 449 full path records and 143 full transcript records; 176 SVG circles with positions/posteriors and 205 transition lines with positions; every summary card, invalid/stale behavior, complete JSON export and 320/390/1280 containment. Python tests run on 3.10-3.13; wheel reproduction uses an isolated environment outside the source checkout.

```bash
python -m unittest discover -s tests -v
python tools/build_audits.py
npm test
bash tools/wheel_smoke.sh
```

## Limits

Exhaustive enumeration is exponential and intentionally tiny. Forward/backward in isolation is efficient in sequence length times target length, but this audit includes the exhaustive oracle; no speed or production-scale claim is made. Synthetic logits do not establish recognition quality, representation quality or usefulness of alignments as timestamps. A posterior is a model-conditioned latent alignment, not observed timing or causal importance. No training or downstream benchmark was run.

## Sources and attribution

Implementation, independent checks and synthetic controls by Midya Rahmani. No external implementation code, dataset, audio, weights or diagrams copied. Sources were read November 9, 2026.

1. Graves, Fernandez, Gomez and Schmidhuber, ICML 2006, [Connectionist Temporal Classification](http://www.cs.toronto.edu/~graves/icml%5F2006.pdf): original collapse map, target path sum, forward/backward and softmax gradient. Primary algorithm source.
2. Hannun, Distill 2017, [Sequence Modeling with CTC](https://mlanthology.org/distill/2017/hannun2017distill-sequence/): accessible metadata/summary for the visual exposition of marginalizing alignments. The fetched anthology entry is a summary, not the full Distill article.
3. [PyTorch CTCLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CTCLoss.md): log-probability inputs, blank exclusion, reduction and zero_infinity conventions. CTCLab does not claim API compatibility, batch reduction or PyTorch-default mean behavior.
4. [TensorFlow ctc_loss](https://www.tensorflow.org/api_docs/python/tf/nn/ctc_loss): logits/softmax and blank-index conventions. CTCLab accepts finite logits but does not implement TensorFlow batching/padding.
5. Hasegawa-Johnson, Illinois ECE537 Fall 2022, [Lecture 21](https://courses.grainger.illinois.edu/ece537/fa2022/slides/lec21.pdf): educational recurrence/gradient exposition. Some slide prose calls forward/backward values best-path probabilities and a conclusion drops a gradient minus sign; CTCLab follows the original paper's total-probability sum and negative-log-loss derivative instead. We do not adopt the lecture's convergence comparisons.
6. Hannun, [prefix CTC decoder example](https://gist.github.com/awni/56369a90d03953e370f3964c826ed4b0), 2017: establishes a separate prefix-beam decoding approach for contrast. CTCLab does not copy or implement it.
7. [NumpyCTC](https://github.com/yehudabab/NumpyCTC), independent implementation README: additional collapse/path-sum context. Its probability-space gradients are not interchangeable with this project's logit gradients. No code copied.
