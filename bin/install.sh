#!/bin/sh
# Install this garden's git hooks and semantic merge driver into this clone.
#
# Hooks and merge-driver config live in .git/, which is NOT cloned, so every fresh clone runs this once.
# There is exactly ONE installer. There used to be two — this one wrote a hook running only the gate,
# while bin/hooks/install.sh installed the versioned hook running the gate AND the fast suite. Neither
# was a superset, so following the README after the CHECKLIST silently removed the fast suite from the
# gate. The versioned hooks in bin/hooks/ are the source of truth and this script only copies them.
set -e
REPO="$(git rev-parse --show-toplevel)"

# 1) the versioned hooks — copied, never generated, so what runs is what is reviewed
for h in "$REPO"/bin/hooks/*; do
  name=$(basename "$h")
  case "$name" in *.sh) continue ;; esac
  cp "$h" "$REPO/.git/hooks/$name"
  chmod +x "$REPO/.git/hooks/$name"
  echo "installed .git/hooks/$name"
done

# 2) semantic merge driver, referenced by .gitattributes (merge=daftar). Git does NOT warn when
#    an attribute names a driver that is not configured — it silently text-merges instead. The
#    attribute and this config must therefore always change together.
git config merge.daftar.name "daftar semantic merge (dmmerge)"
git config merge.daftar.driver "python3 $REPO/bin/dmmerge.py --file %O %A %B"
echo "configured merge driver 'daftar' -> bin/dmmerge.py"

# NO GLOBAL SKILL SYMLINK. This script used to offer one, into $HOME/.claude/skills/. It is not offered
# any more: the symlink outlives the clone it points at, its `[ ! -e ]` guard meant re-running this could
# never repair a stale one, and on this machine it resolved to a different clone pinned two vocabulary
# majors behind. The skill is PROJECT-SCOPED at .claude/skills/ and loads whenever you work in this repo.

echo "installed: pre-commit gate + semantic merge driver in $REPO/.git"
