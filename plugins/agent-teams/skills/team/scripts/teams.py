#!/usr/bin/env python3
"""Interrupteur des agent teams d'un projet — `/agent-teams:team on | off | status` (plugin 1.2.0).

    python3 teams.py status [--root DIR] [--json]
    python3 teams.py on  [--scope project|local|user] [--root DIR] [--dry-run]
    python3 teams.py off [--scope project|local|user] [--root DIR] [--dry-run]

Ce que ça touche, et rien d'autre :
- le flag `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` dans les settings, par ordre de priorité Claude
  Code : `.claude/settings.local.json` > `.claude/settings.json` > `~/.claude/settings.json`
  (`CLAUDE_CONFIG_DIR` respecté ; les managed settings, au-dessus de tout, ne sont ni lues ni écrites) ;
- `teammateMode` (`on` pose "auto" seulement si aucun fichier ne le définit) ;
- la rule héritée `.claude/rules/agent-teams.md` (plugin ≤ 1.1, v1.4 du template) : déplacée dans
  `.claude/.cache/agent-teams.md.obsolete` — les invariants sont désormais injectés au spawn par le
  hook du plugin, la rule ne faisait plus que coûter ~1,9k tokens à chaque session.

`on` exige une relance (l'équipe est montée au démarrage de la session). `off` vaut pour les
prochains spawns sans relance (Claude Code relit le flag à chaque spawn — doc agent teams).
Un settings en JSON invalide n'est jamais réécrit : code 2 et message. Stdlib uniquement.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

TEAM_ENV = "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"
RULE = Path(".claude/rules/agent-teams.md")
RULE_BAK = Path(".claude/.cache/agent-teams.md.obsolete")
SCOPES = ("local", "project", "user")  # priorité décroissante


def truthy(v) -> bool:
    return v is not None and str(v).strip().lower() in ("1", "true", "yes", "on")


def paths(root: Path) -> dict:
    user_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return {"local": root / ".claude" / "settings.local.json",
            "project": root / ".claude" / "settings.json",
            "user": user_dir / "settings.json"}


def load(p: Path):
    """(dict, erreur) — fichier absent = dict vide, JSON invalide = (None, message)."""
    if not p.is_file():
        return {}, None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, f"{p} : JSON illisible ({e})"
    return (d, None) if isinstance(d, dict) else (None, f"{p} : pas un objet JSON")


def flag_of(d):
    env = d.get("env") if isinstance(d, dict) else None
    return env.get(TEAM_ENV) if isinstance(env, dict) else None


def state(root: Path) -> dict:
    ps = paths(root)
    files, errors = {}, []
    for s in SCOPES:
        d, err = load(ps[s])
        if err:
            errors.append(err)
        files[s] = d
    flags = {s: flag_of(files[s]) for s in SCOPES}
    modes = {s: (files[s] or {}).get("teammateMode") for s in SCOPES}
    src = next((s for s in SCOPES if flags[s] is not None), None)
    session = os.environ.get(TEAM_ENV)
    effective = truthy(flags[src]) if src else truthy(session)  # sans settings : export shell (ou managed)
    mode_src = next((s for s in SCOPES if modes[s] is not None), None)
    rule = root / RULE
    return {"root": str(root), "paths": {s: str(ps[s]) for s in SCOPES}, "errors": errors,
            "flags": flags, "flag_source": src or ("shell" if session is not None else None),
            "effective": effective, "session": session, "session_active": truthy(session),
            "restart_needed": effective and not truthy(session),
            "modes": modes, "mode": modes[mode_src] if mode_src else None, "mode_source": mode_src,
            "legacy_rule": rule.is_file(), "_files": files}


def write(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def set_flag(d: dict, value) -> None:
    env = d.setdefault("env", {})
    if value is None:
        env.pop(TEAM_ENV, None)
        if not env:
            d.pop("env", None)
    else:
        env[TEAM_ENV] = value


def move_legacy_rule(root: Path, dry: bool, log: list) -> None:
    rule = root / RULE
    if not rule.is_file():
        return
    try:
        head = rule.read_text(encoding="utf-8").lstrip().splitlines()[:1]
    except OSError:
        head = []
    if not head or not head[0].startswith("# Agent teams"):
        log.append(f"ℹ️ {RULE} : rule maison (titre inattendu) — laissée telle quelle")
        return
    if not dry:
        bak = root / RULE_BAK
        bak.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(rule), str(bak))
    log.append(f"🧹 {RULE} → {RULE_BAK} (rule héritée : ~1,9k tokens à chaque session ; "
               "les invariants sont maintenant injectés au spawn par le plugin)")


def toggle(root: Path, on: bool, scope: str, dry: bool) -> int:
    st = state(root)
    ps, files = paths(root), st["_files"]
    ti = SCOPES.index(scope)
    touched, log = {}, []

    def edit(s, value, why):
        if files[s] is None:
            raise ValueError(f"{ps[s]} : JSON illisible — corrige-le à la main, rien n'a été écrit")
        d = touched.setdefault(s, json.loads(json.dumps(files[s])))
        set_flag(d, value)
        shown = "retiré" if value is None else f'"{value}"'
        log.append(f"✏️ {ps[s]} : {TEAM_ENV} {shown} — {why}")

    try:
        # Un fichier plus prioritaire que la cible gagnerait contre elle : dans le projet, on l'aligne
        # (local ↔ projet) ; en scope user, le choix d'un projet est délibéré → signalé, jamais touché.
        for s in SCOPES[:ti]:
            v = st["flags"][s]
            if v is not None and truthy(v) != on:
                if scope == "user":
                    log.append(f"ℹ️ {ps[s]} : {TEAM_ENV} {json.dumps(v)} prime sur user — laissé "
                               f"(ce projet reste {'COUPÉ' if not truthy(v) else 'ACTIF'})")
                else:
                    edit(s, None, f"il primait sur `{scope}`")
        if on:
            if not truthy(st["flags"][scope]):
                edit(scope, "1", "agent teams actives")
            if st["mode"] is None:
                d = touched.setdefault(scope, json.loads(json.dumps(files[scope] or {})))
                d["teammateMode"] = "auto"
                log.append(f'✏️ {ps[scope]} : teammateMode "auto" (un pane par teammate si la session tourne DANS tmux)')
        else:
            lower = [st["flags"][s] for s in SCOPES[ti + 1:] if st["flags"][s] is not None]
            # Ailleurs ça reste allumé (settings moins prioritaire, ou export shell sans settings) → "0" explicite
            still_on = any(truthy(v) for v in lower) or (
                st["flag_source"] == "shell" and st["session_active"])
            if still_on and st["flags"][scope] != "0":
                edit(scope, "0", "le flag reste à 1 ailleurs (user ou shell) : 0 explicite ici")
            elif not still_on and st["flags"][scope] is not None:
                edit(scope, None, "agent teams coupées")
    except ValueError as e:
        print(f"❌ {e}")
        return 2

    if not dry:
        for s, d in touched.items():
            write(ps[s], d)
    move_legacy_rule(root, dry, log)

    print(("[dry-run] " if dry else "") + f"Agent teams → {'ON' if on else 'OFF'} (scope {scope})")
    for line in log or ["✅ rien à changer : déjà dans cet état"]:
        print(f"  {line}")
    if on:
        if st["session_active"]:
            print("  ✅ flag déjà actif dans cette session — aucune relance nécessaire")
        else:
            print("  🔁 RELANCE REQUISE : l'équipe se monte au démarrage. Quitte, puis `claude --continue` "
                  "(idéalement dans `tmux new -s <projet>` pour un pane par teammate).")
    else:
        print("  ✅ effet immédiat sur les prochains spawns (un subagent nommé reste un subagent) ; "
              "l'équipe montée au démarrage de cette session disparaît à la relance.")
        if st["mode"] is not None:
            print(f'  ℹ️ teammateMode "{st["mode"]}" laissé ({st["mode_source"]}) : sans effet flag coupé')
    return 0


def status(root: Path, as_json: bool) -> int:
    st = state(root)
    if as_json:
        print(json.dumps({k: v for k, v in st.items() if not k.startswith("_")}, ensure_ascii=False, indent=2))
        return 2 if st["errors"] else 0
    label = {"local": "local  ", "project": "projet ", "user": "user   "}
    print(f"Agent teams — {st['root']}")
    for s in SCOPES:
        v = st["flags"][s]
        print(f"  {label[s]} {st['paths'][s]} : " + ("—" if v is None else json.dumps(v)))
    src = st["flag_source"]
    print(f"  → {'ACTIVES' if st['effective'] else 'COUPÉES'}"
          + (f" (source : {src})" if src else " (flag défini nulle part)")
          + f" · session en cours : {st['session'] if st['session'] is not None else '—'}")
    if st["restart_needed"]:
        print("  🔁 activées dans les settings mais pas dans cette session : relance requise")
    if src == "user" and st["effective"]:
        print("  ⚠️ flag posé en USER : TOUTES tes sessions, tous projets, montent une équipe — "
              "`off --scope user` pour le retirer, puis `on` projet par projet")
    if st["mode"] is not None:
        print(f'  teammateMode "{st["mode"]}" ({st["mode_source"]})')
    if st["legacy_rule"]:
        print(f"  🧹 rule héritée {RULE} présente : ~1,9k tokens à chaque session, inutile avec ce plugin → "
              "`on` ou `off` la déplace dans .claude/.cache/")
    for e in st["errors"]:
        print(f"  ❌ {e}")
    return 2 if st["errors"] else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("status", "on", "off"))
    ap.add_argument("--scope", choices=SCOPES, default="project")
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    if a.mode == "status":
        return status(root, a.json)
    return toggle(root, a.mode == "on", a.scope, a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
