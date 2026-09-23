# daftar: WHICH PYTHON runs the tools in this clone. Sourced, never run: by the hooks, from beside them in the
# hooks directory (bin/install.py copies it there with them), and by bin/install.sh. bin/install.py makes the
# same choice in Python and records it.
#
# The first candidate that RUNS and IMPORTS yaml, tried in this order: `git config daftar.python` (the choice
# recorded last time), python3, python, `py -3` (the Windows launcher). A name that is found but runs no Python
# is skipped: on Windows `python3` and `python` may be the Microsoft Store's App execution aliases, which
# `command -v` finds and which only offer to install Python — the 20.0 hook took the first name it found and
# stopped there. A Python without PyYAML is skipped too, because nothing here runs without it. The one that works
# is recorded per clone as `git config daftar.python`, so the next run tries it first; when none works, the
# refusal names each candidate and why, because "python3 is required" on a machine that shows a python3 is a
# message nobody can act on.
#
# After `daftar_choose_python` succeeds, `daftar_py <args>` runs the chosen interpreter. `daftar_choose_python
# --no-record` chooses the same way and records nothing: seed/germinate.sh runs before there is a garden to record
# in, and the clone it runs from is not its to configure.

# UTF-8 WHATEVER THE MACHINE'S CODE PAGE. Every bean is UTF-8 and every tool opens files as UTF-8, but a Python on
# Windows writes to a pipe in the old code page, and a Persian title in a message would stop the gate mid-sentence
# (UnicodeEncodeError). Python's UTF-8 mode makes what the tools print UTF-8 too; elsewhere it changes nothing.
PYTHONUTF8=1
export PYTHONUTF8

daftar_py() {
  case "$DAFTAR_PY" in
    "py -"*) py ${DAFTAR_PY#py } "$@" ;;       # the launcher and its version switch, split on purpose
    *) "$DAFTAR_PY" "$@" ;;                    # a name or a path, which may hold a space
  esac
}

daftar_choose_python() {
  _dp_record=yes
  [ "$1" = "--no-record" ] && _dp_record=
  _dp_cfg=$(git config --get daftar.python 2>/dev/null)
  _dp_why=
  _dp_tried=
  for _dp_c in "$_dp_cfg" python3 python "py -3"; do
    [ -n "$_dp_c" ] || continue
    case "|$_dp_tried|" in *"|$_dp_c|"*) continue ;; esac
    _dp_tried="$_dp_tried|$_dp_c"
    DAFTAR_PY=$_dp_c
    # the interpreter's own path, in forward slashes (a path Git's sh and Windows both read), and with no line end:
    # a Windows Python ends a printed line with CR LF, and $(...) strips only the LF
    _dp_exe=$(daftar_py -c 'import sys, yaml; sys.stdout.write(sys.executable.replace(chr(92), "/"))' 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$_dp_exe" ]; then
      if [ -n "$_dp_record" ]; then
        [ -n "$_dp_cfg" ] && [ "$_dp_c" = "$_dp_cfg" ] || git config daftar.python "$_dp_exe" 2>/dev/null
      fi
      DAFTAR_PY=$_dp_exe
      return 0
    fi
    case "$_dp_c" in "py -"*) _dp_bin=py ;; *) _dp_bin=$_dp_c ;; esac
    _dp_at=$(command -v "$_dp_bin" 2>/dev/null)
    _dp_q=$_dp_c
    case "$_dp_c" in *" "*) case "$_dp_c" in "py -"*) ;; *) _dp_q="\"$_dp_c\"" ;; esac ;; esac
    if [ -z "$_dp_at" ]; then
      _dp_r="not found"
    elif daftar_py -c 'import sys' >/dev/null 2>&1; then
      _dp_r="runs, but PyYAML is missing: $_dp_q -m pip install PyYAML"
    else
      case "$_dp_at" in
        *WindowsApps*) _dp_r="is the Microsoft Store alias (App execution aliases), which runs no Python — install Python from python.org, or turn the alias off in Settings > Apps > Advanced app settings > App execution aliases" ;;
        *) _dp_r="is at $_dp_at but does not run" ;;
      esac
    fi
    [ "$_dp_c" = "$_dp_cfg" ] && _dp_q="git config daftar.python ($_dp_c)"
    _dp_why="$_dp_why
  $_dp_q: $_dp_r"
  done
  DAFTAR_PY=
  echo "daftar: no Python here runs the tools. Each candidate, and why:$_dp_why
Install Python 3 with PyYAML (pip install PyYAML), or name one that works:
  git config daftar.python <path-to-python>" >&2
  return 1
}
