#!/usr/bin/env python3
"""Régression des commandes rsync DOCUMENTÉES (README, USAGE, /adopt-template), jouées pour de vrai.

Pourquoi : un motif rsync sans « / » initial vaut à TOUS les niveaux (« otherwise it is matched
against the end of the pathname », man rsync). Vécu sur un projet adopté : `--exclude='README.md'`
a écarté en silence 11 README imbriqués, dont `.claude/skills/README.md` (l'inventaire que la CI
vérifie) et `.claude/agents/README.md`. Même risque pour `.env.example`, `test/`, `plugins/`…
Et `/.git/` (« / » final = dossiers seulement) laissait passer le `.git` d'un worktree, qui est un
FICHIER : le projet se retrouvait rattaché au dépôt du template (vu en jouant ce test dans un worktree).

Chaque commande `rsync` des blocs de code est extraite, ses `--exclude` doivent être ancrés, puis
elle est exécutée (source = ce dépôt, destination = un dossier temporaire) : les fichiers imbriqués
du template doivent arriver, les dossiers de maintenance rester dehors, et en brownfield le README
et le `.env.example` du projet ne doivent pas être remplacés.

Usage : python3 test/test_rsync_docs.py     (exit 0 = tout vert ; rsync requis)
"""
import re, shlex, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = (".github/README.md", ".claude/USAGE.md", ".claude/skills/adopt-template/SKILL.md")
NESTED = (".claude/skills/README.md", ".claude/agents/README.md", ".claude/docs/adr/README.md",
          ".claude/docs/specs/README.md")
MAINTENANCE = ("EXAMPLES", "test", ".github", "plugins", ".claude-plugin", ".git")
PASS = FAIL = 0


def ok(label, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else: FAIL += 1; print(f"  ❌ {label}")


def rsync_commands(text: str):
    """Commandes `rsync …` (lignes de continuation `\\` jointes) des blocs de code d'un markdown."""
    cmds = []
    for block in re.findall(r"```[a-z]*\n(.*?)```", text, re.S):
        logical = re.sub(r"\\\n\s*", " ", block)
        cmds += [l.strip() for l in logical.split("\n") if l.strip().startswith("rsync ")]
    return cmds


if not shutil.which("rsync"):
    print("❌ rsync introuvable")
    sys.exit(1)

tmp = Path(tempfile.mkdtemp(prefix="rsyncdocs-"))
try:
    total = 0
    for doc in DOCS:
        print(f"\n== {doc} ==")
        cmds = rsync_commands((ROOT / doc).read_text(encoding="utf-8"))
        ok("au moins une commande rsync documentée", bool(cmds))
        for k, cmd in enumerate(cmds):
            total += 1
            toks = shlex.split(cmd)
            excl = [t.split("=", 1)[1] for t in toks if t.startswith("--exclude=")]
            brown = "--ignore-existing" in toks
            kind = "brownfield" if brown else "greenfield"
            loose = [e for e in excl if not e.startswith("/")]
            ok(f"[{kind} #{k + 1}] tous les --exclude ancrés (« / » initial)" + (f" — fautifs : {loose}" if loose else ""),
               bool(excl) and not loose)
            pos = [i for i, t in enumerate(toks) if i > 0 and not t.startswith("-")]
            dest = tmp / f"{Path(doc).stem}-{k}"
            dest.mkdir(parents=True)
            if brown:  # projet existant : son README et son .env.example ne doivent jamais bouger
                (dest / "README.md").write_text("# Mon projet\n", encoding="utf-8")
                (dest / ".env.example").write_text("MA_VAR=\n", encoding="utf-8")
            run = toks[:]
            run[pos[-2]], run[pos[-1]] = f"{ROOT}/", f"{dest}/"
            r = subprocess.run([a for a in run if a != "-av"] + ["-a"], capture_output=True, text=True)
            ok(f"[{kind} #{k + 1}] commande exécutée sans erreur", r.returncode == 0)
            missing = [n for n in NESTED if not (dest / n).is_file()]
            ok(f"[{kind} #{k + 1}] README imbriqués du template copiés (skills, agents, docs)"
               + (f" — manquants : {missing}" if missing else ""), not missing)
            leaked = [d for d in MAINTENANCE if (dest / d).exists()]
            ok(f"[{kind} #{k + 1}] dossiers de maintenance du template laissés dehors"
               + (f" — copiés : {leaked}" if leaked else ""), not leaked)
            if brown:
                ok(f"[{kind} #{k + 1}] README.md et .env.example du projet intacts",
                   (dest / "README.md").read_text(encoding="utf-8") == "# Mon projet\n"
                   and (dest / ".env.example").read_text(encoding="utf-8") == "MA_VAR=\n")
            # Template cloné en worktree (ou --separate-git-dir) : .git est un FICHIER — déterministe
            # ici, quel que soit le checkout de la CI.
            syn, sdest = tmp / f"syn-{Path(doc).stem}-{k}", tmp / f"syn-dest-{Path(doc).stem}-{k}"
            (syn / ".claude" / "skills").mkdir(parents=True)
            (syn / ".git").write_text("gitdir: /ailleurs/.git/worktrees/x\n", encoding="utf-8")
            (syn / ".claude" / "skills" / "README.md").write_text("# inventaire\n", encoding="utf-8")
            sdest.mkdir()
            run[pos[-2]], run[pos[-1]] = f"{syn}/", f"{sdest}/"
            subprocess.run([a for a in run if a != "-av"] + ["-a"], capture_output=True, text=True)
            ok(f"[{kind} #{k + 1}] `.git` FICHIER (worktree) non copié, README imbriqué copié",
               not (sdest / ".git").exists() and (sdest / ".claude/skills/README.md").is_file())
    ok("commandes greenfield ET brownfield couvertes", total >= 4)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{'🎉 RSYNC DOCS OK' if FAIL == 0 else '💥 ÉCHECS'} — {PASS} pass, {FAIL} fail")
sys.exit(0 if FAIL == 0 else 1)
