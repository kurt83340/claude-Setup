#!/usr/bin/env python3
"""Harnais Phase 0 × 5 types (PROTOCOL-E2E) — anti-régression sur projets GÉNÉRÉS.

Pour chaque profil de cleanup-for-type : rsync documenté (USAGE §Setup) → chmod hooks →
git init/commit → render --vars (fixture « caisse ») → --check → cleanup-for-type →
traçabilité version stack.md → verify-e2e.py + 3 scans :
  S1. blocs anti-mauvais-routage des SKILL.md survivants : chaque `/ref` = skill survivant,
      builtin ou plugin namespacé (vérifie prune_dead_skill_blocks — c'est lui qui a attrapé F6)
  S2. nav (CLAUDE.md, .claude/CLAUDE.md, template-maintenance, USAGE) : aucune ligne
      bullet/table ne référence un skill supprimé (vérifie prune_dead_inventory)
  S3. contrats v0.19 post-init : Continuation State (HANDOFF), DoD typée + circuit breakers
      + frontmatter status (templates de /spec, si le profil garde /spec)

Usage : python3 test/phase0-harness.py [--workdir DIR] [--types a,b] [--force]
        (défaut : workdir temporaire jeté, les 5 types)

⚠️ Leçon v0.19 encodée : le harnais DÉTRUIT et recrée les jetables (rmtree). Si un jetable
du workdir contient de l'état agentique accumulé (specs numérotées), il REFUSE sans --force —
ne jamais re-runner le harnais après avoir joué Phase B et suivantes sur ces jetables.
"""
import argparse, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent
TYPES = ["script-jetable", "automation-n8n", "python-app", "web-app", "bdd-migration"]
VARS = {
    "PROJECT_NAME": "Caisse Rapide", "CLIENT_NAME": "Boulangerie Martin",
    "PROJECT_FOLDER": "caisse-rapide", "NOM_DECIDEUR": "Sophie Martin",
    "EMAIL_DECIDEUR": "sophie@boulangerie-martin.fr", "TON_NOM": "Julien Leroy",
    "TON_EMAIL": "fr.leroyjulien@gmail.com", "COMMANDE_INSTALL": "pip install -e .[dev]",
    "COMMANDE_RUN": "python -m caisse", "COMMANDE_TESTS": "pytest -q",
}
BUILTINS = {"plugin", "resume", "compact", "clear", "doctor", "init",
            "security-review", "code-review", "loop", "reload-skills"}
NAV = ["CLAUDE.md", ".claude/CLAUDE.md", ".claude/rules/template-maintenance.md", "USAGE.md"]
EXCLUDES = ("EXAMPLES/", "test/", ".github/", ".git/", "plugins/", ".claude-plugin/")


def sh(cmd, cwd=None, check=True):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"CMD KO [{cmd}]\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    return r


def block_lines(text):
    """Lignes de quote du bloc anti-mauvais-routage (marqueur → fin du quote)."""
    out, capture = [], False
    for l in text.split("\n"):
        if "**Quand ne PAS utiliser**" in l:
            capture = True
        if capture:
            if l.lstrip().startswith(">"):
                out.append(l)
            else:
                break
    return out


def etat_agentique(root):
    specs = root / ".claude/docs/conception/specs"
    return specs.is_dir() and any(re.match(r"^\d{3}-", p.name) for p in specs.iterdir())


def run_type(t, workdir, template_skills, version):
    root = workdir / f"jetable-{t}"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    excl = " ".join(f"--exclude='{e}'" for e in EXCLUDES)
    sh(f"rsync -a {excl} {TEMPLATE}/ {root}/")
    sh("chmod +x .claude/hooks/*.py .claude/hooks/*.sh", cwd=root)
    sh("git init -q && git add -A && git -c user.email=e2e@test -c user.name=e2e "
       "commit -qm 'snapshot pre-init'", cwd=root)
    (root / "vars.json").write_text(json.dumps(VARS), encoding="utf-8")
    sh(f"python3 .claude/skills/init-from-template/scripts/render.py --vars vars.json --root {root}", cwd=root)
    sh(f"python3 .claude/skills/init-from-template/scripts/render.py --check --root {root}", cwd=root)
    sh(f"python3 .claude/skills/init-from-template/scripts/cleanup-for-type.py --type {t}", cwd=root)
    st = root / ".claude/docs/stack.md"
    if st.is_file():  # étape Phase 0 « traçabilité version » (agentique → simulée)
        st.write_text(st.read_text(encoding="utf-8")
                      + f"\n> Template claude-Setup v{version} — init E2E mécanique\n", encoding="utf-8")

    verify = sh(f"python3 {TEMPLATE}/test/verify-e2e.py --root {root}", check=False)
    v_last = verify.stdout.strip().splitlines()[-1] if verify.stdout.strip() else verify.stderr[-120:]

    problems = []
    skills = {p.name for p in (root / ".claude/skills").iterdir() if p.is_dir()} \
        if (root / ".claude/skills").is_dir() else set()
    dead = template_skills - skills
    dead_pat = re.compile("`/(?:%s)(?![\\w-])" % "|".join(re.escape(n) for n in sorted(dead))) if dead else None

    for f in sorted((root / ".claude/skills").glob("*/SKILL.md")) if skills else []:
        for r in set(re.findall(r"`/([a-z0-9_:-]+)", "\n".join(block_lines(f.read_text(encoding="utf-8"))))):
            base = r.split('"')[0]
            if ":" in base or base in skills or base in BUILTINS:
                continue
            problems.append(f"S1 skills/{f.parent.name}: bloc route vers `/{base}` (absent)")
    if dead_pat:
        for n in NAV:
            p = root / n
            if not p.is_file():
                continue
            for i, l in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
                if l.lstrip().startswith(("-", "|")) and dead_pat.search(l):
                    problems.append(f"S2 {n}:{i}: réf de skill supprimé")
    ho = root / ".claude/docs/HANDOFF.md"
    if ho.is_file() and "## Continuation State" not in ho.read_text(encoding="utf-8"):
        problems.append("S3 HANDOFF.md sans Continuation State")
    tpl = root / ".claude/skills/spec/templates"
    if "spec" in skills:
        if "command_passes:" not in (tpl / "tasks.md").read_text(encoding="utf-8"):
            problems.append("S3 tasks.md sans DoD typée")
        if "## Circuit breakers" not in (tpl / "plan.md").read_text(encoding="utf-8"):
            problems.append("S3 plan.md sans circuit breakers")
        if "status: draft" not in (tpl / "spec.md").read_text(encoding="utf-8"):
            problems.append("S3 spec.md sans frontmatter status")

    status = verify.returncode == 0 and not problems
    print(f"=== {t} : {'PASS' if status else 'FAIL'} ===  verify-e2e → {v_last} · skills : {len(skills)}")
    for p in problems:
        print(f"  ❌ {p}")
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", type=Path, default=None,
                    help="dossier des jetables (défaut : tmp jeté)")
    ap.add_argument("--types", default=",".join(TYPES))
    ap.add_argument("--force", action="store_true",
                    help="écraser un jetable qui contient de l'état agentique (specs)")
    args = ap.parse_args()
    workdir = args.workdir or Path(tempfile.mkdtemp(prefix="phase0-"))
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    if not args.force:
        for t in types:
            if etat_agentique(workdir / f"jetable-{t}"):
                sys.exit(f"🛑 jetable-{t} contient de l'état agentique (specs 00X) — le harnais "
                         "le DÉTRUIRAIT (leçon v0.19). Relance avec --force en connaissance de cause.")
    template_skills = {p.name for p in (TEMPLATE / ".claude/skills").iterdir() if p.is_dir()}
    version = (TEMPLATE / ".claude/template-version").read_text().strip()
    ok_all = True
    for t in types:
        try:
            ok_all &= run_type(t, workdir, template_skills, version)
        except RuntimeError as e:
            ok_all = False
            print(f"=== {t} : FAIL (harnais) ===\n{e}")
    print("✅ Phase 0 : PASS" if ok_all else "❌ Phase 0 : frictions à corriger")
    if args.workdir is None and ok_all:
        shutil.rmtree(workdir, ignore_errors=True)
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
