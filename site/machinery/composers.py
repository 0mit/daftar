"""daftar's own mechanisms, drawn: the garden module for the machinery page of daftar's site.

Five composers — the gate, the journal, the merge, the mycelium and the ledger — each drawing one mechanism of daftar
as it is recorded in a demo garden (`site/machinery/record.yaml`). They draw only with the pattern kit, so every
element is recorded: its pattern, its id (the slug of its label), its box, and the bean it depicts. The kit is imported
when the drawings are made, from the copy vendored into the demo garden; nothing else is imported but the kit's model.

site/machinery/build.py copies this file into the demo garden as `bin/mechanisms.py` and names it there. Each composer
returns (title, svg, caption, claim). A figure is 960 wide and 280 to 340 tall, draws at most 18 elements, carries
exactly one accent (the point the mechanism turns on) and shows no address.

Node classes carry the natures the site uses: `svc` a person (empsychon), `nas` a record or a program (lekton),
`ext` what is outside this garden's hands.
"""
from fxdraw import node, store, gate, flow, elbow, tag, boundary, ribbon, figure, esc
import fxmodel


def mech_gate():
    b = [boundary(226, 12, 720, 296, "this clone of the garden"),
         node(16, 64, 180, 52, "A writer", "a person or an agent", cls="svc", bean="sam"),
         store(256, 58, 200, 66, "Staged files", "what git add put in the index"),
         gate(630, 91, "breaks a rule, or unjournalled?", 236, 66),
         store(286, 200, 200, 66, "The law", "std-vocab.md + VOCAB.md", bean="daftar"),
         node(774, 20, 168, 52, "Refused", "what is wrong, and where", cls="nas"),
         node(774, 210, 168, 52, "Committed", "history, with its entry", cls="nas"),
         flow(196, 90, 256, 90, "git add", ly=82),
         flow(456, 91, 512, 91, "git commit", lx=482, ly=78),
         elbow([(630, 58), (630, 46), (774, 46)], "refused", "accent", 702, 38),
         elbow([(630, 124), (630, 236), (774, 236)], "passes", "", 702, 228),
         elbow([(486, 233), (566, 233), (566, 109)], "reads", "sig", 590, 180),
         tag(256, 140, "the entry must name every bean it changes", "tag-warn"),
         tag(630, 280, "--no-verify: an emergency, said in the journal")]
    cap = ("The <b>gate</b> reads what is staged, not the working tree, against the law. It refuses a change that breaks "
           "a rule, or that the journal entry does not name. What passes is what the commit records.")
    return ("The gate", figure(960, 320, "".join(b), "the gate: the staged files are read against the law; refused, or committed"),
            cap, "A commit is recorded only if the gate passes it.")


def mech_journal():
    b = [node(16, 34, 172, 52, "A writer", "sam, or an agent", cls="svc", bean="sam"),
         node(276, 34, 244, 52, "bin/dmjournal.py", "reads the clock, writes the heading", cls="nas", bean="daftar"),
         node(276, 150, 244, 52, "The clock", "the machine's time, with its offset", cls="ext"),
         store(590, 20, 180, 64, "log/journal.md", "one entry per change"),
         store(590, 112, 180, 64, "journal-stamps", "this clone's register"),
         gate(680, 250, "stamped here?", 160, 56),
         node(306, 224, 180, 52, "Refused", "a typed heading", cls="nas"),
         flow(188, 60, 276, 60, "who, what, body", ly=52),
         flow(398, 150, 398, 86, "now", "sig", lx=420, ly=122),
         flow(520, 50, 590, 50, "appends", ly=42),
         flow(520, 74, 590, 140, "registers", lx=555, ly=110),
         flow(680, 176, 680, 222, "reads", "sig", lx=704, ly=203),
         elbow([(770, 52), (806, 52), (806, 250), (760, 250)], "reads", "sig", 806, 150),
         flow(600, 250, 486, 250, "not stamped", "accent", ly=242),
         tag(560, 290, "entries already written are never checked or rewritten")]
    cap = ("A heading is a position in time. <b>bin/dmjournal.py</b> reads the clock, writes the heading and registers "
           "it in this clone. The <b>gate</b> refuses a heading a commit adds that this clone's tool did not write, and "
           "a bean change the entry does not name.")
    return ("The journal", figure(960, 316, "".join(b), "the journal: a heading read from the clock, registered, and checked by the gate"),
            cap, "Every change carries who, when and why, and no hand types the when.")


def mech_merge():
    b = [store(16, 24, 170, 62, "Record A", "a clone's branch"),
         store(16, 124, 170, 62, "Record B", "another session's branch"),
         node(236, 64, 204, 52, "git merge", "never merges a bean's lines", cls="ext"),
         node(520, 64, 206, 52, "bin/dmmerge.py", "the daftar merge driver", cls="nas", bean="daftar"),
         gate(623, 190, "same establishing anchor?", 214, 58),
         node(776, 164, 170, 52, "One canonical bean", "each fact joined", cls="nas"),
         node(776, 276, 170, 52, "A disagreement, kept", "both values: merge_open", cls="nas"),
         node(520, 276, 150, 52, "sam settles", "the gardener decides", cls="svc", bean="sam"),
         flow(186, 55, 236, 82),
         flow(186, 155, 236, 100),
         flow(440, 90, 520, 90, "merge=daftar", ly=82),
         flow(623, 116, 623, 161, "resolve", lx=650, ly=142),
         flow(730, 190, 776, 190, "yes: join", lx=752, ly=182),
         flow(623, 219, 623, 276, "equal bare names: to a person", ly=250),
         flow(861, 216, 861, 276, "values differ, nothing orders them", "accent", ly=250),
         flow(670, 302, 776, 302, "picks one", "sig", ly=294),
         tag(16, 232, "an inferred value never overrides an asserted one")]
    cap = ("Git never merges a bean's lines: <code>.gitattributes</code> hands every bean to <b>bin/dmmerge.py</b>. Two "
           "beans are one object when an establishing <b>anchor</b> says so. Where one value subsumes another it is "
           "kept, and the other is recorded; where nothing orders them, both are kept for a person to settle.")
    return ("The merge", figure(960, 340, "".join(b), "the merge: two records, one canonical bean, a disagreement kept for a person"),
            cap, "Two records of one thing become one, and nothing either said is lost.")


def _shared_name():
    """The name shared-camera carries across gardens: its establishing anchor as this garden records it."""
    for a in ((fxmodel.fm("shared-camera").get("identity") or {}).get("anchors") or []):
        if isinstance(a, dict) and a.get("establishing"):
            return str(a.get("value"))
    return "contract:shared-camera"


def mech_mycelium():
    b = [boundary(16, 16, 300, 270, "garden-sam — kept by sam"),
         boundary(566, 16, 378, 270, "garden-ali — kept by ali"),
         store(36, 55, 260, 70, "shared-camera", "the agreement both are parties to", bean="shared-camera"),
         node(36, 200, 150, 52, "sam", "the gardener", cls="svc", bean="sam"),
         store(340, 55, 200, 70, "A proposal", "one file, beside both gardens"),
         gate(640, 90, "clean?", 100, 48),
         node(720, 64, 210, 52, "ali's working tree", "taken: written, not committed", cls="nas"),
         node(780, 200, 150, 52, "ali's commit", "the ratification", cls="accent"),
         node(590, 200, 140, 52, "ali", "the gardener", cls="svc", bean="ali"),
         flow(111, 200, 111, 125, "a party", "sig", lx=142, ly=166),
         flow(296, 90, 340, 90, "make", ly=82),
         flow(540, 90, 590, 90, "read", ly=82),
         flow(690, 90, 720, 90, "take", lx=705, ly=82),
         flow(855, 116, 855, 200, "git commit", ly=162),
         flow(730, 226, 780, 226, "decides", "sig", lx=755, ly=218),
         tag(590, 138, "taking is not accepting", "tag-warn"),
         ribbon(16, 300, 928, esc(_shared_name() + " — named once, by the garden that recorded it first"))]
    cap = ("Gardens meet only by <b>proposal</b>. <b>garden-sam</b> writes one file beside both gardens, under an "
           "agreement both gardeners are parties to. <b>garden-ali</b> reads it, which writes nothing, then takes it "
           "into the working tree, which commits nothing. Ali's commit is the ratification, and taking an agreement is "
           "not accepting it.")
    return ("The mycelium", figure(960, 340, "".join(b), "the mycelium: a proposal between two gardens, taken in by the other gardener's commit"),
            cap, "What passes between gardens is only ever a proposal, and only its gardener lets it in.")


def mech_ledger():
    b = [store(16, 24, 200, 66, "shared-camera", "what moved: paid and borne", bean="shared-camera"),
         store(16, 150, 200, 66, "washer-loan", "lent, and repaid monthly", bean="washer-loan"),
         node(350, 94, 190, 52, "bin/dmledger.py", "reads, in fractions", cls="nas", bean="daftar"),
         gate(655, 120, "comes out even?", 150, 54),
         node(770, 94, 176, 52, "What is owed", "read, never stored", cls="accent"),
         node(770, 232, 176, 52, "Between two", "netted across agreements", cls="nas"),
         flow(216, 57, 350, 108, "transactions", lx=283, ly=72),
         flow(216, 183, 350, 132, "transactions, clauses", lx=283, ly=184),
         flow(540, 120, 580, 120),
         flow(730, 120, 770, 120, "yes", ly=112),
         elbow([(655, 147), (655, 170), (800, 170), (800, 146)], "no", "", 690, 162),
         flow(900, 146, 900, 232, "nets", lx=922, ly=192),
         tag(560, 182, "not even: shown as the fraction it is", "tag-warn"),
         tag(350, 160, "no balance is stored")]
    cap = ("An agreement records only what <b>moved</b>. <b>bin/dmledger.py</b> reads what each party owes from that, "
           "exactly, in fractions, and nets it between two parties. A share that does not come out even is shown as the "
           "fraction it is. Nothing stores a balance.")
    return ("The ledger", figure(960, 300, "".join(b), "the ledger: what moved, read into what is owed"),
            cap, "What one person owes another is read from what moved, never written.")


COMPOSERS = {"gate": mech_gate, "journal": mech_journal, "merge": mech_merge,
             "mycelium": mech_mycelium, "ledger": mech_ledger}
