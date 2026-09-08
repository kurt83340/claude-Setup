#!/usr/bin/env python3
"""Tests de régression du budget de contexte (v1.4.0) :

  - context-budget.py : ne compte QUE l'auto-chargé (index + @-imports récursifs + rules NON scopées),
    ignore les liens simples et les @ dans les blocs fencés / spans inline, FLAGUE une rule scopée
    `paths:` ré-importée en @ (scoping court-circuité — bug mesuré +12k tokens/session), seuil --max.
  - slim-context.py : migration idempotente d'un projet < v1.4 — journal HANDOFF et gotchas code-map
    déplacés SANS perte, ROADMAP et rules scopées en lien simple, --dry-run sans effet, rejouable.
  - le template vierge tient sous le seuil CI.

Origine : 2026-09-08 — un projet généré d'un mois démarrait à 144k tokens (86k pour 3 docs
auto-chargées sans borne, 12k pour une rule scopée importée) → 59,8k après migration.

Usage : python3 test/test_context_budget.py   (exit 0 = tout vert)
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUDGET = ROOT / ".claude" / "skills" / "doc-health" / "scripts" / "context-budget.py"
SLIM = ROOT / ".claude" / "skills" / "init-from-template" / "scripts" / "slim-context.py"
PASS = FAIL = 0


def ok(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


def write(p: Path, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)


def budget(root, *args):
    r = run(BUDGET, "--root", str(root), "--json", "--no-user", *args)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip().startswith("{") else {})


def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        h.update(str(p.relative_to(root)).encode()); h.update(p.read_bytes())
    return h.hexdigest()


JOURNAL = "\n".join(f"- 2026-08-{d:02d} — session {d} : " + "blabla " * 70 for d in range(1, 21))  # ≈ 9,8k chars → > 4k tok est.
HANDOFF = f"""# HANDOFF — 2026-09-08

**Branche** : `main`

## Status

- ✅ tests verts

## Continuation State (machine-readable — grammaire fixe `Clé: valeur`, 1 ligne chacune)

Spec: aucune
Commande de reprise: aucune

## Journal (append-only — 1 ligne par session, NE JAMAIS réécrire)

{JOURNAL}
"""
CODEMAP = """# Code Map

## Vue d'ensemble (macro)

A → B

## Règles de couplage (⭐ le cœur)

- ❌ `sync` n'importe jamais `api`

## Intention & décisions locales

- pourquoi

## Gotchas (pièges non évidents)

- ⚠️ `src/sync/notion.py` — l'API renvoie 200 même en erreur
- ⚠️ `src/api/` — le cache est invalidé par tout write

## Quand mettre à jour ce fichier

- règle de couplage → ici
- ⚠️ **L'ordre des portes ne se réordonne PAS** (gotcha égaré ici, vécu 2026-09-08) : `src/interp.py`
  ③ avant ② rend ② inatteignable
- ⚠️ `out/veille/` ne se purge JAMAIS
"""


def make_project(tmp: Path) -> Path:
    root = tmp / "proj"
    write(root / "CLAUDE.md", "# P\n\n- Reprise : @.claude/docs/HANDOFF.md\n- Roadmap : @.claude/docs/ROADMAP.md\n"
          "- Code map : @.claude/docs/code-map.md\n- Cadrage : [cadrage](.claude/docs/cadrage/README.md)\n"
          "- exemple en code : `@.claude/docs/lecons.md`\n\n```markdown\n- Reprise : @.claude/docs/stack.md\n```\n"
          "> seuls les 3 docs d'état vivant sont auto-chargés\n")
    write(root / ".claude" / "CLAUDE.md", "# Template\n\n**Lis EN PREMIER** : @rules/template-maintenance.md\n")
    write(root / ".claude" / "rules" / "template-maintenance.md", "---\npaths:\n  - \".claude/docs/**\"\n---\n# TM\n" + "x" * 4000 + "\n")
    write(root / ".claude" / "rules" / "code-style.md", "---\npaths: \"**/*.py\"\n---\n# style\n" + "y" * 800 + "\n")
    write(root / ".claude" / "rules" / "git-workflow.md", "# git\n" + "z" * 600 + "\n")
    write(root / ".claude" / "docs" / "HANDOFF.md", HANDOFF)
    write(root / ".claude" / "docs" / "ROADMAP.md", "# Roadmap\n" + "r" * 3000 + "\n")
    write(root / ".claude" / "docs" / "code-map.md", CODEMAP)
    write(root / ".claude" / "docs" / "lecons.md", "# leçons\n" + "l" * 3000 + "\n")
    write(root / ".claude" / "docs" / "stack.md", "# stack\n" + "s" * 3000 + "\n")
    write(root / ".claude" / "docs" / "cadrage" / "README.md", "# cadrage\n")
    write(root / ".claude" / "skills" / "doc-health" / "SKILL.md", "---\nname: doc-health\ndescription: audit\n---\n# x\n")
    write(root / ".claude" / "hooks" / "pretooluse-inject-codemap.py", "# old hook\n")
    write(root / ".claude" / "rules" / "agent-teams.md", "# old long rule\n" + "t" * 9000 + "\n")
    return root


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)

    print("== 1. context-budget.py : périmètre auto-chargé exact ==")
    p = make_project(tmp)
    rc, j = budget(p)
    files = {f["path"]: f for f in j.get("files", [])}
    ok("exit 0 sans seuil", rc == 0)
    ok("index racine + .claude/CLAUDE.md comptés", "CLAUDE.md" in files and ".claude/CLAUDE.md" in files)
    ok("@-imports HANDOFF / ROADMAP / code-map comptés (via CLAUDE.md)",
       all(f".claude/docs/{n}.md" in files for n in ("HANDOFF", "ROADMAP", "code-map"))
       and files[".claude/docs/HANDOFF.md"]["via"] == "CLAUDE.md")
    ok("lien simple (cadrage) NON compté", ".claude/docs/cadrage/README.md" not in files)
    ok("@ dans un span inline / bloc fencé NON comptés (lecons, stack)",
       ".claude/docs/lecons.md" not in files and ".claude/docs/stack.md" not in files)
    ok("rule NON scopée (git-workflow) comptée", ".claude/rules/git-workflow.md" in files
       and files[".claude/rules/git-workflow.md"]["kind"] == "rule")
    ok("rule scopée paths: (code-style) → à la demande, pas comptée",
       ".claude/rules/code-style.md" not in files
       and any(r["path"] == ".claude/rules/code-style.md" for r in j["on_demand_rules"]))
    tm = files.get(".claude/rules/template-maintenance.md")
    ok("rule scopée ré-importée en @ → comptée ET flaguée « scoping court-circuité »",
       tm is not None and tm["scoped_import"] and "retirer le @" in tm["remedy"])
    ok("HANDOFF gros → remède journal proposé", "journal" in files[".claude/docs/HANDOFF.md"]["remedy"].lower())
    ok("total = somme des fichiers, estimation chars/2",
       j["total_tok"] == sum(f["tok"] for f in j["files"]) and files["CLAUDE.md"]["tok"] == files["CLAUDE.md"]["chars"] // 2)
    rc_max, _ = budget(p, "--max", "10")
    ok("--max dépassé → exit 1", rc_max == 1)
    r_txt = run(BUDGET, "--root", str(p), "--no-user", "--max", "10")
    ok("sortie texte : 🔴 + seuil dépassé", "🔴" in r_txt.stdout and "Seuil dépassé" in r_txt.stdout)
    total_before = j["total_tok"]

    print("\n== 2. slim-context.py : --dry-run sans effet ==")
    h0 = tree_hash(p)
    r = run(SLIM, "--root", str(p), "--dry-run", "--no-template-files")
    ok("exit 0", r.returncode == 0)
    ok("aucun fichier modifié", tree_hash(p) == h0)
    ok("annonce les 5 étapes en [DRY] (1, 2, 3, 3b, 4)", r.stdout.count("[DRY] ✅") == 5)

    print("\n== 3. slim-context.py : migration réelle, sans perte ==")
    r = run(SLIM, "--root", str(p), "--template", str(ROOT))
    ok("exit 0", r.returncode == 0)
    ho = (p / ".claude/docs/HANDOFF.md").read_text(encoding="utf-8")
    jo = p / ".claude/docs/HANDOFF-journal.md"
    ok("HANDOFF : § Journal retiré, pointeur HANDOFF-journal.md présent, Continuation State intact",
       "## Journal" not in ho and "HANDOFF-journal.md" in ho and "## Continuation State" in ho)
    ok("HANDOFF-journal.md créé avec les 20 entrées intactes",
       jo.is_file() and all(f"- 2026-08-{d:02d} — session {d}" in jo.read_text(encoding="utf-8") for d in range(1, 21)))
    cm = (p / ".claude/docs/code-map.md").read_text(encoding="utf-8")
    gf = p / ".claude/docs/code-map-gotchas.md"
    ok("code-map : § Gotchas remplacé par le pointeur, couplage + « Quand mettre à jour » intacts",
       "## Gotchas → `code-map-gotchas.md`" in cm and "l'API renvoie 200" not in cm
       and "## Règles de couplage" in cm and "## Quand mettre à jour" in cm)
    ok("code-map-gotchas.md créé avec les 2 entrées (chemins en backticks conservés)",
       gf.is_file() and "`src/sync/notion.py`" in gf.read_text(encoding="utf-8") and "`src/api/`" in gf.read_text(encoding="utf-8"))
    ok("« Quand mettre à jour » : entrées ⚠️ égarées → gotchas (continuation incluse), consigne conservée",
       "L'ordre des portes" not in cm and "ne se purge JAMAIS" not in cm and "- règle de couplage → ici" in cm
       and "L'ordre des portes" in gf.read_text(encoding="utf-8") and "③ avant ②" in gf.read_text(encoding="utf-8")
       and "Migrés depuis « Quand mettre à jour" in gf.read_text(encoding="utf-8"))
    idx = (p / ".claude/CLAUDE.md").read_text(encoding="utf-8")
    ok(".claude/CLAUDE.md : @rules/template-maintenance.md → lien simple",
       "@rules/template-maintenance.md" not in idx and "[rules/template-maintenance.md](rules/template-maintenance.md)" in idx)
    cl = (p / "CLAUDE.md").read_text(encoding="utf-8")
    ok("CLAUDE.md : @ROADMAP → lien simple, HANDOFF/code-map toujours en @, « 3 docs » → « 2 docs »",
       "@.claude/docs/ROADMAP.md" not in cl and "[ROADMAP.md](.claude/docs/ROADMAP.md)" in cl
       and "@.claude/docs/HANDOFF.md" in cl and "@.claude/docs/code-map.md" in cl and "seuls les 2 docs" in cl)
    ok("fichiers v1.4 copiés depuis le template (hook + rule courte), ancienne rule sauvegardée",
       (p / ".claude/hooks/pretooluse-inject-codemap.py").read_bytes() == (ROOT / ".claude/hooks/pretooluse-inject-codemap.py").read_bytes()
       and (p / ".claude/rules/agent-teams.md").read_bytes() == (ROOT / ".claude/rules/agent-teams.md").read_bytes()
       and (p / ".claude/.cache/agent-teams.md.pre-1.4").is_file()
       and (p / ".claude/skills/doc-health/scripts/context-budget.py").is_file())
    rc2, j2 = budget(p)
    files2 = {f["path"] for f in j2["files"]}
    ok("budget après migration : rule scopée + ROADMAP sortis de l'auto-chargé, total en baisse",
       ".claude/rules/template-maintenance.md" not in files2 and ".claude/docs/ROADMAP.md" not in files2
       and j2["total_tok"] < total_before // 2)

    print("\n== 4. slim-context.py : idempotent (rejouer = no-op) ==")
    h1 = tree_hash(p)
    r = run(SLIM, "--root", str(p), "--template", str(ROOT))
    ok("exit 0 et aucun fichier modifié au 2e passage", r.returncode == 0 and tree_hash(p) == h1)
    ok("toutes les étapes annoncées « déjà fait »", "✅" not in r.stdout.replace("→ Vérifie", ""))

    print("\n== 5. slim-context.py : projet sans journal ni gotchas (post-v1.4) ==")
    q = tmp / "fresh"
    write(q / ".claude" / "docs" / "HANDOFF.md", "# HANDOFF\n\n## Status\n\n- ok\n")
    write(q / ".claude" / "docs" / "code-map.md", "# CM\n\n## Gotchas → `code-map-gotchas.md`\n\npointeur\n")
    write(q / "CLAUDE.md", "# P\n- @.claude/docs/HANDOFF.md\n")
    r = run(SLIM, "--root", str(q), "--no-template-files")
    ho = (q / ".claude/docs/HANDOFF.md").read_text(encoding="utf-8")
    ok("HANDOFF sans § Journal → seul le pointeur est ajouté, contenu intact",
       r.returncode == 0 and "## Status" in ho and "HANDOFF-journal.md" in ho and not (q / ".claude/docs/HANDOFF-journal.md").exists())
    ok("code-map déjà migrée → non touchée", "⏭ 3." in r.stdout)

    print("\n== 6. Template vierge : sous le seuil CI ==")
    r = run(BUDGET, "--root", str(ROOT), "--no-user", "--max", "12000")
    ok("context-budget --max 12000 sur le template → exit 0", r.returncode == 0)
    rc, j = budget(ROOT)
    files = {f["path"]: f for f in j["files"]}
    ok("template : aucune rule scopée importée en @", not any(f["scoped_import"] for f in j["files"]))
    ok("template : HANDOFF + code-map en @, ROADMAP en lien",
       ".claude/docs/HANDOFF.md" in files and ".claude/docs/code-map.md" in files and ".claude/docs/ROADMAP.md" not in files)
    ok("template : template-maintenance.md à la demande (paths:)",
       any(x["path"] == ".claude/rules/template-maintenance.md" for x in j["on_demand_rules"]))
    print(f"     (template vierge : {j['total_tok']} tok est. auto-chargés — projet)")

print(f"\n{'🎉 CONTEXT BUDGET OK' if FAIL == 0 else '💥 ÉCHECS'} — {PASS} pass, {FAIL} fail")
sys.exit(0 if FAIL == 0 else 1)
