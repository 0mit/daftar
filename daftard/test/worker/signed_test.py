#!/usr/bin/env python3
"""The worker's `signed`: a request's sitting environment applied while it runs, only the signing names taken, and
everything put back after — and a save's author the sitting's person where there is one, the handplace where not.

    python3 test/worker/signed_test.py
"""
import importlib.util
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', '..', 'python', 'garden_worker.py'), encoding='utf-8').read()
start = src.index('SIGNING = (')
end = src.index('def run_save(')
ns = {'os': os}
exec(compile(src[start:end], 'garden_worker.py', 'exec'), ns)   # the part under test, without a garden to stand in
signed, author = ns['signed'], ns['author']

os.environ.pop('DAFTARD_ASKPASS', None)
os.environ['GIT_CONFIG_COUNT'] = 'before'
assert author() == ('Daftar handplace', 'daftard@localhost'), author()
sign = {'GIT_AUTHOR_NAME': 'Ada', 'GIT_AUTHOR_EMAIL': 'ada@example.org', 'GIT_CONFIG_COUNT': '3',
        'DAFTARD_ASKPASS': 'http://127.0.0.1:1/askpass/t', 'PATH': '/nowhere', 'LD_PRELOAD': 'x.so'}
path = os.environ.get('PATH')
with signed(sign):
    assert os.environ['GIT_AUTHOR_NAME'] == 'Ada' and os.environ['GIT_CONFIG_COUNT'] == '3'
    assert os.environ.get('PATH') == path and 'LD_PRELOAD' not in os.environ, 'only the signing names are taken'
    assert author() == ('Ada', 'ada@example.org'), author()
assert os.environ['GIT_CONFIG_COUNT'] == 'before' and 'GIT_AUTHOR_NAME' not in os.environ \
    and 'DAFTARD_ASKPASS' not in os.environ, 'everything is put back'
try:
    with signed(sign):
        raise RuntimeError('a request that fails')
except RuntimeError:
    pass
assert 'DAFTARD_ASKPASS' not in os.environ, 'put back even when the request fails'
print('PASS: worker signed — applied while the request runs, only the signing names, put back after')

# ---- a save the clock refused is the machine's, said by the clock's own sentence
start = src.index('STAMP_REFUSED = ')
end = src.index('def person(')
ns2 = {'re': __import__('re')}
exec(compile(src[start:end], 'garden_worker.py', 'exec'), ns2)
said = ("save: NOT STAMPED: this machine's clock (box) cannot be shown within 30 s of its time sources — x: no answer. "
        "sam keeps this machine: set its clock right. — nothing written")
got = ns2['clock_refusal'](said)
assert got and got.startswith("this machine's clock (box)") and got.endswith('set its clock right.'), got
assert ns2['clock_refusal']('save: the gate refused it') is None
print('PASS: worker clock — a save the clock refused is answered by the clock\'s own sentence')
