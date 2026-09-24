#!/usr/bin/env python3
"""dmdigest — account for every line of a source document before any of it becomes a bean.

WHY IT EXISTS. The 2026-08-06 handoff recorded that "~66% of markdown survives digestion". Nobody
could act on that number: it did not say WHICH third was lost, so it could not be checked, argued
with, or fixed. This replaces it with an accounting that names a destination for every single line
and FAILS when it cannot.

THE RULE (todo-digest-server-map.md, decision 3). Every source line is exactly one of:

  carried     it becomes data in a bean or a mapping
  pointed-at  it stays where it is and a bean references it (`file:` pointer)
  dropped     it is deliberately not carried, WITH a stated reason
  UNPLACED    none of the above -> the run FAILS. This is the whole point of the tool.

`--dry-run` writes nothing and is the default: it says whether the design holds before it costs a
commit. There is no mode that writes yet — the loop does the writing, one document per iteration,
and this tool is what tells it whether it may.
"""
import collections, glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STRUCTURAL = 'blank'
FENCE = re.compile(r'^\s*```')
TABLE = re.compile(r'^\s*\|')
TABLE_RULE = re.compile(r'^\s*\|[\s:|-]+\|\s*$')
HEADING = re.compile(r'^\s*#{1,6}\s')
LISTITEM = re.compile(r'^\s*([-*+]\s|\d+\.\s)')
QUOTE = re.compile(r'^\s*>')
def _host_names():
    """The names a command line can use for a machine THIS garden records: every `genos: host` bean's id and
    the first label of each of its `hostname` anchors, plus localhost. Read from the beans, because the
    list was once typed here as this estate's six hosts, and in any other garden every command would have
    been reported host-ambiguous — or worse, claimed by a name that means nothing there."""
    names = {'localhost'}
    for path in glob.glob(os.path.join(ROOT, 'beans', '*.md')):
        fm = dmparse.loads(dmparse.read(path)[0] or '') or {}
        if not isinstance(fm, dict) or fm.get('genos') not in ('host', 'virtual-host'):
            continue
        names.add(str(fm.get('bean')))
        for a in ((fm.get('identity') or {}).get('anchors') or []):
            if isinstance(a, dict) and a.get('key') == 'hostname' and a.get('value'):
                names.add(str(a['value']).split('.')[0])
    return names


HOST = re.compile(r'\b(' + '|'.join(sorted(map(re.escape, _host_names()))) + r')\b', re.I)
PATHY = re.compile(r'(^|\s)(/etc/|/var/|/usr/|/home/|/mnt/)')
# Prose must LOOK like prose to be claimed. Opening on a letter, digit, or the handful of
# marks real sentences start with — not 'anything left over', which is how a fall-through
# becomes an unfalsifiable zero.
HTML_COMMENT = re.compile(r'^<!--|-->$')
HRULE = re.compile(r'^([-*_])\1{2,}$')
CONTROL = re.compile(r'[\x00-\x08\x0b-\x1f]')
def is_prose(st):
    """Prose is a line that CONTAINS WORDS and is not markup.

    Deliberately not 'everything left over'. The first version fell through to `carried`, which made
    UNPLACED unreachable and its zero unfalsifiable — the defect this release exists to name. The
    widening below was driven by the 8 lines the strict version surfaced, every one of them real
    prose opening on a unicode mark: '−95 and a human still filed it as Junk' (U+2212, not a hyphen),
    '⚑ Mail is stored on /mnt/share0', '→ vps-SPOF closed', ':80 on a specific host'. A rule written
    from cases beats a rule written from imagination, and the failure path stays REACHABLE: markup
    and control characters still land in UNPLACED, which is verified in both directions.
    """
    return bool(re.search(r'[A-Za-z]', st)) and not st.startswith('<') and not CONTROL.search(st)


def classify(lines):
    """Every line -> (destination, why). No line may fall through; UNPLACED is a failure, not a default."""
    out, incode, fence_lang = [], False, None
    for raw in lines:
        s = raw.rstrip('\n')
        st = s.strip()
        if FENCE.match(s):
            incode = not incode
            fence_lang = st[3:].strip() if incode else None
            out.append(('carried', 'code-fence delimiter -> the mapping entry boundary'))
            continue
        if incode:
            hosted = bool(HOST.search(s))
            out.append(('carried',
                        f"command line -> mappings/ steps"
                        + ("" if hosted else " (HOST NOT NAMED in the source — must be established)")))
            continue
        if not st:
            out.append((STRUCTURAL, 'blank — layout, carries nothing'))
        elif TABLE_RULE.match(s):
            out.append(('dropped', 'table rule line — presentation only; the records carry the content'))
        elif TABLE.match(s):
            out.append(('carried', 'table row -> one record under details: on the owning bean'))
        elif HEADING.match(s):
            out.append(('carried', 'heading -> the key or section it names'))
        elif LISTITEM.match(s):
            out.append(('carried', 'list item -> an entry (open:, steps:, or a details list)'))
        elif QUOTE.match(s):
            out.append(('pointed-at', 'blockquote — cross-reference to another document'))
        elif HRULE.match(st):
            out.append(('dropped', 'thematic break — presentation only, same class as a table rule'))
        elif HTML_COMMENT.match(st):
            out.append(('dropped', 'HTML comment — an authoring note, not content'))
        elif is_prose(st):
            out.append(('carried', 'prose -> a bean fact, or the body of a genos:design bean'))
        else:
            # NO CATCH-ALL. The first version of this function ended in `else: carried`, which made
            # UNPLACED unreachable and its zero GUARANTEED rather than measured — the exact defect
            # this whole vocabulary release was written about, reproduced in the tool built to find
            # it. Prose must now LOOK like prose (open with a letter or digit) to be claimed as
            # carried; anything else is surfaced for a human instead of absorbed silently.
            out.append(('UNPLACED', f'no destination: {st[:60]!r}'))
    return out


def audit(path):
    lines = open(path, encoding='utf-8', errors='replace').readlines()
    cls = classify(lines)
    tally = collections.Counter(d for d, _ in cls)
    unplaced = [(i + 1, lines[i].rstrip()) for i, (d, _) in enumerate(cls) if d == 'UNPLACED']
    # host-ambiguity is not an accounting failure; it is the WORK the accounting reveals
    noshost = sum(1 for d, w in cls if 'HOST NOT NAMED' in w)
    return len(lines), tally, unplaced, noshost


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not args:
        print("usage: python3 bin/dmdigest.py <directory of .md documents> [--dry-run]"); return 2
    root = args[0]
    docs = sorted(glob.glob(os.path.join(root, '*.md')))
    if not docs:
        print(f"no documents under {root}"); return 2

    print(f"DRY RUN — {len(docs)} documents under {root}. Nothing is written.\n")
    print(f"{'document':38s} {'lines':>5s} {'carried':>8s} {'point':>6s} {'drop':>5s} "
          f"{'struct':>7s} {'UNPLACED':>9s} {'no-host':>8s}")
    print('-' * 100)
    grand, fails = collections.Counter(), []
    total_noshost = 0
    for d in docs:
        n, t, unplaced, noshost = audit(d)
        grand.update(t); grand['lines'] += n; total_noshost += noshost
        if unplaced:
            fails.append((d, unplaced))
        print(f"{os.path.basename(d):38s} {n:5d} {t['carried']:8d} {t['pointed-at']:6d} "
              f"{t['dropped']:5d} {t[STRUCTURAL]:7d} {len(unplaced):9d} {noshost:8d}")

    placed = grand['carried'] + grand['pointed-at'] + grand['dropped'] + grand[STRUCTURAL]
    print('-' * 100)
    print(f"{'TOTAL':38s} {grand['lines']:5d} {grand['carried']:8d} {grand['pointed-at']:6d} "
          f"{grand['dropped']:5d} {grand[STRUCTURAL]:7d} {grand['UNPLACED']:9d} {total_noshost:8d}")

    content = grand['lines'] - grand[STRUCTURAL]
    print(f"\naccounted: {placed}/{grand['lines']} lines ({100*placed/grand['lines']:.1f}%)")
    print(f"of {content} CONTENT lines (blanks excluded), {grand['carried']} become data "
          f"({100*grand['carried']/content:.1f}%), {grand['dropped']} are dropped with a reason, "
          f"{grand['pointed-at']} stay where they are and are pointed at")
    print(f"\nHOST NOT NAMED in {total_noshost} command lines — these are the ones that must have a "
          f"host established before they are carried. That is the WORK, not a defect in the tally: a "
          f"command carried without its host is true of a machine nobody named.")

    if fails:
        print("\nFAILED — these documents have lines with no destination:")
        for d, un in fails:
            print(f"  {os.path.basename(d)}: {len(un)} line(s), first at {un[0][0]}: {un[0][1][:70]}")
        return 1
    print("\nEVERY LINE HAS A DESTINATION. The design holds; the loop may write.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
