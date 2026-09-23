#!/usr/bin/env python3
"""Vérification LIVE des hooks dans de vraies sessions Claude Code (`claude -p`) — manuelle.

Pourquoi : les suites mécaniques appellent les hooks avec des payloads synthétiques ; le bug du
filet mémoire (v1.4.1 — fausse alerte « session fermée sans /handoff » à CHAQUE démarrage) venait
de l'ORDRE réel des événements, invisible hors d'une vraie session. Ce script rejoue ce cycle avec
le vrai binaire, sur un projet jetable généré depuis l'arbre de travail :

  1. session qui modifie le code ET réécrit HANDOFF.md (/handoff)  → aucun filet écrit ;
     le gotcha ciblant le fichier édité arrive dans le contexte (transcript)
  2. nouvelle session                                              → AUCUNE injection « Filet mémoire »
  3. session qui modifie le code SANS /handoff                     → filet écrit
  4. nouvelle session                                              → filet injecté (message humain de
                                                                     la session 3 dedans), puis consommé

Coût : 4 appels courts (modèle haiku par défaut). Isolé des réglages utilisateur
(--setting-sources project,local), sans MCP (--strict-mcp-config). Les transcripts créés sous
~/.claude/projects/ pour ce projet jetable sont supprimés à la fin.
PAS en CI (auth + tokens) — à rejouer à chaque version majeure et à chaque montée de Claude Code.

Usage : python3 test/live-hooks-check.py [--model haiku] [--ref vX.Y.Z] [--keep]
        (--ref v1.4.1 montre le bug d'origine — mesuré 2026-09-23, claude 2.1.280 : v1.4.1 6/10 · v1.5.0 10/10)
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_TOP = {"EXAMPLES", "test", ".github", ".git", "plugins", ".claude-plugin"}
GIT = ["git", "-c", "user.email=live@test", "-c", "user.name=live"]
PASS = FAIL = 0


def ok(label, cond):
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if cond else (PASS, FAIL + 1)
    print(f"  {'✅' if cond else '❌'} {label}")


def make_project(tmp: Path, ref: str) -> Path:
    dest = tmp / "proj"
    dest.mkdir()
    if ref == "WORKTREE":
        for child in ROOT.iterdir():
            if child.name in EXCLUDE_TOP:
                continue
            if child.is_dir():
                shutil.copytree(child, dest / child.name, ignore=shutil.ignore_patterns("__pycache__", ".cache"))
            else:
                shutil.copy2(child, dest / child.name)
    else:  # version taguée (comparaison avant/après un correctif)
        tar = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", ref], capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", str(dest)], input=tar.stdout, check=True)
        for d in EXCLUDE_TOP:
            shutil.rmtree(dest / d, ignore_errors=True)
    subprocess.run(["git", "init", "-q"], cwd=dest, check=True)
    subprocess.run(GIT + ["add", "-A"], cwd=dest, check=True)
    subprocess.run(GIT + ["commit", "-qm", "pre-init"], cwd=dest, check=True)
    vars_ = tmp / "vars.json"
    vars_.write_text(json.dumps({"PROJECT_NAME": "Caisse Live", "CLIENT_NAME": "Boulangerie", "PROJECT_FOLDER": "caisse-live",
                                 "NOM_DECIDEUR": "S M", "EMAIL_DECIDEUR": "s@example.org", "TON_NOM": "J L",
                                 "TON_EMAIL": "j@example.org", "COMMANDE_INSTALL": "pip install -e .",
                                 "COMMANDE_RUN": "python -m caisse", "COMMANDE_TESTS": "pytest -q"}), encoding="utf-8")
    s = dest / ".claude/skills/init-from-template/scripts"
    subprocess.run([sys.executable, str(s / "render.py"), "--vars", str(vars_), "--root", str(dest)], check=True, capture_output=True)
    subprocess.run([sys.executable, str(s / "cleanup-for-type.py"), "--type", "python-app", "--root", str(dest)],
                   check=True, capture_output=True)
    (dest / "src").mkdir()
    (dest / "src/app.py").write_text("print('caisse')\n", encoding="utf-8")
    g = dest / ".claude/docs/code-map-gotchas.md"
    g.write_text(g.read_text(encoding="utf-8")
                 + "\n- ⚠️ `src/app.py` — PIEGE-LIVE-42 : les montants sont en centimes (int), jamais en float\n",
                 encoding="utf-8")
    subprocess.run(GIT + ["add", "-A"], cwd=dest, check=True)
    subprocess.run(GIT + ["commit", "-qm", "init"], cwd=dest, check=True)
    return dest


def session(proj: Path, prompt: str, model: str) -> dict:
    r = subprocess.run(["claude", "-p", prompt, "--model", model, "--setting-sources", "project,local",
                        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                        "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"],
                       cwd=proj, capture_output=True, text=True, timeout=300)
    out = {"rc": r.returncode, "startup": "", "session_id": None, "hook_errors": []}
    for line in r.stdout.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        out["session_id"] = out["session_id"] or e.get("session_id")
        if e.get("subtype") == "hook_response":
            if e.get("hook_name", "").startswith("SessionStart"):
                out["startup"] += e.get("stdout") or ""
            if e.get("exit_code") not in (0, None) or "Traceback" in (e.get("stderr") or ""):
                out["hook_errors"].append(f"{e.get('hook_name')}: exit {e.get('exit_code')} {e.get('stderr', '')[:200]}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--ref", default="WORKTREE", help="version du template à tester (tag vX.Y.Z) — défaut : arbre de travail")
    a = ap.parse_args()
    if not shutil.which("claude"):
        print("⏭  binaire `claude` absent — vérification live impossible ici")
        return 0
    tmp = Path(tempfile.mkdtemp(prefix="live-hooks-"))
    proj = make_project(tmp, a.ref)
    net = proj / ".claude/.cache/session-end-snapshot.md"
    slug_dir = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(proj))
    try:
        print(f"== projet jetable : {proj} (claude {subprocess.run(['claude', '--version'], capture_output=True, text=True).stdout.strip()}) ==")
        s1 = session(proj, "Fais exactement ceci, sans poser de question : 1) ajoute la ligne TOTAL_CENTIMES = 0 à la fin "
                           "de src/app.py ; 2) remplace tout le contenu de .claude/docs/HANDOFF.md par deux lignes : "
                           "'# HANDOFF — test live' puis 'Status: ok'. Réponds ensuite uniquement FAIT.", a.model)
        ok("1. session avec /handoff : code 0, hooks sans erreur", s1["rc"] == 0 and not s1["hook_errors"])
        ok("1. aucun filet écrit (HANDOFF mis à jour pendant la session)", not net.exists())
        transcript = next(slug_dir.glob(f"{s1['session_id']}.jsonl"), None) if s1["session_id"] else None
        ok("1. gotcha ciblant src/app.py injecté dans le contexte (PreToolUse)",
           bool(transcript) and "PIEGE-LIVE-42" in transcript.read_text(encoding="utf-8"))
        subprocess.run(GIT + ["add", "-A"], cwd=proj, check=True)
        subprocess.run(GIT + ["commit", "-qm", "session 1"], cwd=proj, check=True)
        s2 = session(proj, "Réponds uniquement par le mot OK.", a.model)
        ok("2. démarrage suivant : AUCUNE alerte « Filet mémoire » (bug v1.4.1)", "Filet mémoire" not in s2["startup"])
        ok("2. session sans trace git → toujours aucun filet", not net.exists())
        s3 = session(proj, "Sans poser de question, ajoute la ligne TVA = 20 à la fin de src/app.py, ne touche à rien "
                           "d'autre, puis réponds uniquement FAIT.", a.model)
        ok("3. code modifié SANS /handoff → filet écrit", s3["rc"] == 0 and net.exists())
        s4 = session(proj, "Réponds uniquement par le mot OK.", a.model)
        ok("4. démarrage suivant : filet injecté", "Filet mémoire" in s4["startup"])
        ok("4. filet = message HUMAIN de la session 3 (ni vide, ni /exit)",
           "TVA = 20" in s4["startup"] and "<command-name>" not in s4["startup"])
        ok("4. filet consommé (jamais réinjecté)", not net.exists())
        ok("aucune erreur de hook sur les 4 sessions",
           not (s1["hook_errors"] + s2["hook_errors"] + s3["hook_errors"] + s4["hook_errors"]))
    finally:
        if not a.keep:
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.rmtree(slug_dir, ignore_errors=True)  # transcripts de CE projet jetable uniquement
    print(f"\n{'🎉 LIVE OK' if FAIL == 0 else '💥 ÉCHECS'} — {PASS} pass, {FAIL} fail")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
