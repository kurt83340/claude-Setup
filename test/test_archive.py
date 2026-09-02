#!/usr/bin/env python3
"""Suite de régression d'archive-projet.py (skill /archive-projet).

Couvre : pré-flights (pas un projet, déjà archivé, worktrees actifs, destination occupée),
marqueur .claude/archived (4 clés), bannière CLAUDE.md (insert au top / strip au restore),
dry-run strictement sans écriture, commande finale (mkdir + mv projet + mv auto-memory quand
le slug existe, note « rien à migrer » sinon), scan des références internes, restore
(retour marqueur, --dest override, non-archivé), status. Home fake via $ARCHIVE_PROJET_HOME.

Stdlib pur, jetables sous tempfile. Usage : python3 test/test_archive.py  (exit 0 = vert)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / ".claude" / "skills" / "archive-projet" / "scripts" / "archive-projet.py"
PASS = FAIL = 0


def ok(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


def run(fake_home, *args, cwd=None):
    env = dict(os.environ, ARCHIVE_PROJET_HOME=str(fake_home))
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, env=env, cwd=cwd)


def expected_slug(path):
    # Verrou de régression : même règle que slug() du script (non-alphanum → '-')
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def make_project(base, name="projet_x"):
    root = base / name
    (root / ".claude").mkdir(parents=True)
    (root / "CLAUDE.md").write_text("# projet_x\n\nContenu projet.\n", encoding="utf-8")
    (root / "notes.md").write_text(f"script local : {root}/run.sh\n", encoding="utf-8")
    return root


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    fake_home = base / "home"
    (fake_home / ".claude" / "projects").mkdir(parents=True)

    # ── Pré-flights ────────────────────────────────────────────────────────────
    print("== pré-flights ==")
    vide = base / "pas-un-projet"
    vide.mkdir()
    r = run(fake_home, "archive", "--reason", "x", "--root", str(vide))
    ok("dossier sans .claude/ → refus (exit 2)", r.returncode == 2 and ".claude/ absent" in r.stdout)

    p1 = make_project(base)
    mem1 = fake_home / ".claude" / "projects" / expected_slug(p1)
    (mem1 / "memory").mkdir(parents=True)

    # ── Dry-run : zéro écriture ───────────────────────────────────────────────
    print("\n== archive --dry-run ==")
    r = run(fake_home, "archive", "--reason", "test livré", "--root", str(p1), "--dry-run")
    ok("dry-run : exit 0", r.returncode == 0)
    ok("dry-run : marqueur NON écrit", not (p1 / ".claude" / "archived").exists())
    ok("dry-run : bannière NON écrite", "PROJET ARCHIVÉ" not in (p1 / "CLAUDE.md").read_text())
    ok("dry-run : commande finale quand même affichée", "COMMANDE FINALE" in r.stdout)
    ok("dry-run : scan interne détecte notes.md", "notes.md" in r.stdout)

    # ── Archive réel ──────────────────────────────────────────────────────────
    print("\n== archive réel ==")
    r = run(fake_home, "archive", "--reason", "test livré", "--root", str(p1))
    ok("archive : exit 0", r.returncode == 0)
    marker = (p1 / ".claude" / "archived").read_text(encoding="utf-8")
    ok("marqueur : 4 clés présentes",
       all(k in marker for k in ("archived:", "reason:", "original-path:", "archived-path:")))
    ok("marqueur : raison conservée", "test livré" in marker)
    dest_default = p1.parent / "_archives" / p1.name
    ok("marqueur : destination par défaut = <parent>/_archives/<nom>", str(dest_default) in marker)
    cm = (p1 / "CLAUDE.md").read_text(encoding="utf-8")
    ok("bannière : insérée en tête (marqueurs HTML)",
       cm.startswith("<!-- archive-projet:start -->") and "<!-- archive-projet:end -->" in cm)
    ok("bannière : mentionne restore", "/archive-projet restore" in cm)
    ok("bannière : contenu original préservé", "Contenu projet." in cm)
    ok("commande finale : mkdir + mv projet",
       f"mkdir -p '{dest_default.parent}'" in r.stdout and f"mv '{p1}' '{dest_default}'" in r.stdout)
    ok("commande finale : migration auto-memory (slug source → slug destination)",
       f"mv '{mem1}' '{fake_home / '.claude' / 'projects' / expected_slug(dest_default)}'" in r.stdout)

    r = run(fake_home, "archive", "--reason", "re", "--root", str(p1))
    ok("re-archive → refus (exit 2, déjà archivé)", r.returncode == 2 and "déjà archivé" in r.stdout)

    r = run(fake_home, "status", "--root", str(p1))
    ok("status : archivé (raison + chemins)", "test livré" in r.stdout and "original-path" in r.stdout)

    # ── Restore (après move simulé, comme en réel) ────────────────────────────
    print("\n== restore ==")
    # Simuler la commande finale que l'utilisateur aurait lancée (mv projet + mv mémoire)
    dest_default.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(p1), str(dest_default))
    mem_arch = fake_home / ".claude" / "projects" / expected_slug(dest_default)
    shutil.move(str(mem1), str(mem_arch))
    r = run(fake_home, "restore", "--root", str(dest_default), "--dry-run")
    ok("restore dry-run : exit 0, rien retiré", r.returncode == 0
       and (dest_default / ".claude" / "archived").exists()
       and "PROJET ARCHIVÉ" in (dest_default / "CLAUDE.md").read_text())
    r = run(fake_home, "restore", "--root", str(dest_default))
    ok("restore : exit 0", r.returncode == 0)
    ok("restore : marqueur retiré", not (dest_default / ".claude" / "archived").exists())
    cm = (dest_default / "CLAUDE.md").read_text(encoding="utf-8")
    ok("restore : bannière retirée, contenu intact",
       "archive-projet:start" not in cm and cm.startswith("# projet_x"))
    ok("restore : commande de retour vers original-path",
       f"mv '{dest_default}' '{p1}'" in r.stdout)
    ok("restore : migration mémoire retour (slug archivé → slug origine)",
       f"mv '{mem_arch}' '{mem1}'" in r.stdout)
    r = run(fake_home, "restore", "--root", str(dest_default))
    ok("restore sur non-archivé → refus (exit 2)", r.returncode == 2 and "non archivé" in r.stdout)
    r = run(fake_home, "status", "--root", str(dest_default))
    ok("status : non archivé", "non archivé" in r.stdout)

    # ── Restore in-place (archivé mais commande finale jamais lancée) ─────────
    p1b = make_project(base, "projet_inplace")
    run(fake_home, "archive", "--reason", "oops", "--root", str(p1b))
    r = run(fake_home, "restore", "--root", str(p1b))
    ok("restore in-place (jamais déplacé) : exit 0, « aucun move nécessaire », marquage retiré",
       r.returncode == 0 and "aucun move nécessaire" in r.stdout
       and not (p1b / ".claude" / "archived").exists()
       and "PROJET ARCHIVÉ" not in (p1b / "CLAUDE.md").read_text())

    # ── --dest custom + destination occupée + restore --dest ──────────────────
    print("\n== --dest custom & collisions ==")
    p2 = make_project(base, "projet_y")
    dest2 = base / "coffre" / "projet_y"
    r = run(fake_home, "archive", "--reason", "pause", "--root", str(p2), "--dest", str(dest2))
    ok("--dest custom : exit 0 + marqueur pointe la dest custom",
       r.returncode == 0 and str(dest2) in (p2 / ".claude" / "archived").read_text())
    ok("--dest custom : commande finale utilise la dest custom", f"mv '{p2}' '{dest2}'" in r.stdout)
    ok("sans auto-memory : note « rien à migrer », pas de mv mémoire",
       "rien à migrer" in r.stdout and "projects" not in r.stdout.split("COMMANDE FINALE")[-1])
    back2 = base / "retour" / "projet_y"
    r = run(fake_home, "restore", "--root", str(p2), "--dest", str(back2))
    ok("restore --dest override : commande vers la nouvelle cible", f"mv '{p2}' '{back2}'" in r.stdout)

    p3 = make_project(base, "projet_z")
    (base / "_archives" / "projet_z").mkdir(parents=True)
    r = run(fake_home, "archive", "--reason", "x", "--root", str(p3))
    ok("destination occupée → refus (exit 2)", r.returncode == 2 and "occupée" in r.stdout)

    # ── Worktrees actifs → blocage ────────────────────────────────────────────
    print("\n== git worktrees ==")
    p4 = make_project(base, "projet_git")
    git(p4, "init", "-q")
    git(p4, "config", "user.email", "t@t.t")
    git(p4, "config", "user.name", "t")
    git(p4, "add", "-A")
    git(p4, "commit", "-q", "-m", "init")
    wt = base / "projet_git--wt"
    has_wt = git(p4, "worktree", "add", "-q", str(wt), "-b", "wt").returncode == 0
    r = run(fake_home, "archive", "--reason", "x", "--root", str(p4))
    ok("worktree actif → refus (exit 2)", has_wt and r.returncode == 2 and "worktree" in r.stdout)
    git(p4, "worktree", "remove", str(wt))
    (p4 / "sale.txt").write_text("x", encoding="utf-8")
    r = run(fake_home, "archive", "--reason", "x", "--root", str(p4))
    ok("worktree retiré + tree sale → passe avec warning commit",
       r.returncode == 0 and "non committées" in r.stdout)

    # ── CLAUDE.md absent : marqueur seul ──────────────────────────────────────
    print("\n== CLAUDE.md absent ==")
    p5 = base / "sans_claudemd"
    (p5 / ".claude").mkdir(parents=True)
    r = run(fake_home, "archive", "--reason", "x", "--root", str(p5))
    ok("sans CLAUDE.md : exit 0 + bannière sautée avec warning + marqueur écrit",
       r.returncode == 0 and "bannière sautée" in r.stdout
       and (p5 / ".claude" / "archived").exists())

print(f"\n{'🎉 ARCHIVE OK' if FAIL == 0 else '❌ ARCHIVE KO'} — {PASS} pass, {FAIL} fail")
sys.exit(1 if FAIL else 0)
