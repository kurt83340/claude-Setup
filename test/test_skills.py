#!/usr/bin/env python3
"""Suite de tests des skills du template (structure + conventions + benchmarks).

Pourquoi : un SKILL.md est du code d'instruction — il rote comme du code (référence morte,
convention oubliée) et dégrade l'agent EN SILENCE (constat mesuré chez Citadel : une
instruction stale nuit activement, elle n'est pas neutre). Cette suite vérifie mécaniquement
ce qui est vérifiable sans LLM :

  1. frontmatter : name = nom du dossier, description non vide ;
  2. bloc anti-mauvais-routage : « Quand ne PAS utiliser » nommant ≥ 1 skill voisin EXISTANT
     + « Réversibilité » typée (🟢/🟠/🔴) — convention v0.19, encodée dans /scaffold ;
  3. couplages des templates bundlés (spec/templates/*, HANDOFF) — grammaire DoD typée,
     circuit breakers, frontmatter status, Continuation State ;
  4. scénarios test/benchmarks/ : structure valide (skill existant, input, assertions).

Le COMPORTEMENT des skills se teste en agentique : test/PROTOCOL-E2E.md Phase B déroule les
scénarios de test/benchmarks/ sur un projet jetable. Périmètre : skills cœur (.claude/skills/)
uniquement — les skills de plugins ont leurs propres conventions.

Usage : python3 test/test_skills.py     (exit 0 = tout vert)
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
BENCH = ROOT / "test" / "benchmarks"
PASS = FAIL = 0

# Mêmes conventions de résolution que le check CI « pipelines » (.github/workflows/ci.yml)
BUILTINS = {"plugin", "resume", "compact", "clear", "doctor", "init"}
EXTERNES = {"n8n-mcp-skills"}  # plugins upstream non vendorés


def ok(label, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else: FAIL += 1; print(f"  ❌ {label}")


def frontmatter(text):
    """Retourne (dict clé→valeur brute, corps) — parser minimal stdlib, pas de YAML lib."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    head, body = text[3:end], text[end + 4:]
    fields = {}
    for line in head.splitlines():
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields, body


def known_names():
    """Noms invocables : skills cœur + plugins maison (plugin:skill) + builtins."""
    core = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    house = {f"{pl.parent.parent.name}:{pl.name}"
             for pl in (ROOT / "plugins").glob("*/skills/*") if pl.is_dir()}
    return core, house


CORE, HOUSE = known_names()


def ref_valide(ref):
    base = ref.split('"')[0]
    ns = base.split(":")[0] if ":" in base else None
    return base in CORE or base in HOUSE or ns in EXTERNES or base in BUILTINS


# 1. Structure + convention de chaque skill cœur
print("== skills cœur : frontmatter + bloc anti-mauvais-routage ==")
for d in sorted(SKILLS.iterdir()):
    if not d.is_dir():
        continue
    f = d / "SKILL.md"
    if not f.exists():
        ok(f"{d.name}: SKILL.md présent", False)
        continue
    text = f.read_text(encoding="utf-8")
    meta, body = frontmatter(text)
    ok(f"{d.name}: frontmatter name = dossier", meta.get("name") == d.name)
    ok(f"{d.name}: description non vide (≥ 40 chars)", len(meta.get("description", "")) >= 40)

    # Bloc « Quand ne PAS utiliser » : les lignes de quote qui le contiennent
    lines, block, capture = body.splitlines(), [], False
    for line in lines:
        if "**Quand ne PAS utiliser**" in line:
            capture = True
        if capture:
            if line.strip().startswith(">"):
                block.append(line)
            elif line.strip():
                break
    ok(f"{d.name}: bloc « Quand ne PAS utiliser » présent", bool(block))
    refs = re.findall(r"`/([a-z0-9_:-]+)", "\n".join(block))
    ok(f"{d.name}: ≥ 1 skill voisin nommé dans le bloc", bool(refs))
    for r in sorted(set(refs)):
        ok(f"{d.name}: voisin `/{r.split(chr(34))[0]}` existe", ref_valide(r))
    rev = [l for l in body.splitlines() if "**Réversibilité**" in l]
    ok(f"{d.name}: réversibilité typée (🟢/🟠/🔴)",
       bool(rev) and any(c in "".join(block + rev) for c in "🟢🟠🔴"))

# 2. Couplages des templates bundlés (contrat v0.19 — DoD typée, breakers, status, continuation)
print("\n== templates bundlés : contrats v0.19 ==")
tpl = SKILLS / "spec" / "templates"
for name in ("research.md", "spec.md", "plan.md", "tasks.md"):
    ok(f"spec/templates/{name} présent", (tpl / name).exists())
spec_t = (tpl / "spec.md").read_text(encoding="utf-8") if (tpl / "spec.md").exists() else ""
ok("spec.md template : frontmatter status: draft", spec_t.startswith("---") and "status: draft" in spec_t)
tasks_t = (tpl / "tasks.md").read_text(encoding="utf-8") if (tpl / "tasks.md").exists() else ""
ok("tasks.md template : grammaire DoD typée (command_passes/file_exists/manual)",
   all(k in tasks_t for k in ("command_passes:", "file_exists:", "manual:")))
plan_t = (tpl / "plan.md").read_text(encoding="utf-8") if (tpl / "plan.md").exists() else ""
ok("plan.md template : § Circuit breakers", "## Circuit breakers" in plan_t)
ho_t = (ROOT / ".claude" / "docs" / "HANDOFF.md").read_text(encoding="utf-8")
ok("HANDOFF.md template : § Continuation State (5 clés)",
   "## Continuation State" in ho_t and all(
       k in ho_t for k in ("Spec:", "Task:", "Fichiers en cours:", "Bloqué sur:", "Commande de reprise:")))
ok("skill handoff : compose le Continuation State",
   "## Continuation State" in (SKILLS / "handoff" / "SKILL.md").read_text(encoding="utf-8"))

# 3. Scénarios benchmarks : structure (l'exécution est agentique — PROTOCOL-E2E Phase B)
print("\n== benchmarks : scénarios valides ==")
ok("test/benchmarks/ présent (README + scénarios)", (BENCH / "README.md").exists())
scenarios = sorted(BENCH.glob("*/*.md")) if BENCH.exists() else []
ok("≥ 3 scénarios seed", len(scenarios) >= 3)
for sc in scenarios:
    rel = f"{sc.parent.name}/{sc.name}"
    meta, body = frontmatter(sc.read_text(encoding="utf-8"))
    ok(f"{rel}: dossier = skill cœur existant", sc.parent.name in CORE)
    ok(f"{rel}: frontmatter skill = dossier", meta.get("skill") == sc.parent.name)
    ok(f"{rel}: input non vide", bool(meta.get("input")))
    # listes : `assert-contains:` suivi de lignes `  - …`
    raw = sc.read_text(encoding="utf-8")
    m = re.search(r"^assert-contains:\s*\n((?:\s+-\s+.+\n)+)", raw, re.M)
    ok(f"{rel}: assert-contains ≥ 1 item", bool(m))
    ok(f"{rel}: section ## Attendu non vide", "## Attendu" in body and len(body.split("## Attendu", 1)[-1].strip()) > 20)

print(f"\n{'✅' if FAIL == 0 else '❌'} {PASS} ok, {FAIL} ko")
sys.exit(1 if FAIL else 0)
