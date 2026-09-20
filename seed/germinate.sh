#!/bin/sh
# germinate — grow a new garden from this seed.
#
# What germinates is the LANGUAGE, never an estate: the Tier-0 vocabulary, the parser, the gate and the
# tools, plus four empty templates. Beans are NOT carried. They are re-observable facts about machines
# that still exist, and copying them into a new garden would import assertions nobody made there.
#
# The pins are INTERPOLATED from the vocabulary's own `version:` key. A version typed into a template is
# a second copy that can disagree with the first, and the gate now treats a disagreeing pin as an ERROR.
#
# Usage:  sh seed/germinate.sh <target-directory>
set -e

TARGET="$1"
[ -n "$TARGET" ] || { echo "usage: sh seed/germinate.sh <target-directory>" >&2; exit 2; }
[ -e "$TARGET" ] && { echo "germinate: $TARGET already exists — refusing to plant over it" >&2; exit 2; }
# ABSOLUTE BEFORE ANYTHING CHANGES DIRECTORY. The copy below runs from inside the release, so a relative
# target resolved THERE: `sh daftar/seed/germinate.sh garden` planted the language inside the clone and left
# an empty skeleton where the garden was asked for. v0.3.0 shipped that; found by the first end-to-end run.
PARENT=$(dirname -- "$TARGET")
[ -d "$PARENT" ] || { echo "germinate: $PARENT does not exist — create it first" >&2; exit 2; }
TARGET="$(CDPATH= cd -- "$PARENT" && pwd)/$(basename -- "$TARGET")"

SEED=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$SEED/.." && pwd)

command -v python3 >/dev/null || { echo "germinate: python3 is required" >&2; exit 2; }
python3 -c 'import yaml' 2>/dev/null || { echo "germinate: PyYAML is required (pip install PyYAML)" >&2; exit 2; }

VER=$(python3 - "$SEED/std-vocab.md" <<'PY'
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(sys.argv[1])), 'bin'))
import dmparse, yaml
print(str(yaml.safe_load(dmparse.read(sys.argv[1])[0])['version']))
PY
)
[ -n "$VER" ] || { echo "germinate: could not read the vocabulary version" >&2; exit 1; }
# WHICH RELEASE this garden grows from: the tag the release checkout sits on, else "untagged <commit>". Recorded in
# GARDEN.md so a garden can say what it runs, and bin/dmupgrade.py can refuse to go backwards.
RELEASE=$(git -C "$ROOT" describe --tags --exact-match 2>/dev/null || echo "untagged $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)")

mkdir -p "$TARGET/beans" "$TARGET/mappings" "$TARGET/log" "$TARGET/seed"
# WHAT TRAVELS IS DECLARED ONCE, in seed/LANGUAGE, and bin/dmupgrade.py reads the same file — so a new garden
# and an upgraded one cannot disagree about what the language is. The reasons for each entry live there.
( cd "$ROOT" && grep -v '^[[:space:]]*#' "$SEED/LANGUAGE" | grep -v '^[[:space:]]*$' | while read -r pat; do
    for f in $pat; do
        [ -d "$f" ] && continue      # `seed/*` also matches seed/knowledge/; its files have their own line
        [ -f "$f" ] || { echo "germinate: seed/LANGUAGE names '$pat', which matches no file" >&2; exit 1; }
        mkdir -p "$TARGET/$(dirname "$f")"
        cp -p "$f" "$TARGET/$f"
    done
  done ) || exit 1
find "$TARGET" -name __pycache__ -type d -prune -exec rm -rf {} +

GARDEN=$(basename "$TARGET")
for f in VOCAB GARDEN; do
    sed -e "s/@@VERSION@@/$VER/g" -e "s/@@GARDEN@@/$GARDEN/g" -e "s/@@RELEASE@@/$RELEASE/g" \
        "$SEED/$f.md.template" > "$TARGET/$f.md"
done
sed -e "s/@@GARDEN@@/$GARDEN/g" "$SEED/journal.md.template" > "$TARGET/log/journal.md"
sed -e "s/@@GARDEN@@/$GARDEN/g" "$SEED/pending.md.template" > "$TARGET/log/pending.md"

cd "$TARGET"
git init -q .
sh bin/install.sh >/dev/null 2>&1 || true       # hooks + merge driver; harmless if it cannot
git add -A
git -c user.name=germinate -c user.email=germinate@localhost \
    commit -q -m "germinate: $GARDEN — the language, at std-vocab@$VER. No beans."
python3 bin/dmcheck.py

cat <<EOF

germinated: $TARGET  (std-vocab@$VER, daftar $RELEASE)

The garden is empty and it passes its own gate. To plant the first bean:
  1. write $TARGET/beans/<id>.md   (bean: <id> must equal the filename)
  2. append an entry to $TARGET/log/journal.md  — the gate REFUSES a bean staged without one.
     Its heading is a POSITION IN TIME and the gate checks the form, so read it from the clock:
       printf '\n## %s · your-name · what you did\n- action: added [[<id>]].\n' "\$(date '+%Y-%m-%d %H:%M%:z')" >> $TARGET/log/journal.md
  3. git add -A && git commit

  python3 bin/dmrules.py   prints every rule in force, derived from the vocabulary.
  seed/README.md           a first person, a first host and a first journal entry, passing as written.
  seed/COOKBOOK.md         a domain, a service on a machine, a rented server, and adding a missing value.
  MODEL.md, CHECKLIST.md   what the rules mean, and how a write is made.

WORKING WITH A CODING AGENT? .claude/skills/daftar/ came with the garden. Open the garden in a tool
that reads it and the agent loads the law from THIS garden rather than guessing — which is the point
of the whole thing: one language, both parties writing in it, neither able to corrupt it quietly.
EOF

# AN UNTAGGED CLONE MAKES AN UNPINNABLE GARDEN, and this is said LAST, where it is still on the screen.
# The README tells a reader to pin a release and upgrade deliberately; cloning the default branch and
# running this script is the one path that quietly does the opposite, and it is the path everybody takes
# first. Said before the gate runs, it scrolls away behind forty lines of PASS and is never read — which
# is how this script already learned to print the git-identity warning at the end rather than the start.
case "$RELEASE" in
untagged*)
    cat <<EOF

NOTE: this clone is not on a release tag, so the garden records
  daftar_release: "$RELEASE"
which names no release anybody else can fetch. Fine for a look around. To pin one:
  git -C $ROOT tag -l                    # the releases this clone knows
  git -C $ROOT checkout <tag>            # the newest, usually
and grow again — or, in this garden as it stands, adopt one deliberately with
  cd $TARGET && python3 bin/dmupgrade.py <tag>
EOF
    ;;
esac
# WHO COMMITS. germinate commits as "germinate"; every later commit is yours, and git refuses one with no identity.
# A cold-start drill's first bean failed there, on a fresh machine, with nothing in the docs to say why.
if [ -z "$(git -C "$TARGET" config user.email)" ] || [ -z "$(git -C "$TARGET" config user.name)" ]; then
    cat <<EOF

BEFORE YOUR FIRST COMMIT: git has no identity here, and will refuse it. Set one for this garden:
  git -C $TARGET config user.name  "Your Name"
  git -C $TARGET config user.email "you@example.org"
An agent working in the garden should commit under its own name (e.g. "agent (model, session)"), so the journal's
"who" and git's author agree.
EOF
fi
