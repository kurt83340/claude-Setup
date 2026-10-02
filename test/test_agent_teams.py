#!/usr/bin/env python3
"""Régression du plugin agent-teams (1.2.0) : invariants injectés au spawn + interrupteur on/off/status.

Pourquoi : les invariants d'équipe ne sont plus une rule auto-chargée (~1,9k tokens à chaque session) ;
ils n'existent plus que par le hook `team-invariants.py`. Un hook muet = des teammates sans protocole,
sans aucun signal. Et `teams.py` réécrit des settings : il ne doit ni perdre une clé, ni écraser un
JSON invalide, ni toucher un projet quand on coupe en scope user.

Usage : python3 test/test_agent_teams.py     (exit 0 = tout vert, stdlib)
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "agent-teams"
HOOK = PLUGIN / "hooks" / "team-invariants.py"
TEAMS = PLUGIN / "skills" / "team" / "scripts" / "teams.py"
TEAM_ENV = "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"
HEAD = "## § Teammate — règles d'équipe (ajoutées par le plugin agent-teams)"
PASS = FAIL = 0
TMP = Path(tempfile.mkdtemp(prefix="agentteams-"))
CFG = TMP / "user-cfg"
CFG.mkdir()


def ok(label, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else: FAIL += 1; print(f"  ❌ {label}")


def env(**extra):
    e = {k: v for k, v in os.environ.items() if k not in (TEAM_ENV, "CLAUDE_PROJECT_DIR")}
    e["CLAUDE_CONFIG_DIR"] = str(CFG)
    e.update({k: str(v) for k, v in extra.items()})
    return e


def hook(payload, hook_path=HOOK, **extra):
    r = subprocess.run([sys.executable, str(hook_path)], input=json.dumps(payload), capture_output=True,
                       text=True, env=env(**extra))
    out = json.loads(r.stdout).get("hookSpecificOutput", {}) if r.stdout.strip() else {}
    return r, out


def spawn(sid, **ti):
    base = {"description": "d", "prompt": "Fais la tâche T1.", "subagent_type": "worker", "name": "back"}
    base.update(ti)
    return {"hook_event_name": "PreToolUse", "session_id": sid, "tool_name": "Agent", "tool_input": base}


def teams(*args, **extra):
    return subprocess.run([sys.executable, str(TEAMS), *args], capture_output=True, text=True, env=env(**extra))


try:
    # ── 1. hooks.json : le hook est câblé sur le spawn ────────────────────────────────────────
    print("== hooks.json ==")
    hj = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    pre = [m for m in hj.get("PreToolUse", []) if "Agent" in m.get("matcher", "").split("|")]
    ok("PreToolUse(Agent) → team-invariants.py",
       any("team-invariants.py" in h["command"] for m in pre for h in m["hooks"]))
    ok("SessionStart(compact|clear) → team-invariants.py (ré-arme § Lead)",
       any("team-invariants.py" in h["command"] and {"compact", "clear"} <= set(m.get("matcher", "").split("|"))
           for m in hj.get("SessionStart", []) for h in m["hooks"]))
    pj = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    ok("plugin.json en 1.2.0+", tuple(int(x) for x in pj["version"].split(".")) >= (1, 2, 0))
    ok("plus de rule à copier dans le plugin (agent-teams-rule.md retiré)",
       not (PLUGIN / "skills" / "team" / "agent-teams-rule.md").exists())

    # ── 2. hook : injection au spawn d'un teammate ────────────────────────────────────────────
    print("\n== team-invariants.py — spawn ==")
    sid = f"t-{os.getpid()}"
    marker = Path(tempfile.gettempdir()) / f"claude-agent-teams-lead-{sid}.flag"
    marker.unlink(missing_ok=True)
    r, out = hook(spawn(sid), **{TEAM_ENV: "0"})
    ok("flag à 0 → rien (le spawn reste un subagent)", r.returncode == 0 and r.stdout.strip() == "")
    r, out = hook(spawn(sid))
    ok("flag absent → rien", r.stdout.strip() == "")
    r, out = hook(spawn(sid), **{TEAM_ENV: "1"})
    ui = out.get("updatedInput", {})
    ok("flag à 1 + name → § Teammate ajouté à la FIN du prompt",
       ui.get("prompt", "").startswith("Fais la tâche T1.") and HEAD in ui.get("prompt", "")
       and "SendMessage" in ui["prompt"].split(HEAD, 1)[1])
    ok("les autres champs du spawn sont conservés tels quels",
       {k: v for k, v in ui.items() if k != "prompt"} == {"description": "d", "subagent_type": "worker", "name": "back"})
    ok("§ Lead injecté au lead (additionalContext), sans les règles teammate",
       "§ Lead" in out.get("additionalContext", "") and "worktree" in out["additionalContext"]
       and HEAD not in out["additionalContext"])
    ok("pas de permissionDecision (le flux de permissions normal continue)", "permissionDecision" not in out)
    r, out2 = hook(spawn(sid, name="front"), **{TEAM_ENV: "true"})
    ok("2e spawn de la session : § Teammate oui, § Lead non (1×/session)",
       HEAD in out2.get("updatedInput", {}).get("prompt", "") and "additionalContext" not in out2)
    r, out3 = hook(spawn(sid, prompt=ui["prompt"]), **{TEAM_ENV: "1"})
    ok("prompt qui contient déjà les règles (respawn recopié) → pas de doublon", "updatedInput" not in out3)
    for label, payload in (("sans name (subagent)", spawn(sid, name="")),
                           ("fork", spawn(sid, subagent_type="fork")),
                           ("isolation", spawn(sid, isolation="worktree")),
                           ("appel DANS un subagent/teammate (agent_id)", {**spawn(sid), "agent_id": "a1"})):
        r, o = hook(payload, **{TEAM_ENV: "1"})
        ok(f"{label} → rien", r.returncode == 0 and r.stdout.strip() == "")
    r, o = hook({"hook_event_name": "PreToolUse", "session_id": sid, "tool_name": "Agent", "tool_input": "x"},
                **{TEAM_ENV: "1"})
    ok("tool_input inattendu → exit 0 silencieux", r.returncode == 0 and r.stdout.strip() == "")
    r = subprocess.run([sys.executable, str(HOOK)], input="pas du json", capture_output=True, text=True, env=env())
    ok("stdin illisible → exit 0", r.returncode == 0)

    # ── 3. ré-armement après compaction / clear ───────────────────────────────────────────────
    print("\n== team-invariants.py — SessionStart ==")
    hook({"hook_event_name": "SessionStart", "session_id": sid, "source": "compact"})
    ok("SessionStart compact → marqueur § Lead effacé", not marker.exists())
    r, out4 = hook(spawn(sid, name="tester"), **{TEAM_ENV: "1"})
    ok("spawn suivant : § Lead ré-injecté", "§ Lead" in out4.get("additionalContext", ""))
    marker.unlink(missing_ok=True)

    # ── 4. plugin abîmé : jamais en silence ───────────────────────────────────────────────────
    print("\n== team-invariants.py — invariants illisibles ==")
    broken = TMP / "broken-plugin"
    (broken / "hooks").mkdir(parents=True)
    (broken / "skills" / "team").mkdir(parents=True)
    shutil.copy2(HOOK, broken / "hooks" / "team-invariants.py")
    r, o = hook(spawn(sid + "-b"), hook_path=broken / "hooks" / "team-invariants.py", **{TEAM_ENV: "1"})
    ok("invariants.md absent → avertissement au lead (teammate SANS règles), pas d'updatedInput",
       "invariants illisibles" in o.get("additionalContext", "") and "updatedInput" not in o)
    (Path(tempfile.gettempdir()) / f"claude-agent-teams-lead-{sid}-b.flag").unlink(missing_ok=True)

    # ── 5. teams.py : interrupteur ────────────────────────────────────────────────────────────
    print("\n== teams.py — on / off / status ==")
    proj = TMP / "proj"
    (proj / ".claude" / "rules").mkdir(parents=True)
    sp, sl, su = proj / ".claude/settings.json", proj / ".claude/settings.local.json", CFG / "settings.json"
    sp.write_text(json.dumps({"permissions": {"allow": ["Read"]},
                              "enabledPlugins": {"agent-teams@claude-setup": True}}, indent=2) + "\n")
    rule = proj / ".claude/rules/agent-teams.md"
    rule.write_text("# Agent teams — invariants d'équipe (auto-chargés)\nancienne rule\n")
    su.write_text(json.dumps({"env": {TEAM_ENV: "1"}, "teammateMode": "tmux"}))
    r = teams("status", "--root", str(proj), "--json", **{TEAM_ENV: "1"})
    st = json.loads(r.stdout)
    ok("status : flag vu en user, effectif, rule héritée signalée",
       st["flag_source"] == "user" and st["effective"] and st["legacy_rule"] and st["mode"] == "tmux")
    r = teams("status", "--root", str(proj), **{TEAM_ENV: "1"})
    ok("status texte : avertit que le flag user vaut pour TOUTES les sessions", "TOUTES tes sessions" in r.stdout)
    before = sp.read_text()
    r = teams("off", "--root", str(proj), "--dry-run", **{TEAM_ENV: "1"})
    ok("off --dry-run : plan affiché, rien écrit ni déplacé", r.returncode == 0 and "[dry-run]" in r.stdout
       and sp.read_text() == before and rule.exists())
    r = teams("off", "--root", str(proj), **{TEAM_ENV: "1"})
    spj = json.loads(sp.read_text())
    ok("off projet alors que user=1 → \"0\" explicite dans le projet, autres clés intactes",
       spj["env"][TEAM_ENV] == "0" and spj["permissions"] == {"allow": ["Read"]}
       and spj["enabledPlugins"] == {"agent-teams@claude-setup": True})
    ok("off → rule héritée déplacée dans .claude/.cache/ (plus auto-chargée)",
       not rule.exists() and (proj / ".claude/.cache/agent-teams.md.obsolete").is_file())
    ok("off → user settings non touchés", json.loads(su.read_text()) == {"env": {TEAM_ENV: "1"}, "teammateMode": "tmux"})
    r = teams("on", "--root", str(proj))
    spj = json.loads(sp.read_text())
    ok("on → flag \"1\", relance annoncée, teammateMode non imposé (déjà défini en user)",
       spj["env"][TEAM_ENV] == "1" and "teammateMode" not in spj and "RELANCE REQUISE" in r.stdout)
    r = teams("off", "--scope", "user", "--root", str(proj))
    ok("off --scope user : flag retiré du user, le choix du projet (1) laissé et signalé",
       TEAM_ENV not in json.loads(su.read_text()).get("env", {})
       and json.loads(sp.read_text())["env"][TEAM_ENV] == "1" and "prime sur user" in r.stdout)
    su.write_text("{}")
    r = teams("off", "--root", str(proj))
    ok("off projet, plus rien ailleurs → clé retirée (et env vide supprimé)", "env" not in json.loads(sp.read_text()))
    r = teams("on", "--root", str(proj))
    ok("on sans teammateMode nulle part → \"auto\" posé", json.loads(sp.read_text()).get("teammateMode") == "auto")
    sl.write_text(json.dumps({"env": {TEAM_ENV: "1"}}))
    r = teams("off", "--root", str(proj))
    ok("off projet : le local à 1 (qui primerait) est aligné aussi",
       TEAM_ENV not in json.loads(sl.read_text()).get("env", {}) and TEAM_ENV not in json.loads(sp.read_text()).get("env", {}))
    sl.write_text("{ pas du json")
    r = teams("on", "--scope", "local", "--root", str(proj))
    ok("settings en JSON invalide → code 2, fichier jamais réécrit",
       r.returncode == 2 and sl.read_text() == "{ pas du json")
    r = teams("status", "--root", str(proj), "--json")
    ok("status : JSON invalide signalé (code 2)", r.returncode == 2 and json.loads(r.stdout)["errors"])
    sl.unlink()
    custom = proj / ".claude/rules/agent-teams.md"
    custom.write_text("# Ma rule maison sur les équipes\n")
    r = teams("on", "--root", str(proj))
    ok("rule maison (titre inattendu) → laissée en place", custom.exists() and "rule maison" in r.stdout)
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print(f"\n{'🎉 AGENT-TEAMS OK' if FAIL == 0 else '💥 ÉCHECS'} — {PASS} pass, {FAIL} fail")
sys.exit(0 if FAIL == 0 else 1)
