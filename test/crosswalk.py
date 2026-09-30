#!/usr/bin/env python3
"""Crosswalks (std-vocab 24.0, step 11): FHIR R5 Observations and Darwin Core occurrences carried into beans and back
by the law's tables alone (bin/dmcrosswalk.py). The beans pass the gate; the round trip gives back every field it did
not list, equal field for field; what a table cannot carry is listed, never dropped.

Every fixture is INVENTED: a household's own readings, kept by its gardener, in a code list an invented clinic keeps;
two rowans seen on an invented island.
Run: python3 test/crosswalk.py   (0 = green)
"""
import csv, io, json, os, re, subprocess, sys, tempfile
from decimal import Decimal
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-3000:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                          env=dict(os.environ, PYTHONIOENCODING="utf-8"))


T = tempfile.mkdtemp(prefix="dmcross-")
G = os.path.join(T, "g")
r = run(PY, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates, kept by keeper", r.returncode == 0, r.stdout + r.stderr)
run("git", "config", "user.name", "keeper (test)", cwd=G)
run("git", "config", "user.email", "keeper@example.org", cwd=G)


def write(rel, text):
    p = os.path.join(G, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(rel):
    return open(os.path.join(G, *rel.split("/")), encoding="utf-8").read()


def gate():
    r = run(PY, "bin/dmcheck.py", "--all", cwd=G)
    return r.stdout + r.stderr


def ok(out):
    return re.search(r" 0 error\(s\)", out) is not None


def tool(*a):
    r = run(PY, "bin/dmcrosswalk.py", *a, cwd=G)
    return r.returncode, r.stdout, r.stderr


def listed(err):
    return sorted(l[len("not carried: "):] for l in err.splitlines() if l.startswith("not carried: "))


def flat(node, path=""):
    out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            out.update(flat(v, f"{path}.{k}" if path else k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.update(flat(v, f"{path}[{i}]"))
    else:
        out[path] = node
    return out


VOCAB_EXTRA = """local_gene:
  - { genos: organism, of_nature: soma, level: organism, establishing_anchor_family: [logical], meaning: "a living thing, invented" }
registry_additions:
  knowledge_schemes:
    - scheme: vital-codes
      classifies: what an invented clinic reads of a body, where on it, and how
      holding: at-authority
      code_pattern: '^[A-Z][0-9]{2}$'
      licence: LicenseRef-invented
      publisher: an invented clinic
      url: "https://example.org/vital-codes"
      levels: [ { level: code } ]
      neighbours: none
      sources: "https://example.org/vital-codes"
"""
_v = read("VOCAB.md")
for _k in ("local_gene", "registry_additions"):
    _v = re.sub(rf"(?m)^{_k}: (\[\]|\{{\}}).*\n", "", _v)
_h, _sep, _rest = _v.partition("\n---\n")
write("VOCAB.md", _h + "\n" + VOCAB_EXTRA + _sep + _rest)

# ---------------------------------------------------------------- FHIR R5 Observation
FHIR = """[
 {"resourceType": "Observation", "id": "bp-systolic-0314", "status": "final",
  "code": {"coding": [{"system": "https://example.org/vital-codes", "code": "V01", "display": "systolic pressure"}]},
  "subject": {"reference": "Patient/keeper"},
  "effectiveDateTime": "2026-03-14T08:30:00+03:00",
  "bodySite": {"coding": [{"system": "https://example.org/vital-codes", "code": "B12"}]},
  "method": {"coding": [{"system": "https://example.org/vital-codes", "code": "M03"}]},
  "valueQuantity": {"value": 118.0, "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"},
  "performer": [{"reference": "Practitioner/keeper"}],
  "note": [{"text": "seated, after five minutes"}]},
 {"resourceType": "Observation", "id": "posture-0314", "status": "final",
  "code": {"coding": [{"system": "https://example.org/vital-codes", "code": "V07"}]},
  "subject": {"reference": "Patient/keeper"},
  "effectiveDateTime": "2026-03-14",
  "valueCodeableConcept": {"coding": [{"system": "https://example.org/vital-codes", "code": "P02"}]},
  "performer": [{"reference": "Device/cuff-1"}],
  "interpretation": [{"text": "normal"}]},
 {"resourceType": "Observation", "id": "weight-0314", "status": "preliminary",
  "code": {"coding": [{"system": "https://example.org/vital-codes", "code": "V11"}]},
  "subject": {"reference": "Patient/keeper"},
  "effectiveDateTime": "2026-03-14T08:40:00+03:00",
  "valueQuantity": {"value": 71.25, "system": "http://unitsofmeasure.org", "code": "[lb_av]"}}
]
"""
write("in/obs.json", FHIR)
rc, out, err = tool("to", "fhir", "in/obs.json")
check("D-1 FHIR -> beans: the tool runs", rc == 0, out + err)
got = listed(err)
check("D-1 what the table cannot carry is LISTED, each field by its path: a display, a unit's words, an "
      "interpretation, a performer that is no Practitioner, a status that is no reading made, and a quantity whose unit has no row, whole",
      got == sorted(["record 1: code.coding[0].display", "record 1: valueQuantity.unit",
                     "record 2: interpretation[0].text", "record 2: performer[0].reference",
                     "record 3: status", "record 3: valueQuantity.code", "record 3: valueQuantity.system",
                     "record 3: valueQuantity.value"]), got)
m = re.search(r"# beans/keeper\.md\n(.*)", out, re.S)
check("...and the readings land on the bean they are of", m is not None, out)
obs = m.group(1) if m else ""
k = read("beans/keeper.md")
head, sep, body = k[4:].partition("\n---\n")
write("beans/keeper.md", "---\n" + head + "\n" + obs.rstrip() + "\n---\n" + body)
out = gate()
check("D-1 the carried readings pass the gate: codes of a scheme held at its authority, a moment as FHIR writes it, "
      "a unit of the law", ok(out), out[-2500:])

rc, back, err = tool("back", "fhir", "keeper")
check("D-1 beans -> FHIR: the tool runs", rc == 0, back + err)
orig = json.loads(FHIR, parse_float=Decimal, parse_int=Decimal)
again = json.loads(back, parse_float=Decimal, parse_int=Decimal)
drop = {1: {"code.coding[0].display", "valueQuantity.unit"}, 2: {"interpretation[0].text", "performer[0].reference"},
        3: {"status", "valueQuantity.code", "valueQuantity.system", "valueQuantity.value"}}
kept = [{p: v for p, v in flat(o).items() if p not in drop[i + 1]} for i, o in enumerate(orig)]
# record 3 came in with a status it could not carry: back, it is a reading made, and says so
kept[2]["status"] = "final"
bk = [flat(a) for a in again]
check("D-1 the round trip: every field not listed comes back equal, field for field, decimals as written",
      bk == kept, json.dumps([{k: str(v) for k, v in d.items()} for d in bk], indent=1)[:3000])
check("...and back lists nothing it could not carry", listed(err) == [], err)

# a garden's own attribute the table has no row for is listed on the way back, never dropped
write("beans/keeper.md", read("beans/keeper.md").replace("    note: seated, after five minutes\n",
                                                         "    note: seated, after five minutes\n    presence: present\n"))
rc, back, err = tool("back", "fhir", "keeper", "bp-systolic-0314")
check("D-1 back: an attribute no row carries is listed by its path", listed(err) ==
      ["keeper:observations.bp-systolic-0314: presence"], err)
run("git", "checkout", "-q", "--", "beans/keeper.md", cwd=G)

# ---------------------------------------------------------------- Darwin Core occurrences
DWC = ("occurrenceID,eventDate,decimalLatitude,decimalLongitude,geodeticDatum,coordinateUncertaintyInMeters,locality,"
       "scientificName,recordedBy\n"
       "rowan-north,2026-05-02,57.1203,-6.1044,EPSG:4326,30,above the north landing,Sorbus aucuparia,keeper\n"
       "rowan-glen,2026-05-03,57.0981,-6.0877,EPSG:4326,,the glen by the old mill,Sorbus aucuparia,keeper\n")
write("in/occ.csv", DWC)
rc, out, err = tool("to", "dwc", "in/occ.csv")
check("D-1 Darwin Core -> beans: the tool runs", rc == 0, out + err)
check("D-1 a taxon and a recorder, which `located_at` has no place for, are LISTED",
      listed(err) == sorted(["record 1: recordedBy", "record 1: scientificName", "record 2: recordedBy",
                             "record 2: scientificName"]), listed(err))
check("...a coordinate is never bare: the datum, then latitude and longitude, in the system's one form",
      'EPSG:4326;57.1203,-6.1044' in out, out)
check("...and Darwin Core's uncertainty is an accuracy of kind bound, in metres; with none stated, none is given",
      re.search(r"accuracy: \{count: '30', unit: metre, kind: bound\}", out) and out.count("accuracy") == 1, out)
OWN = "owned_by: { legal: { owner: { bean: keeper } } }\nresponsibility: { legal: { holder: { bean: keeper } } }\n"
for bid, text in re.findall(r"# beans/([a-z-]+)\.md\n(.*?)(?=\n# beans/|\Z)", out, re.S):
    write(f"beans/{bid}.md", f"---\nbean: {bid}\ngenos: organism\ntitle: \"{bid}\"\nstatus: active\n"
          f"summary: \"a rowan on an invented island\"\nnature: soma\n{OWN}"
          f"identity: {{ status: provisional, anchors: [ {{ key: serial, value: \"{bid.upper()}-1\", class: hardware, "
          f"establishing: true }} ] }}\nprovenance: {{ src: observed, by: keeper, as_of: now }}\n{text.rstrip()}\n"
          f"---\n{bid}, invented.\n")
out = gate()
check("D-1 the carried positions pass the gate (and the gate loaded both tables as registries of the law)", ok(out), out[-2500:])
rc, back, err = tool("back", "dwc", "rowan-north", "rowan-glen")
rows = [{k: v for k, v in r.items() if v != ""} for r in csv.DictReader(io.StringIO(back))]
want = [{k: v for k, v in r.items() if v != "" and k not in ("scientificName", "recordedBy")}
        for r in csv.DictReader(io.StringIO(DWC))]
check("D-1 the round trip: every column not listed comes back equal", rows == want, back)
check("...and back lists nothing", listed(err) == [], err)

print(f"\ncrosswalk: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
