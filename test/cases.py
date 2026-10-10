#!/usr/bin/env python3
"""The four standing cases (core 2.0's acceptance): a routine consultation, an open-heart surgery, an Arduino blinker
and a production line with accounts — each a garden of its own grown from this tree, written in statements, saved
through its gate, and each refusing what it must.

  consultation  the patient's own garden: the doctor under an opaque id, the clinic by its ROR id; a lab result (LOINC)
                and a diagnosis (ICD-10), schemes held at their authority and checked by their form, special-category,
                so sealed before the save — and refused unsealed
  surgery       a coronary bypass as a course on a walk of its steps; its two grafts (ICD-10-PCS) and a clotting time
                (LOINC) sealed; the patient's Turkish identity number held, refused written; the surgeon's ORCID iD, the
                echo study's DICOM UID and the oxygenator's GTIN, each checked — and an altered copy refused
  blinker       a board that runs a sketch named by its SHA-256 and classed by its SPDX licence; its LED's rate a
                frequency in hertz; the resistor's 220 ohms kept whole in `details`, since the law has no electrical
                quantity yet
  line          a production line as a walk whose steps take and give the workshop's own parts, a batch as its course,
                and its money booked to accounts of the garden's own extract of the Turkish uniform chart — a move
                after the final step, and a booking to no account, refused

Run: python3 test/cases.py   (0 = green)
"""
import hashlib, os, re, shutil, socket, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS = []
HOST = socket.gethostname()


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-900:]))
    if not cond:
        FAILS.append(name)


def write(g, rel, text):
    p = os.path.join(g, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def text(g, rel):
    with open(os.path.join(g, rel), encoding='utf-8') as fh:
        return fh.read()


def gate(g):
    return grow.run(PY, 'bin/check.py', cwd=g)


def save(g, who, what, *body):
    return grow.run(PY, 'bin/save.py', who, what, '--body', *body, cwd=g)


def seal(g, bean, sid):
    return grow.run(PY, 'bin/held.py', 'put', bean, sid, cwd=g)


def bean(bid, kind, title, statements, body='', details=''):
    return (f'---\nbean: {bid}\nkind: {kind}\ntitle: "{title}"\nstatements:\n'
            + ''.join(f'  - {s}\n' for s in statements) + (f'details:\n{details}' if details else '') + f'---\n{body or title}\n')


def laptop(g, who):
    return bean('laptop', 'host', "laptop — the machine this garden is kept on",
                [f'read: {{ by: {who}, at: now }}', f'own:  {{ by: {who}, of: self }}',
                 f'name: {{ by: anchor-hostname, of: self, as: {HOST} }}'],
                details=f'  roots:\n    vault: {{ system: unix-filesystem, at: "{HOST}:{g}-vault", keeps: special-category, '
                        f'readable_from: this-host }}\n')


def at_authority(scheme, classifies, publisher, url, pattern, sensitive=True):
    return (f"  - {{ scheme: {scheme}, classifies: \"{classifies}\", holding: at-authority,"
            + (" sensitive: special-category," if sensitive else "")
            + f" publisher: \"{publisher}\", url: \"{url}\", levels: [ {{ level: code }} ], neighbours: none,"
              f" sources: \"{url}\", code_pattern: '{pattern}' }}\n")


HOSTNAME_NS = '  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name for itself" }\n'
LOINC = at_authority('loinc', 'laboratory and clinical observations (LOINC)', 'Regenstrief Institute', 'https://loinc.org',
                     '^[1-9][0-9]{0,6}-[0-9]$')
T = tempfile.mkdtemp(prefix='core-cases-')
try:
    REL = grow.release(os.path.join(T, 'release'))

    # ---- A ROUTINE CONSULTATION, in the patient's own garden
    A = os.path.join(T, 'clinic')
    r = grow.garden(REL, A, 'pat', '--gardener-name', 'Pat')
    os.makedirs(A + '-vault')
    write(A, 'VOCAB.md', '---\nprofiles: [knowledge]\nnamespaces:\n' + HOSTNAME_NS + 'schemes:\n'
          + at_authority('icd-10', "diagnoses, as the WHO's ICD-10 classes them", 'World Health Organization',
                         'https://icd.who.int/browse10/2019/en', r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$') + LOINC
          + "---\n# the patient's own rows\n")
    write(A, 'beans/laptop.md', laptop(A, 'pat'))
    write(A, 'beans/clinic.md', bean('clinic', 'org', "the clinic (its ROR id is the one ROR documents as its example)",
                                     ['say:  { by: pat, at: now }', 'name: { by: ror, of: self, as: "05dxps055" }']))
    write(A, 'beans/p-1a2b3c4d.md', bean('p-1a2b3c4d', 'person', 'p-1a2b3c4d',
                                         ['say: { by: pat, at: now }', 'own: { by: theone, of: self }',
                                          'represent: { by: self, of: clinic, as: "a doctor of the clinic" }']))
    write(A, 'beans/consultation.md', bean('consultation', 'event', "consultation — a sore throat, seen at the clinic", [
        'say:     { by: pat, at: now }', 'be:      { by: self, at: "2026-10-06 10:30+03:00" }',
        'own:     { by: theone, of: self }', 'answer:  { by: clinic, of: self, as: law }',
        'attend:  { by: pat, of: self }', 'attend:  { by: p-1a2b3c4d, of: self }',
        'measure: { id: strep, by: p-1a2b3c4d, of: pat, as: "loinc:78012-2", presence: present, at: "2026-10-06 10:40+03:00" }',
        'classify: { id: dx, by: p-1a2b3c4d, of: pat, as: "icd-10:J02.0" }']))
    g = gate(A)
    check("consultation: a garden grows, and its lab result and diagnosis, written unsealed, are refused as special-category",
          r.returncode == 0 and g.returncode != 0 and g.out.count('special-category, unsealed') == 2
          and 'cannot be read here' not in g.out, g.out[-900:])
    write(A, 'beans/consultation.md', text(A, 'beans/consultation.md').replace('icd-10:J02.0', 'icd-10:j02'))
    g = gate(A)
    check("...a code of a scheme held at its authority is checked by its form there: `j02` is no ICD-10 code",
          "'j02' is not in the form of a code of icd-10" in g.out, g.out[-700:])
    write(A, 'beans/consultation.md', text(A, 'beans/consultation.md').replace('icd-10:j02', 'icd-10:J02.0'))
    s1, s2 = seal(A, 'consultation', 'strep'), seal(A, 'consultation', 'dx')
    r = save(A, 'pat', 'RULE-CHANGE: a consultation, its health facts sealed',
             '- action: RULE-CHANGE — VOCAB.md takes the knowledge profile and two schemes held at their authority, '
             'special-category; wrote [[laptop]], [[clinic]], [[p-1a2b3c4d]] and [[consultation]]',
             '- ratified_by: pat', '- held: consultation strep added', '- held: consultation dx added')
    leaked = grow.run('git', 'grep', '-c', '-e', '78012-2', '-e', 'J02.0', 'HEAD', cwd=A).out.strip()
    check("...sealed, it is saved through the gate, and neither code is anywhere in git",
          s1.returncode == 0 and s2.returncode == 0 and r.returncode == 0 and not leaked, (r.out[-700:], leaked))

    # ---- AN OPEN-HEART SURGERY: a coronary bypass, in the patient's garden
    B = os.path.join(T, 'heart')
    r = grow.garden(REL, B, 'pat', '--gardener-name', 'Pat')
    os.makedirs(B + '-vault')
    write(B, 'VOCAB.md', '---\nprofiles: [knowledge]\nkinds:\n'
          '  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n'
          'namespaces:\n' + HOSTNAME_NS + 'schemes:\n'
          + at_authority('icd-10-pcs', 'procedures, as ICD-10-PCS codes them', 'Centers for Medicare & Medicaid Services',
                         'https://www.cms.gov/medicare/coding-billing/icd-10-codes', '^[0-9A-HJ-NP-Z]{7}$') + LOINC
          + "---\n# the patient's own rows\n")
    write(B, 'beans/laptop.md', laptop(B, 'pat'))
    write(B, 'beans/hospital.md', bean('hospital', 'org', 'the hospital where the surgery was done',
                                       ['say: { by: pat, at: now }']))
    write(B, 'beans/p-5e6f7a8b.md', bean('p-5e6f7a8b', 'person', 'p-5e6f7a8b', [
        'say: { by: pat, at: now }', 'own: { by: theone, of: self }',
        'name: { by: orcid, of: self, as: "0000-0002-1825-0097" }',
        'represent: { by: self, of: hospital, as: "the surgeon" }']))
    write(B, 'beans/oxygenator-model.md', bean('oxygenator-model', 'document',
                                               "the oxygenator's model (its GTIN is GS1's own documented example)",
                                               ['say: { by: pat, at: now }', 'name: { by: gs1, of: self, as: "(01)09520123456788" }']))
    write(B, 'beans/echo-study.md', bean('echo-study', 'document', 'echo-study — the echocardiogram before the surgery', [
        'say: { by: pat, at: now }', 'name: { by: dicom-uid, of: self, as: "2.25.147690544832915329147527678556278928838" }']))
    steps = [('admitted', 'the patient is admitted and prepared', 'patient', 'induction'),
             ('induction', 'anaesthesia is induced', 'anaesthetist', 'on-bypass'),
             ('on-bypass', 'the heart-lung machine takes over', 'perfusionist', 'grafts'),
             ('grafts', 'the grafts are sewn', 'surgeon', 'off-bypass'),
             ('off-bypass', 'the heart beats on its own again', 'perfusionist', 'recovery')]
    write(B, 'mappings/walk-cabg.md', bean('walk-cabg', 'procedure', 'walk-cabg — how a coronary bypass goes',
                                           ['say: { by: pat, at: now }']
                                           + [f'step: {{ id: {i}, as: "{a}", by: {b}, to: [{t}] }}' for i, a, b, t in steps]
                                           + ['step: { id: recovery, as: "intensive care, then the ward", by: patient, walk: { final: "true" } }',
                                              'step: { id: stopped, as: "the operation is stopped", walk: { exit: "true", reasons: [unstable] } }']))
    moves = [f'move: {{ by: p-5e6f7a8b, of: self, through: course, at: ["2026-10-07 {h}+03:00", "walk-cabg#{s}"] }}'
             for h, s in (('07:30', 'admitted'), ('08:10', 'induction'), ('09:00', 'on-bypass'), ('09:20', 'grafts'),
                          ('11:05', 'off-bypass'), ('12:30', 'recovery'))]
    SURGERY = bean('surgery', 'contract', "surgery — Pat's coronary bypass", [
        'say: { by: pat, at: now }', 'own: { by: theone, of: self }', 'answer: { by: pat, of: self, as: law }',
        'answer: { by: hospital, of: self, as: law }', 'agree: { by: pat, of: "the surgery", through: written, as: patient }',
        'agree: { by: p-5e6f7a8b, of: "the surgery", through: written, as: surgeon }',
        'be: { id: course, by: self, at: walk-cabg, as: order }'] + moves + [
        'use: { by: hospital, of: oxygenator-model }',
        'classify: { id: graft-lima, by: p-5e6f7a8b, of: self, as: "icd-10-pcs:02100Z9" }',
        'classify: { id: graft-svg, by: p-5e6f7a8b, of: self, as: "icd-10-pcs:021109W" }',
        'measure: { id: act, by: p-5e6f7a8b, of: pat, as: "loinc:3184-9", value: { count: "480", unit: s }, at: "2026-10-07 09:15+03:00" }'])
    write(B, 'beans/surgery.md', SURGERY)
    write(B, 'beans/pat.md', text(B, 'beans/pat.md').replace(
        '---\nPat', '  - name: { id: tckn, by: tr-tckn, of: self, as: "10000000146" }\n'
                    '  - say: { by: pat, of: [tckn], at: now }\n---\nPat', 1))
    g = gate(B)
    check("surgery: its two graft codes and its clotting time refused unsealed, and the identity number refused written",
          r.returncode == 0 and g.out.count('special-category, unsealed') == 3 and 'a government number' in g.out
          and g.out.count('error') and 'names' not in g.out.split('core check')[0], g.out[-900:])
    for bad, says in (('"0000-0002-1825-0098"', 'orcid-checksum'), ('"(01)09520123456787"', 'gs1-element'),
                      ('"2.25.340282366920938463463374607431768211456"', 'uuid-integer')):
        target = 'beans/p-5e6f7a8b.md' if 'orcid' in says else 'beans/oxygenator-model.md' if 'gs1' in says else 'beans/echo-study.md'
        good = text(B, target)
        write(B, target, re.sub(r'as: "[^"]+" \}', f'as: {bad} }}', good, count=1) if 'name:' in good else good)
        g = gate(B)
        check(f"...an altered name is refused by its check ({says})", says in g.out, g.out[-500:])
        write(B, target, good)
    seals = [seal(B, 'pat', 'tckn')] + [seal(B, 'surgery', i) for i in ('graft-lima', 'graft-svg', 'act')]
    r = save(B, 'pat', 'RULE-CHANGE: the coronary bypass, its codes sealed',
             '- action: RULE-CHANGE — VOCAB.md takes the knowledge profile, the kind procedure and two schemes held at '
             'their authority; wrote [[laptop]], [[hospital]], [[p-5e6f7a8b]], [[oxygenator-model]], [[echo-study]], '
             '[[walk-cabg]], [[surgery]] and [[pat]]', '- ratified_by: pat', '- held: pat tckn added',
             '- held: surgery graft-lima added', '- held: surgery graft-svg added', '- held: surgery act added')
    leaked = grow.run('git', 'grep', '-c', '-e', '10000000146', '-e', '02100Z9', '-e', '021109W', '-e', '3184-9', 'HEAD',
                      cwd=B).out.strip()
    course = grow.run(PY, 'bin/daftar.py', 'seq', 'course', 'surgery', cwd=B)
    check("...sealed and held, it is saved, nothing of them in git, and its course read: at recovery, a final step",
          all(s.returncode == 0 for s in seals) and r.returncode == 0 and not leaked
          and "at 'recovery'" in course.out and 'a final step' in course.out, (r.out[-600:], leaked, course.out[-300:]))
    write(B, 'beans/surgery.md', text(B, 'beans/surgery.md').replace(
        '  - use:', '  - move: { by: p-5e6f7a8b, of: self, through: course, at: ["2026-10-07 13:00+03:00", "walk-cabg#grafts"] }\n  - use:'))
    g = gate(B)
    check("...a move after the final step is refused (rule line)", g.returncode != 0 and 'line' in g.out, g.out[-500:])
    grow.run('git', 'checkout', '--', 'beans/surgery.md', cwd=B)

    # ---- AN ARDUINO BLINKER
    C = os.path.join(T, 'maker')
    r = grow.garden(REL, C, 'sam', '--gardener-name', 'Sam')
    sketch = ('void setup() { pinMode(LED_BUILTIN, OUTPUT); }\nvoid loop() { digitalWrite(LED_BUILTIN, HIGH); delay(1000); '
              'digitalWrite(LED_BUILTIN, LOW); delay(1000); }\n')
    write(C, 'VOCAB.md', '---\nprofiles: [knowledge]\nkinds:\n'
          '  - { kind: component, nature: body, level: device, meaning: "a part an electronic thing is built of" }\n'
          'schemes:\n' + at_authority('spdx', 'the licences a work is under, by their SPDX identifiers',
                                      'the SPDX project', 'https://spdx.org/licenses/', '^[A-Za-z0-9][A-Za-z0-9.+-]*$',
                                      sensitive=False) + "---\n# the maker's own rows\n")
    write(C, 'beans/uno.md', bean('uno', 'host', 'uno — the board the blinker runs on', [
        'read: { by: sam, at: now }', 'own: { by: sam, of: self }', 'run: { by: self, of: blink }']))
    write(C, 'beans/led.md', bean('led', 'component', 'led — the light-emitting diode that blinks', [
        'read: { by: sam, at: now }', 'part: { by: self, of: uno }',
        'measure: { id: blink-rate, by: sam, of: self, as: frequency, value: { count: "0.5", unit: Hz }, at: "2026-10-09 18:00+03:00" }']))
    write(C, 'beans/resistor.md', bean('resistor', 'component', "resistor — the LED's current-limiting resistor",
                                       ['read: { by: sam, at: now }', 'part: { by: self, of: uno }'],
                                       details='  resistance: "220 Ohm (UCUM `Ohm`), its bands red, red, brown — kept whole '
                                               'here: the law has no electrical quantity yet"\n'))
    write(C, 'beans/blink.md', bean('blink', 'program', 'blink — the sketch that blinks the LED', [
        'make: { by: sam, at: now }', f'name: {{ by: sha-256, of: self, as: "{hashlib.sha256(sketch.encode()).hexdigest()}" }}',
        'classify: { of: self, as: "spdx:CC0-1.0" }'], body='```c\n' + sketch + '```'))
    r2 = save(C, 'sam', 'RULE-CHANGE: the blinker', '- action: RULE-CHANGE — VOCAB.md takes the knowledge profile, the '
              'kind component and SPDX held at its authority; wrote [[uno]], [[led]], [[resistor]] and [[blink]]',
              '- ratified_by: sam')
    check("blinker: a board runs a sketch named by its content's SHA-256 and classed by its SPDX licence, its LED's rate "
          "in hertz — saved through the gate", r.returncode == 0 and r2.returncode == 0, r2.out[-800:])

    # ---- A PRODUCTION LINE WITH ACCOUNTS
    D = os.path.join(T, 'bracket-line')
    r = grow.garden(REL, D, 'sam', '--gardener-name', 'Sam')
    write(D, 'VOCAB.md', '---\nprofiles: [accounting]\nkinds:\n'
          '  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\nschemes:\n'
          '  - { scheme: tdhp, classifies: "where an amount belongs, by the Turkish uniform chart of accounts", '
          'holding: extract, publisher: "the Ministry of Finance (Resmi Gazete 21447)", url: "file:extracts/tdhp.tsv", '
          'levels: [ { level: group }, { level: class }, { level: account } ], neighbours: none, sources: extracts/tdhp.tsv }\n'
          '  - { scheme: parts, classifies: "what the line takes in and gives out", holding: extract, publisher: the '
          'workshop, url: "file:extracts/parts.tsv", levels: [ { level: part } ], neighbours: none, sources: extracts/parts.tsv }\n'
          'files:\n  - { registry: tdhp, file: extracts/tdhp.tsv, key: code }\n'
          '  - { registry: parts, file: extracts/parts.tsv, key: code }\n---\n# the workshop\'s own rows\n')
    write(D, 'extracts/tdhp.tsv', 'code\tlevel\tparent\tname\n1\tgroup\t\tcurrent assets\n15\tclass\t1\tinventories\n'
          '150\taccount\t15\traw materials\n6\tgroup\t\tthe income statement\n60\tclass\t6\tgross sales\n'
          '600\taccount\t60\tdomestic sales\n7\tgroup\t\tcost accounts\n72\tclass\t7\tdirect labour\n'
          '720\taccount\t72\tdirect labour costs\n')
    write(D, 'extracts/parts.tsv', 'code\tlevel\tparent\tname\nsteel-sheet\tpart\t\tsteel sheet, 2 mm\n'
          'powder-paint\tpart\t\tpowder paint\nbracket\tpart\t\ta painted steel bracket\n')
    write(D, 'mappings/walk-bracket-line.md', bean('walk-bracket-line', 'procedure', 'walk-bracket-line — a batch down the line', [
        'say: { by: sam, at: now }',
        'step: { id: cut, as: "the sheet is cut to blanks", by: operator, to: [bent], walk: { takes: [ { code: "parts:steel-sheet", amount: { count: "2.5", unit: kg } } ] } }',
        'step: { id: bent, as: "the blanks are bent", by: operator, to: [painted] }',
        'step: { id: painted, as: "the brackets are painted", by: painter, to: [packed], walk: { takes: [ { code: "parts:powder-paint", amount: { count: "0.2", unit: kg } } ] } }',
        'step: { id: packed, as: "the batch is packed", by: operator, walk: { final: "true", gives: [ { code: "parts:bracket", amount: { count: "100", unit: "{item}" } } ] } }',
        'step: { id: scrapped, as: "the batch is scrapped", walk: { exit: "true", reasons: [out-of-tolerance] } }']))
    for o, title in (('steelworks', 'steelworks — the supplier of the sheet'), ('builder', 'builder — the customer')):
        write(D, f'beans/{o}.md', bean(o, 'org', title, ['say: { by: sam, at: now }']))
    BATCH = bean('batch-41', 'contract', 'batch-41 — a hundred brackets for the builder', [
        'say: { by: sam, at: now }', 'own: { by: theone, of: self }', 'answer: { by: sam, of: self, as: law }',
        'answer: { by: builder, of: self, as: law }', 'agree: { by: sam, of: "a hundred brackets", through: written, as: operator }',
        'agree: { by: builder, of: "a hundred brackets", through: written, as: customer }',
        'be: { id: run, by: self, at: walk-bracket-line, as: order }'] + [
        f'move: {{ by: sam, of: self, through: run, at: ["2026-10-0{d} {h}+03:00", "walk-bracket-line#{s}"] }}'
        for d, h, s in (('8', '08:00', 'cut'), ('8', '10:00', 'bent'), ('8', '13:00', 'painted'), ('9', '11:00', 'packed'))] + [
        'pay: { id: sheet, by: sam, to: steelworks, of: { count: "1250.00", unit: TRY }, at: "2026-10-07" }',
        'book: { of: sheet, to: "tdhp:150", share: "1" }',
        'pay: { id: labour, by: sam, of: { count: "900.00", unit: TRY }, at: "2026-10-09" }',
        'book: { of: labour, to: "tdhp:720", share: "1" }',
        'pay: { id: sale, by: builder, to: sam, of: { count: "4000.00", unit: TRY }, at: "2026-10-09" }',
        'book: { of: sale, to: "tdhp:600", share: "1" }'])
    write(D, 'beans/batch-41.md', BATCH.replace('"tdhp:720"', '"tdhp:721"'))
    g = gate(D)
    check("line: a booking to an account the chart has not is refused", g.returncode != 0 and "'721' is not a code of tdhp" in g.out,
          g.out[-500:])
    write(D, 'beans/batch-41.md', BATCH)
    r2 = save(D, 'sam', 'RULE-CHANGE: the bracket line, and batch 41', '- action: RULE-CHANGE — VOCAB.md takes the '
              'accounting profile, the kind procedure and two schemes of the garden\'s own (tdhp, parts) in extracts/; '
              'wrote [[walk-bracket-line]], [[steelworks]], [[builder]] and [[batch-41]]', '- ratified_by: sam')
    course = grow.run(PY, 'bin/daftar.py', 'seq', 'course', 'batch-41', cwd=D)
    check("...the line's batch moves through cut, bent, painted and packed, its money booked to the chart's accounts — "
          "saved, its course read", r.returncode == 0 and r2.returncode == 0 and "at 'packed'" in course.out,
          (r2.out[-700:], course.out[-300:]))
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the cases ran to their end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)
    for v in ('clinic', 'heart'):
        shutil.rmtree(os.path.join(T, v) + '-vault', ignore_errors=True)

print(f"\ncases: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
