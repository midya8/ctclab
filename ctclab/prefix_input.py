"""Strict exact rational supplied-emission request boundary."""
from fractions import Fraction
import json
import re

KEYS = {'symbols', 'blank', 'frames', 'beam_width'}
SCHEMA = 'ctclab-rational-prefix-v1'
SCOPE = ('Supplied independent-frame CTC law; exact rational arithmetic. Beam mass is '
         'surviving path mass, not renormalized transcript probability or calibrated '
         'confidence. No model, language model, recognition benchmark or new method.')


def rational(value):
    if type(value) is not str or not re.fullmatch(r'(?:0|[1-9][0-9]{0,6})(?:/[1-9][0-9]{0,6})?', value):
        raise ValueError('Canonical nonnegative bounded rational strings required')
    q = Fraction(value)
    if str(q) != value or not 0 <= q <= 1 or max(q.numerator, q.denominator) > 1000000:
        raise ValueError('Canonical probability numerator/denominator at most 1000000 required')
    return q


def validate(request):
    if type(request) is not dict or set(request) != KEYS:
        raise ValueError('Exactly symbols, blank, frames, beam_width required')
    symbols, blank, frames, width = (request[k] for k in ('symbols', 'blank', 'frames', 'beam_width'))
    if type(symbols) is not list or not 2 <= len(symbols) <= 4:
        raise ValueError('2..4 symbols required')
    if any(type(s) is not str or not re.fullmatch(r'[!-~]{1,12}', s) for s in symbols) or len(set(symbols)) != len(symbols):
        raise ValueError('Unique 1..12 printable nonspace ASCII symbol labels required')
    if type(blank) is not int or not 0 <= blank < len(symbols):
        raise ValueError('Integer blank index required')
    if type(width) is not int or not 1 <= width <= 64:
        raise ValueError('Integer beam_width in 1..64 required')
    if type(frames) is not list or len(frames) > 6:
        raise ValueError('0..6 frames required')
    parsed = []
    for row in frames:
        if type(row) is not list or len(row) != len(symbols):
            raise ValueError('Aligned probability rows required')
        values = [rational(x) for x in row]
        if sum(values) != 1:
            raise ValueError('Each frame must sum exactly to one')
        parsed.append(values)
    return parsed


def loads(text, limit=65536):
    if type(text) is not str or len(text.encode('utf-8')) > limit:
        raise ValueError('Serialized byte limit exceeded')
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError('Duplicate JSON key')
            d[k] = v
        return d
    def bad(_):
        raise ValueError('Nonfinite JSON forbidden')
    def floating(_):
        raise ValueError('JSON float/exponent tokens forbidden')
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=bad, parse_float=floating)
    except (RecursionError, json.JSONDecodeError, OverflowError) as e:
        raise ValueError('Invalid or overly deep JSON') from e
