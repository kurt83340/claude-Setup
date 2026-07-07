#!/usr/bin/env python3
"""verify-e2e.py — invariants post-run du protocole E2E (test/PROTOCOL-E2E.md).

À pointer sur un projet JETABLE après une session agentique complète :
    python3 test/verify-e2e.py --root /chemin/du/jetable

Chaque check ne s'applique que si la matière existe (un jetable partiel ne FAIL pas
sur ce qu'il n'a pas exercé) ; exit 0 = tous les invariants vérifiables sont verts.
Stdlib uniquement, comme les autres suites.
"""
import argparse
import json
import re
import sys
from pathlib import Path

PASS = FAIL = SKIP = 0


def ok(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


def skip(label):
    global SKIP
    SKIP += 1
    print(f"  ⏭️  {label} (matière absente)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    root = ap.parse_args().root.resolve()
    docs = root / ".claude" / "docs"

    print(f"🔎 verify-e2e sur {root}\n")

    # ── Init propre ──────────────────────────────────────────────────────────
    print("== init ==")
    perim = [root / "CLAUDE.md", root / "README.md", root / ".env.example",
             root / ".claude" / "CLAUDE.md"]
    core_re = re.compile(r"\{\{[A-Z]{2,}_[A-Z][A-Z0-9_]+\}\}")
    leftovers = []
    for base in perim + [p for d in (docs, root / ".claude" / "rules") if d.is_dir()
                         for p in d.rglob("*.md")]:
        if isinstance(base, Path) and base.is_file() and core_re.search(base.read_text(encoding="utf-8", errors="ignore")):
            leftovers.append(str(base.relative_to(root)))
    ok("0 placeholder CORE dans le périmètre substitué", not leftovers)
    if leftovers:
        print(f"     → {leftovers[:5]}")
    ok("skills bootstrap absents",
       not (root / ".claude/skills/init-from-template").exists()
       and not (root / ".claude/skills/adopt-template").exists())
    tcl = root / ".claude" / "template-version"
    ok(".claude/template-version présent", tcl.is_file())
    claude_md = root / "CLAUDE.md"
    if claude_md.is_file():
        n = len(re.findall(r"@\.claude/\S+", claude_md.read_text(encoding="utf-8")))
        ok(f"CLAUDE.md = 3 @-imports (trouvés : {n})", n == 3)
    inv = root / ".claude" / "CLAUDE.md"
    if inv.is_file():
        t = inv.read_text(encoding="utf-8")
        ok("inventaire sans réf bootstrap", "/init-from-template" not in t and "/adopt-template" not in t)

    # ── settings.json ────────────────────────────────────────────────────────
    print("\n== settings ==")
    sp = root / ".claude" / "settings.json"
    if sp.is_file():
        try:
            settings = json.loads(sp.read_text(encoding="utf-8"))
            ok("settings.json JSON valide", True)
        except Exception:
            settings = {}
            ok("settings.json JSON valide", False)
        script_re = re.compile(r"(?<![\w~/.\\-])\.claude/[^\s:\"']+\.(?:py|sh)")
        dead = []
        for rule in settings.get("permissions", {}).get("allow", []):
            m = script_re.search(rule) if isinstance(rule, str) else None
            if m and not any(c in m.group(0) for c in "*?[") and not (root / m.group(0)).exists():
                dead.append(rule)
        ok("0 allow-rule vers script absent", not dead)
    else:
        skip("settings.json")

    # ── Specs & ROADMAP ─────────────────────────────────────────────────────
    print("\n== specs / roadmap ==")
    specs_dir = docs / "conception" / "specs"
    specs = sorted(d for d in specs_dir.iterdir() if d.is_dir()) if specs_dir.is_dir() else []
    if specs:
        for d in specs:
            files = {f.name for f in d.glob("*.md")}
            ok(f"{d.name} : 4 fichiers (research/spec/plan/tasks)",
               {"research.md", "spec.md", "plan.md", "tasks.md"} <= files)
            ok(f"{d.name} : 0 {{{{SPEC_*}}}} restant",
               not any("{{SPEC_" in f.read_text(encoding="utf-8") for f in d.glob("*.md")))
        nums = [int(m.group(1)) for d in specs if (m := re.match(r"(\d{3})-", d.name))]
        ok(f"numérotation continue depuis 001 ({nums})",
           nums == list(range(1, len(nums) + 1)))
        roadmap = docs / "ROADMAP.md"
        if roadmap.is_file():
            rt = roadmap.read_text(encoding="utf-8")
            missing = [d.name for d in specs if d.name not in rt]
            ok("chaque spec référencée dans ROADMAP", not missing)
    else:
        skip("specs/")

    # ── ADRs ────────────────────────────────────────────────────────────────
    print("\n== adr ==")
    adr_dir = docs / "adr"
    adrs = sorted(adr_dir.glob("[0-9]*.md")) if adr_dir.is_dir() else []
    if adrs:
        statuses = {}
        for f in adrs:
            t = f.read_text(encoding="utf-8")
            m = re.search(r"^status:\s*(\w+)", t, re.M)
            num = re.match(r"(\d+)", f.name).group(1)
            statuses[num] = (m.group(1) if m else "?", t)
        ok("statuts ADR valides",
           all(s in {"proposed", "accepted", "deprecated", "superseded"} for s, _ in statuses.values()))
        bad = []
        for num, (s, t) in statuses.items():
            m = re.search(r"^supersedes:\s*(\d+)", t, re.M)
            if m:
                old = m.group(1).zfill(len(num))
                if statuses.get(old, ("?",))[0] != "superseded":
                    bad.append(f"{num}→{old}")
        ok("chaque supersedes: pointe un ADR passé en superseded", not bad)
    else:
        skip("adr/")

    # ── Leçons / CHANGELOG / HANDOFF ────────────────────────────────────────
    print("\n== docs vivants ==")
    lec = docs / "lecons.md"
    if lec.is_file() and re.search(r"^## \d{4}-", lec.read_text(encoding="utf-8"), re.M):
        ok("leçons : chaque entrée porte un statut",
           all("🆕" in b or "📜" in b or "🔧" in b or "🧠" in b or "❌" in b or "📦" in b
               for b in re.findall(r"^## \d{4}-.*(?:\n(?!## ).*)*", lec.read_text(encoding="utf-8"), re.M)))
    else:
        skip("lecons.md (aucune entrée)")
    ho = docs / "HANDOFF.md"
    if ho.is_file():
        ok("HANDOFF sans placeholder {{ }}", "{{" not in ho.read_text(encoding="utf-8"))
    st = docs / "stack.md"
    if st.is_file():
        ok("stack.md trace la version du template",
           re.search(r"claude-Setup v\d+\.\d+\.\d+", st.read_text(encoding="utf-8")) is not None)
    else:
        skip("stack.md")

    print(f"\n{'🎉 INVARIANTS OK' if FAIL == 0 else '💥 ÉCHECS'} — {PASS} pass, {FAIL} fail, {SKIP} skip")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
