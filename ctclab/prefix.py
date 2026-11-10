"""Exact finite CTC prefix beam audit. No training or language model."""
from copy import deepcopy
from fractions import Fraction as F
from .prefix_input import SCHEMA, SCOPE, validate


def _advance(states, row, blank, trace=False):
    out, edges = {}, []
    def add(source, destination, kind, endpoint, value, token):
        if not value:
            return
        out.setdefault(destination, [F(0), F(0)])[endpoint] += value
        if trace:
            edges.append(dict(source=list(source), destination=list(destination), kind=kind,
                              token=token, endpoint='blank' if endpoint == 0 else 'nonblank', mass=str(value)))
    for p in sorted(states):
        pb, pn = states[p]
        add(p, p, 'blank', 0, (pb+pn)*row[blank], blank)
        for c in range(len(row)):
            if c == blank:
                continue
            if p and p[-1] == c:
                add(p, p, 'continue_run', 1, pn*row[c], c)
                add(p, p+(c,), 'repeat_after_blank', 1, pb*row[c], c)
            else:
                add(p, p+(c,), 'extend', 1, (pb+pn)*row[c], c)
    return out, edges


def _ranking(states):
    return sorted(states, key=lambda p: (-sum(states[p]), p))


def audit_prefix(request):
    rows = validate(request)
    blank, width = request['blank'], request['beam_width']
    beam = {(): [F(1), F(0)]}
    full = {(): [F(1), F(0)]}
    steps = []
    previous_mass = F(1)
    for t, row in enumerate(rows):
        full, _ = _advance(full, row, blank)
        candidates, edges = _advance(beam, row, blank, True)
        ranked = _ranking(candidates)
        keep = set(ranked[:width])
        retained = sum((sum(candidates[p]) for p in keep), F(0))
        records = []
        for rank, p in enumerate(ranked):
            pb, pn = candidates[p]
            records.append(dict(prefix=list(p), blank_mass=str(pb), nonblank_mass=str(pn),
                                mass=str(pb+pn), full_mass=str(sum(full[p])),
                                missing_mass=str(sum(full[p])-pb-pn), rank=rank+1, kept=p in keep))
        steps.append(dict(frame=t, incoming_mass=str(previous_mass), candidate_mass=str(sum((sum(v)for v in candidates.values()),F(0))),
                          discarded_here=str(previous_mass-retained), retained_mass=str(retained),
                          discarded_total=str(1-retained), transitions=edges, candidates=records))
        beam = {p: candidates[p] for p in ranked[:width]}
        previous_mass = retained
    winner = _ranking(beam)[0]
    exact_order = _ranking(full)
    best_mass = sum(full[exact_order[0]])
    exact_winners = [list(p) for p in exact_order if sum(full[p]) == best_mass]
    greedy = [max(range(len(row)), key=lambda c: (row[c], -c)) for row in rows]
    collapsed = []
    for t, c in enumerate(greedy):
        if c != blank and (t == 0 or c != greedy[t-1]):
            collapsed.append(c)
    lost = 1-previous_mass
    runner = max((sum(v) for p, v in beam.items() if p != winner), default=F(0))
    lower = sum(beam[winner])
    # Every other transcript's full mass <= its retained mass + all lost mass.
    certificate = lower > runner+lost
    transcripts = []
    for rank, p in enumerate(exact_order):
        v = beam.get(p, [F(0), F(0)])
        transcripts.append(dict(prefix=list(p), full_mass=str(sum(full[p])), retained_mass=str(sum(v)),
                                missing_mass=str(sum(full[p])-sum(v)), exact_rank=rank+1))
    return dict(schema=SCHEMA, scope=SCOPE, request=deepcopy(request), steps=steps,
                greedy_path=greedy, greedy_transcript=collapsed, greedy_transcript_mass=str(sum(full.get(tuple(collapsed),[F(0)]))),
                beam_winner=list(winner), beam_winner_retained_mass=str(lower), beam_winner_full_mass=str(sum(full[winner])),
                exact_winners=exact_winners, exact_best_mass=str(best_mass),
                exact_regret=str(best_mass-sum(full[winner])), retained_mass=str(previous_mass), discarded_mass=str(lost),
                other_retained_max=str(runner), sufficient_unique_map=certificate,
                transcripts=transcripts)
