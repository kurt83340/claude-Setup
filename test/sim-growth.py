#!/usr/bin/env python3
"""Simulation de croissance — des mois de vie d'un projet généré, session par session.

Pourquoi : les suites unitaires testent chaque hook isolément. Les bugs de budget et de filet
(v1.4 : fausse alerte « session fermée sans /handoff » à CHAQUE démarrage ; projet d'un mois à
144k tokens au 1er tour) n'apparaissent qu'avec l'ORDRE réel des événements et la croissance
réelle de la doc. Ici : déterministe (random.Random seedé), sans Claude, stdlib uniquement.

Une session simulée = ce que ferait Claude Code, avec les hooks DU PROJET (lus dans son
.claude/settings.json, matchers compris, lancés via `sh -c` avec CLAUDE_PROJECT_DIR) :
  SessionStart(startup) → tours de travail : Edit/Write (PreToolUse + PostToolUse), commits,
  skills qui écrivent la doc, Stop à chaque fin de tour → parfois PreCompact + SessionStart(compact)
  → /handoff (≈ 85 %) → transcript JSONL réaliste terminé par /exit → SessionEnd.
Skills émulés en Python, au format de LEUR version et seulement s'ils existent dans le projet :
/handoff (< 1.4 : section datée appendée au journal DANS HANDOFF.md ; ≥ 1.4 : réécriture au format
strict + 1 ligne dans HANDOFF-journal.md), /spec, /feature-done, /adr, /lecon, /idee, /codemap
(gotchas : < 1.4 dans code-map.md, ≥ 1.4 dans code-map-gotchas.md ; règles de couplage).
Le temps passe en reculant les mtimes du projet (≈ 1 jour entre deux sessions) : rappel Stop
> 24 h, purge du cache > 7 j et filet (mtime HANDOFF vs début de session) jouent comme en vrai.

Scénarios :
  A  progression : même croissance seedée sur un projet v1.3.3 et un projet 1.5.0 (python-app)
  B  upgrade à mi-vie : v1.3.3 grossit N/2 sessions + personnalisations → upgrade.py --to WORKTREE
     → N/2 sessions aux nouvelles conventions (rien de perdu, budget revenu sous 8k)
  C  profils : croissance courte à 1.5.0 sur les 6 profils

Usage : python3 test/sim-growth.py [--sessions N] [--seed S] [--quick] [--report PATH] [--keep]
                                    [--scenarios A,B,C] [--jobs J]
  --quick  mode CI : A 20 sessions, B 20, C 8 sessions × 3 profils (< 60 s)
  exit 0 = tout vert · 1 = au moins un contrôle en échec
Prérequis : les tags vX.Y.Z du dépôt (en CI : checkout avec fetch-depth: 0).
"""
import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPGRADE = ROOT / ".claude" / "skills" / "upgrade-template" / "scripts" / "upgrade.py"
BUDGET = ROOT / ".claude" / "skills" / "doc-health" / "scripts" / "context-budget.py"
EXCLUDE_TOP = {"EXAMPLES", "test", ".github", ".git", "plugins", ".claude-plugin"}
VARS = {
    "PROJECT_NAME": "Caisse Rapide", "CLIENT_NAME": "Boulangerie Martin",
    "PROJECT_FOLDER": "caisse-rapide", "NOM_DECIDEUR": "Sophie Martin",
    "EMAIL_DECIDEUR": "sophie@boulangerie-martin.fr", "TON_NOM": "Julien Leroy",
    "TON_EMAIL": "julien@example.org", "COMMANDE_INSTALL": "pip install -e .[dev]",
    "COMMANDE_RUN": "python -m caisse", "COMMANDE_TESTS": "pytest -q",
}
GIT = ["git", "-c", "user.email=sim@example.org", "-c", "user.name=Sim", "-c", "commit.gpgsign=false"]
PROFILES = ("script-jetable", "automation-n8n", "python-app", "web-app", "bdd-migration", "other")
QUICK_PROFILES = ("script-jetable", "web-app", "automation-n8n")
OLD_TAG = "v1.3.3"

# ── Invariants vérifiés (cibles écrites dans le template lui-même) ───────────────────────────
HANDOFF_MAX_LINES = 40          # /handoff Étape 3 : « ≤ 40 lignes » (repli si la cible n'est pas lisible, cf. handoff_target)
BUDGET_MAX_TOK = 12000          # surface auto-chargée d'un projet vivant (CI : template vierge < 12k)
BUDGET_DRIFT_TOK = 3000         # croissance tolérée de la 5e session à la dernière
BUDGET_AFTER_UPGRADE_TOK = 8000
PRETOOL_MAX_CHARS = 3000        # additionalContext PreToolUse (cap du hook : 2 500 + en-tête)
STOP_SIZE_BYTES = 12000         # garde-fou taille du hook Stop (CLAUDE_HANDOFF_MAX_BYTES)
CACHE_DAYS = 7                  # purge du cache par-session au démarrage
NON_CODE_EXT = (".md", ".mdx", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
                ".lock", ".csv", ".log", ".env", ".example")

# ── Rythme de la croissance (≈ « tous les k sessions », avec gigue) ─────────────────────────
CADENCE = {"spec": 5, "feature_done": 8, "adr": 10, "lecon": 4, "idee": 6, "gotcha": 7,
           "coupling": 15, "precompact": 20}
HANDOFF_RATE = 0.85
SIM_EPOCH = datetime(2026, 6, 1, 9, 0)   # calendrier simulé (contenu des docs déterministe)

# Skill → docs qu'il a le droit d'écrire (contrôle « rien d'écrit par un skill absent »)
SKILL_DOCS = {
    "handoff": [r"HANDOFF(-journal)?\.md$"],
    "spec": [r"^specs/", r"^ROADMAP\.md$"],
    "feature-done": [r"^ROADMAP\.md$", r"^CHANGELOG\.md$", r"^specs/[^/]+/(spec|tasks)\.md$", r"^HANDOFF\.md$"],
    "adr": [r"^adr/", r"^CHANGELOG\.md$"],
    "lecon": [r"^lecons\.md$"],
    "idee": [r"^idees/"],
    "codemap": [r"^code-map(-gotchas)?\.md$"],
}
ACTION_SKILL = {"spec": "spec", "feature_done": "feature-done", "adr": "adr", "lecon": "lecon",
                "idee": "idee", "gotcha": "codemap", "coupling": "codemap", "note": "handoff"}

JOURNAL_RE = re.compile(r"— Session (\d+) ·")
GOTCHA_RE = re.compile(r"\(piège G(\d+)\)")
COUPLING_RE = re.compile(r"\(règle C(\d+)\)")
LECON_RE = re.compile(r"^## \d{4}-\d{2}-\d{2} — .*\[L(\d+)\]", re.M)
STACK_RE = re.compile(r"Point d'étape \(S(\d+)\)")
NOTE_MARK = "Notes client (ajoutées à la main)"

# ── Banques de contenu (FR, réalistes, avec marqueurs uniques pour compter sans ambiguïté) ──
FEATURES = [
    ("Pagination cursor", "pagination-cursor"), ("Export PDF des tickets", "export-pdf-tickets"),
    ("Remises fidélité", "remises-fidelite"), ("Synchro du stock", "synchro-stock"),
    ("Clôture de caisse", "cloture-caisse"), ("Paiement sans contact", "paiement-sans-contact"),
    ("Tableau de bord des ventes", "tableau-bord-ventes"), ("Gestion des avoirs", "gestion-avoirs"),
    ("Import du catalogue", "import-catalogue"), ("Alertes de rupture", "alertes-rupture"),
    ("Multi-boutiques", "multi-boutiques"), ("Journal d'audit", "journal-audit"),
    ("TVA multi-taux", "tva-multi-taux"), ("Mode hors-ligne", "mode-hors-ligne"),
    ("Relances clients", "relances-clients"), ("Étiquettes prix", "etiquettes-prix"),
]
PACKAGES = ["caisse", "ventes", "stock", "paiement", "rapports", "sync", "clients", "fiscal"]
MODULES = ["api", "service", "modeles", "calcul", "export", "client", "validation", "cache", "planif", "format"]
ASKS = [
    "ajoute {feat} — commence par `{file}` (ticket #{t})",
    "corrige le calcul de TVA quand une remise s'applique, le test de `{file}` est rouge (ticket #{t})",
    "refacto `{file}` : sépare le calcul de la mise en forme, sans changer le comportement (#{t})",
    "écris les tests manquants pour `{file}` avant qu'on touche à {feat} (#{t})",
    "pourquoi `{file}` renvoie un total négatif sur les avoirs ? (ticket #{t})",
    "branche `{file}` sur l'API du fournisseur et garde le curseur opaque côté client (#{t})",
    "le client veut arrondir au centime supérieur, adapte `{file}` (ticket #{t})",
    "ajoute un log structuré dans `{file}` pour l'incident d'hier soir (#{t})",
    "on reprend {feat} là où on s'était arrêté, regarde `{file}` (#{t})",
    "la clôture de caisse plante quand le tiroir est vide, regarde `{file}` (ticket #{t})",
    "prépare la démo de vendredi pour Sophie : {feat}, surtout `{file}` (#{t})",
]
QUESTIONS = [
    "rappelle-moi pourquoi on a choisi SQLite plutôt que Postgres ? (#{t})",
    "où en est {feat} ? résume-moi l'état sans rien modifier (#{t})",
    "explique-moi le flux de synchro du stock, je dois le présenter (#{t})",
    "quels tests couvrent la clôture de caisse ? juste la liste (#{t})",
]
GOALS = ["avancer {feat}", "corriger les régressions de la clôture de caisse", "stabiliser les tests de {feat}",
         "brancher l'API du fournisseur", "préparer la démo client", "réduire la dette du module TVA",
         "terminer {feat} et relire le diff", "enquêter sur l'incident de synchro de la nuit"]
STATUS = ["✅ {tests} : {n} passed", "⏳ {tests} : {n} passed, 2 failed (clôture)", "✅ lint : propre",
          "⏳ typage : 3 erreurs restantes dans le module TVA", "✅ démo validée par Sophie",
          "⏳ relecture du diff à faire"]
FAILS = ["passer par l'ORM pour l'export → 10× trop lent sur 50k lignes",
         "arrondir à chaque ligne de ticket → écarts d'un centime sur le total",
         "mocker l'API fournisseur au niveau HTTP → tests fragiles, on mocke le client",
         "cache global en mémoire → incohérent entre deux caisses",
         "réessayer sans backoff → bannis 10 min par le fournisseur"]
BLOCKERS = ["rien", "accès sandbox du fournisseur en attente (Sophie relancée)",
            "arbitrage client sur l'arrondi des remises", "clé API de prod pas encore transmise"]
NEXTS = ["**T{a}.{b}** : brancher {feat} sur le module de caisse", "**T{a}.{b}** : tests d'intégration de {feat}",
         "**T{a}.{b}** : relire les cas limites (avoirs, remises cumulées)", "**T{a}.{b}** : démo à Sophie puis /feature-done",
         "**T{a}.{b}** : nettoyer les TODO laissés dans le module"]
FAITS = ["client HTTP avec retry et backoff", "tests de la clôture de caisse", "export CSV séparé par des points-virgules",
         "calcul des remises cumulées", "pagination par curseur", "refacto du module TVA", "logs structurés",
         "écran de synthèse des ventes", "gestion des avoirs négatifs"]
DECISIONS = ["montants en centimes partout", "curseur opaque côté client", "retry 3× avec backoff exponentiel",
             "SQLite tant qu'il n'y a qu'une caisse", "arrondi une seule fois, sur le total", "aucune décision structurante"]
RESTES = ["cas des avoirs partiels", "tests d'intégration", "relecture par Sophie", "documentation du flux",
          "gestion des erreurs réseau", "rien de bloquant"]
GOTCHA_TEXTS = [
    "l'API du fournisseur renvoie 200 même en erreur — vérifier le champ status du body",
    "les montants sont en centimes (int), jamais en float — arrondi bancaire à la fin seulement",
    "le cache est invalidé par toute écriture, même partielle — ne pas écrire dans une boucle",
    "l'ordre des remises change le total : pourcentage d'abord, montant fixe ensuite",
    "le serveur tourne en UTC, les tickets sont en Europe/Paris — convertir à l'affichage seulement",
    "le fournisseur tronque les libellés à 40 caractères sans prévenir",
    "le webhook de paiement peut arriver AVANT la réponse HTTP — idempotence obligatoire",
    "la TVA d'un avoir est négative — ne jamais prendre la valeur absolue",
    "le verrou fichier n'est pas libéré si le process est tué — le purger au démarrage",
    "l'export attend un séparateur point-virgule (Excel FR), pas une virgule",
    "la pagination du fournisseur saute un élément si on trie par date — trier par identifiant",
    "le tiroir-caisse renvoie une trame vide à la première ouverture — réessayer une fois",
]
GLOBAL_GOTCHA = "les montants sont des centimes int dans TOUT le code — jamais de float, même en test"
LECONS = [
    ("Rate limit du fournisseur", "L'API coupe à 60 req/min sans en-tête Retry-After.", "Backoff exponentiel côté client.", "promouvoir en rule si ça revient"),
    ("Arrondi des remises", "Arrondir par ligne crée des écarts d'un centime sur le total.", "Arrondir une seule fois, sur le total.", "memory only"),
    ("Tests qui dépendent de l'heure", "Deux tests cassent entre 23 h et minuit (UTC vs Paris).", "Horloge injectée dans les services.", "promouvoir en rule"),
    ("Libellés tronqués", "Le fournisseur coupe à 40 caractères, les recherches ratent.", "Tronquer nous-mêmes et garder l'original.", "memory only"),
    ("Webhooks en double", "Le paiement arrive parfois deux fois.", "Clé d'idempotence par transaction.", "promouvoir en ADR"),
    ("Export Excel illisible", "Les accents cassent sans BOM UTF-8.", "BOM + point-virgule.", "memory only"),
]
ADRS = [("mvp", "Stack BDD : SQLite plutôt que Postgres", "sqlite-plutot-que-postgres"),
        ("mvp", "Montants en centimes entiers", "montants-centimes"),
        ("infra", "Hébergement sur un VPS unique", "hebergement-vps"),
        ("operations", "Sauvegardes quotidiennes chiffrées", "sauvegardes-chiffrees"),
        ("feature-001", "Pagination par curseur opaque", "pagination-curseur"),
        ("cadrage", "Aucune donnée bancaire stockée", "pas-de-donnees-bancaires"),
        ("infra", "Secrets dans le coffre de l'hébergeur", "secrets-coffre"),
        ("mvp", "Synchronisation par webhooks idempotents", "webhooks-idempotents")]
IDEES = [("Synchro inverse du stock", "synchro-inverse-stock"), ("Alertes Slack de rupture", "alertes-slack-rupture"),
         ("Cache des prix fournisseur", "cache-prix-fournisseur"), ("Mode sombre de la caisse", "mode-sombre"),
         ("Export comptable FEC", "export-fec"), ("Fidélité par QR code", "fidelite-qr-code"),
         ("Prévision des ventes", "prevision-ventes")]
COUPLING_REASONS = ["la couche métier ne connaît pas l'infra", "le calcul fiscal doit rester testable sans réseau",
                    "les exports ne pilotent jamais la caisse", "seul l'orchestrateur connaît les connecteurs"]
TRIGGERS = ["token OAuth du fournisseur", "deploy en production vendredi", "api_key lue depuis l'environnement"]

PASS = FAIL = 0
CHECKS = []          # (section, ok, libellé) — repris dans le rapport
SECTION = ""


# ── Utilitaires ──────────────────────────────────────────────────────────────────────────────

def ok(label, cond):
    global PASS, FAIL
    cond = bool(cond)
    if cond:
        PASS += 1
    else:
        FAIL += 1
    CHECKS.append((SECTION, cond, label))
    print(f"  {'✅' if cond else '❌'} {label}")


def info(text):
    print(f"  · {text}")


def section(title):
    global SECTION
    SECTION = title
    print(f"\n== {title} ==")


def kt(tok):
    return f"{tok / 1000:.1f}k"


def sh(args, cwd=None, env=None, check=True, data=None):
    r = subprocess.run([str(a) for a in args], cwd=cwd, env=env, input=data, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, args))}\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    return r


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def det_uuid(s: str) -> str:
    return str(uuid.UUID(hashlib.md5(s.encode()).hexdigest()))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def base_env(home: Path) -> dict:
    """Environnement isolé et reproductible : HOME vide (ni ~/.claude/settings.json de l'utilisateur
    lu par upgrade.py, ni ~/.gitconfig), aucune variable CLAUDE_* / GIT_* héritée."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("CLAUDE_", "GIT_")) and k not in ("XDG_CONFIG_HOME", "PYTHONPATH")}
    env.update(HOME=str(home), PYTHONIOENCODING="utf-8")
    return env


def is_code(rel: str) -> bool:
    return not rel.startswith(".claude/") and not rel.lower().endswith(NON_CODE_EXT)


def file_kind(rel: str) -> str:
    """code (gotchas ciblés + Globaux) · config (.json/.md… du projet : au plus les gotchas qui le
    ciblent, jamais les Globaux) · methode (.claude/ : rien)."""
    return "methode" if rel.startswith(".claude/") else ("code" if is_code(rel) else "config")


def targets(target, rel: str) -> bool:
    if target is None:          # gotcha « Globaux »
        return True
    return rel.startswith(target) if target.endswith("/") else rel == target


def split_h2(text: str):
    """[(heading | None, corps)] découpé sur les `## ` hors blocs fencés."""
    out, head, cur, fence = [], None, [], False
    for line in text.split("\n"):
        if re.match(r"^\s{0,3}(```|~~~)", line):
            fence = not fence
        if not fence and line.startswith("## "):
            out.append((head, "\n".join(cur)))
            head, cur = line, []
        else:
            cur.append(line)
    out.append((head, "\n".join(cur)))
    return out


def section_bullets(text: str, heading_prefix: str):
    """Puces (`- …`) qui suivent un heading donné, jusqu'à la 1re ligne vide après elles."""
    lines = text.split("\n")
    try:
        i = next(k for k, l in enumerate(lines) if l.startswith(heading_prefix))
    except StopIteration:
        return None
    out = []
    for l in lines[i + 1:]:
        if l.startswith("- "):
            out.append(l[2:])
        elif out and not l.strip():
            break
        elif l.startswith("#"):
            break
        elif l.strip() == "-":
            out.append("")
    return out


def snapshot_ok(text: str, humans: list) -> bool:
    """Le snapshot liste exactement les 3 derniers messages HUMAINS (tronqués à 300 chars)."""
    got = section_bullets(text, "### Derniers messages user")
    exp = [h[:300] for h in humans[-3:]]
    if not exp:
        return got is not None and "_(aucun)_" in text
    return got == exp


# ── Génération des projets (comme test_upgrade.py : init réelle de chaque version) ──────────

def materialize(ref: str, dest: Path):
    dest.mkdir(parents=True)
    if ref == "WORKTREE":
        for child in ROOT.iterdir():
            if child.name in EXCLUDE_TOP:
                continue
            if child.is_dir():
                shutil.copytree(child, dest / child.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".cache"))
            else:
                shutil.copy2(child, dest / child.name)
        return
    tar = subprocess.run(["git", "-C", str(ROOT), "archive", "--format=tar", ref], capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(dest)], input=tar.stdout, check=True)
    for d in EXCLUDE_TOP:
        p = dest / d
        shutil.rmtree(p, ignore_errors=True) if p.is_dir() else (p.unlink() if p.exists() else None)


def init_project(ref: str, profile: str, dest: Path, env: dict) -> Path:
    """Init réelle d'un projet à la version `ref` (render.py + cleanup-for-type.py de CETTE version)."""
    materialize(ref, dest)
    sh(["git", "init", "-q"], cwd=dest, env=env)
    sh(GIT + ["add", "-A"], cwd=dest, env=env)
    sh(GIT + ["commit", "-qm", "snapshot pre-init"], cwd=dest, env=env)
    vf = dest.parent / f"vars-{dest.name}.json"
    vf.write_text(json.dumps(VARS), encoding="utf-8")
    scripts = dest / ".claude/skills/init-from-template/scripts"
    sh([sys.executable, scripts / "render.py", "--vars", vf, "--root", dest], env=env)
    sh([sys.executable, scripts / "cleanup-for-type.py", "--type", profile, "--root", dest], env=env)
    sh(GIT + ["add", "-A"], cwd=dest, env=env)
    sh(GIT + ["commit", "-qm", f"init {ref} {profile}"], cwd=dest, env=env)
    return dest


# ── Plan de croissance (pur : ne dépend que de la seed → croissance IDENTIQUE entre versions) ─

def layout_of(profile: str) -> str:
    return {"web-app": "web", "automation-n8n": "n8n", "other": "go", "bdd-migration": "bdd"}.get(profile, "py")


def new_files(rng, layout, files):
    pkg, mod = rng.choice(PACKAGES), rng.choice(MODULES)
    if layout == "web":
        paths = [f"app/{pkg}/{mod}.ts", f"app/{pkg}/{mod}.test.ts"]
    elif layout == "go":
        paths = [f"internal/{pkg}/{mod}.go", f"internal/{pkg}/{mod}_test.go"]
    elif layout == "n8n" and rng.random() < 0.5:
        paths = [f"workflows/{pkg}-{mod}.json"]
    elif layout == "bdd" and rng.random() < 0.3:
        paths = [f"migrations/versions/{len(files) + 1:03d}_{pkg}_{mod}.py"]
    else:
        paths = [f"src/{pkg}/{mod}.py", f"tests/{pkg}/test_{mod}.py"]
    k = 2
    while any(p in files for p in paths):   # nom déjà pris → suffixe
        paths = [re.sub(r"(\.test\.ts|_test\.go|\.py|\.ts|\.go|\.json)$", rf"_{k}\1", p, count=1) for p in paths]
        k += 1
    return paths if rng.random() < 0.7 else paths[:1]


def dir_of(path: str) -> str:
    return path.rsplit("/", 1)[0] + "/"


def build_plan(key: str, n: int, layout: str) -> list:
    rng = random.Random(key)
    files, gotcha_targets = [], []
    nxt = {k: rng.randint(2, max(3, c)) for k, c in CADENCE.items()}
    nxt["gotcha"] = rng.randint(2, 4)        # 1er gotcha tôt (cf. act_gotcha : mal rangé sur < 1.4)
    nxt["precompact"] = rng.randint(4, 8)    # au moins une compaction même en --quick
    global_at = n // 2 if n >= 16 else None  # 1 gotcha transversal (sans chemin) à mi-parcours : « Globaux »
    #                                          en ≥ 1.4 (remplace le gabarit) ; en B, dernière session < 1.4
    cnt = dict(gotcha=0, coupling=0, lecon=0, spec=0, adr=0, idee=0)
    feat = "la clôture de caisse"
    t, ticket, plan = SIM_EPOCH, 100, []
    tests_cmd = {"web": "npm test", "go": "go test ./..."}.get(layout, "pytest -q")
    for i in range(1, n + 1):
        r = rng.random()
        gap = 0 if i == 1 else (5 if r < 0.15 else 24 if r < 0.85 else 72 if r < 0.95 else 120)
        t += timedelta(hours=gap)
        question = i > 2 and bool(files) and rng.random() < 0.1
        handoff = rng.random() < HANDOFF_RATE
        nwork = rng.randint(1, 3) if handoff else rng.randint(2, 3)     # → 2 à 4 Stop par session
        # ── actions de doc (skills) ──
        actions = []
        for kind in ("spec", "feature_done", "adr", "lecon", "idee", "gotcha", "coupling"):
            if i < nxt[kind]:
                continue
            a = {"kind": kind}
            if kind == "spec":
                cnt["spec"] += 1
                titre, kebab = FEATURES[(cnt["spec"] - 1) % len(FEATURES)]
                lot = (cnt["spec"] - 1) // len(FEATURES)
                if lot:
                    titre, kebab = f"{titre} (lot {lot + 1})", f"{kebab}-lot-{lot + 1}"
                a.update(titre=titre, kebab=kebab, start=rng.random() < 0.5)
                feat = titre.lower()
            elif kind == "adr":
                cnt["adr"] += 1
                scope, titre, kebab = ADRS[(cnt["adr"] - 1) % len(ADRS)]
                a.update(scope=scope, titre=titre, kebab=kebab if cnt["adr"] <= len(ADRS) else f"{kebab}-{cnt['adr']}")
            elif kind == "lecon":
                cnt["lecon"] += 1
                a.update(n=cnt["lecon"], lecon=LECONS[(cnt["lecon"] - 1) % len(LECONS)],
                         scope=rng.choice(["mvp", "infra", "operations", "feature-001"]))
            elif kind == "idee":
                cnt["idee"] += 1
                titre, kebab = IDEES[(cnt["idee"] - 1) % len(IDEES)]
                a.update(titre=titre, kebab=kebab, effort=rng.choice(["Petit (< 1 jour)", "Moyen (~1 sem)", "Gros (> 1 sem)"]))
            elif kind == "gotcha":
                if not files:
                    continue
                cnt["gotcha"] += 1
                target = rng.choice(files[-6:]) if rng.random() < 0.7 else rng.choice(files)
                if rng.random() < 0.3:
                    target = dir_of(target)
                a.update(n=cnt["gotcha"], target=target, text=GOTCHA_TEXTS[(cnt["gotcha"] - 1) % len(GOTCHA_TEXTS)],
                         misplaced=cnt["gotcha"] == 1 or rng.random() < 0.2)
                gotcha_targets.append(target)
            elif kind == "coupling":
                dirs = sorted({dir_of(f) for f in files if not f.endswith(".json")})
                if len(dirs) < 2:
                    continue
                cnt["coupling"] += 1
                da, db = rng.sample(dirs, 2)
                a.update(n=cnt["coupling"], a=da, b=db, raison=rng.choice(COUPLING_REASONS))
            actions.append(a)
            nxt[kind] = i + max(2, round(CADENCE[kind] * rng.uniform(0.6, 1.4)))
        if global_at == i:
            cnt["gotcha"] += 1
            actions.append({"kind": "gotcha", "n": cnt["gotcha"], "target": None, "text": GLOBAL_GOTCHA, "misplaced": False})
        if i == min(3, n):   # l'utilisateur ajoute à la main une section non datée dans HANDOFF.md
            actions.append({"kind": "note"})
        # ── édits de code ──
        edits = []
        if not question:
            if not files or rng.random() < 0.35:
                for p in new_files(rng, layout, files):
                    edits.append(p)
                    files.append(p)
            hot = [f for f in files if any(targets(g, f) for g in gotcha_targets)]
            for _ in range(rng.randint(1, 4)):
                pool = hot if hot and rng.random() < 0.35 else (files[-6:] if rng.random() < 0.7 else files)
                edits.append(rng.choice(pool))
            if rng.random() < 0.4:
                edits.append(rng.choice(edits))            # même fichier deux fois dans la session
        edits = [{"path": p, "trigger": rng.choice(TRIGGERS) if rng.random() < 0.12 else None} for p in edits]
        precompact = bool(edits) and i >= nxt["precompact"]
        if precompact:
            nxt["precompact"] = i + max(5, round(CADENCE["precompact"] * rng.uniform(0.7, 1.3)))
            if not cnt.get("pc"):   # la 1re session compactée se ferme SANS /handoff (session longue, oubli
                handoff = False     # typique) → le filet suivant porte un transcript avec résumé de compaction
                nwork = max(nwork, 2)
                for x in [x for x in actions if x["kind"] == "feature_done"]:
                    actions.remove(x)            # (il édite HANDOFF.md → pas de filet) : reporté
                    nxt["feature_done"] = i + 1
            cnt["pc"] = cnt.get("pc", 0) + 1
        # ── tours ──
        turns = []
        per = [[] for _ in range(nwork)]
        for k, e in enumerate(edits):
            per[min(nwork - 1, k * nwork // max(1, len(edits)))].append(e)
        acts = [[] for _ in range(nwork)]
        for a in actions:
            acts[rng.randrange(nwork)].append(a)
        for w in range(nwork):
            ticket += rng.randint(1, 5)
            ed = per[w]
            fl = ed[0]["path"] if ed else (rng.choice(files) if files else "README.md")
            bank = QUESTIONS if question else ASKS
            msg = rng.choice(bank).format(feat=feat, file=fl, t=ticket)
            turns.append({"msg": msg, "as_list": rng.random() < 0.2, "edits": ed, "actions": acts[w],
                          "reads": rng.randint(1, 4), "reminder": rng.random() < 0.3,
                          "bash": rng.random() < 0.1, "interrupt": rng.random() < 0.05,
                          "commit": False, "precompact": False})
        commit = not question and rng.random() < 0.55
        if commit:
            turns[-1]["commit"] = True
        if precompact:
            w = max(range(nwork), key=lambda k: len(turns[k]["edits"]))
            turns[w]["precompact"] = True
        n_tests = 12 + 3 * i
        ho = {
            "goal": rng.choice(GOALS).format(feat=feat),
            "status": [rng.choice(STATUS).format(tests=tests_cmd, n=n_tests) for _ in range(rng.randint(2, 3))],
            "fails": rng.sample(FAILS, rng.randint(1, 2)),
            "blockers": rng.sample(BLOCKERS, rng.randint(1, 2)),
            "next": [x.format(a=rng.randint(1, 3), b=rng.randint(1, 5), feat=feat)
                     for x in rng.sample(NEXTS, rng.randint(2, 3))],
            "fait": rng.choice(FAITS), "decide": rng.choice(DECISIONS), "reste": rng.choice(RESTES),
            "tests": tests_cmd, "task": f"T{rng.randint(1, 3)}.{rng.randint(1, 5)}",
            "stack": rng.random() < 0.2,   # < 1.4 : section datée ajoutée puis « préservée » (règle d'époque)
        }
        plan.append({"i": i, "gap_h": gap, "date": t, "question": question, "handoff": handoff,
                     "commit_docs": handoff and rng.random() < 0.3, "turns": turns, "ho": ho, "feat": feat})
    return plan


# ── Contenu de code (déterministe) ──────────────────────────────────────────────────────────

def code_unit(rel: str, n: int, trigger) -> str:
    stem = re.sub(r"\W", "_", Path(rel).stem)
    note = f" — {trigger}" if trigger else ""
    if rel.endswith(".py"):
        return (f"def {stem}_etape_{n}(montant_centimes: int) -> int:\n"
                f'    """Étape {n} de {stem}{note}."""\n    return montant_centimes + {n}\n')
    if rel.endswith(".ts"):
        return (f"// Étape {n}{note}\nexport function {stem.replace('.', '_')}Etape{n}(montantCentimes: number): number {{\n"
                f"  return montantCentimes + {n};\n}}\n")
    if rel.endswith(".go"):
        return f"// Etape{n} — étape {n}{note}\nfunc Etape{n}(montantCentimes int) int {{\n\treturn montantCentimes + {n}\n}}\n"
    return f"# étape {n}{note}\n"


def code_header(rel: str) -> str:
    if rel.endswith(".py"):
        return f'"""{rel} — module de la caisse."""\n\n\n'
    if rel.endswith(".ts"):
        return f"// {rel} — module de la caisse\n\n"
    if rel.endswith(".go"):
        return f"package {Path(rel).parent.name}\n\n"
    return ""


def n8n_workflow(rel: str, n: int, trigger) -> str:
    nodes = [{"id": det_uuid(f"{rel}:{k}"), "name": f"Étape {k}", "type": "n8n-nodes-base.set",
              "typeVersion": 3.4, "position": [k * 220, 0],
              "parameters": {"notes": trigger if (trigger and k == n) else ""}} for k in range(1, n + 1)]
    return json.dumps({"name": Path(rel).stem, "nodes": nodes, "connections": {}, "settings": {"executionOrder": "v1"}},
                      ensure_ascii=False, indent=2) + "\n"


# ── Transcript JSONL réaliste ────────────────────────────────────────────────────────────────

class Transcript:
    """Entrées au format Claude Code : messages humains (texte ou liste), tool_use/tool_result
    (avec `toolUseResult`), rappels système, méta, commandes (/handoff, /exit…)."""

    def __init__(self, path: Path, sid: str, cwd: Path, branch: str):
        self.path, self.sid, self.cwd, self.branch = path, sid, str(cwd), branch
        self.n, self.parent = 0, None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    def _id(self):
        self.n += 1
        return det_uuid(f"{self.sid}:{self.n}")

    def _put(self, typ, message, **extra):
        u = self._id()
        e = {"parentUuid": self.parent, "isSidechain": False, "userType": "external", "cwd": self.cwd,
             "sessionId": self.sid, "version": "2.1.263", "gitBranch": self.branch, "type": typ,
             "message": message, "uuid": u, "timestamp": now_iso(), **extra}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        self.parent = u

    def user(self, content, **extra):
        self._put("user", {"role": "user", "content": content}, **extra)

    def human(self, text, as_list=False):
        self.user([{"type": "text", "text": text}] if as_list else text)

    def assistant(self, text):
        self._put("assistant", {"id": "msg_" + self._id()[:8], "type": "message", "role": "assistant",
                                "model": "claude-opus-4-5", "content": [{"type": "text", "text": text}],
                                "stop_reason": "end_turn", "usage": {"input_tokens": 9, "output_tokens": 60}})

    def tool(self, name, inp, result, tur=None):
        tid = "toolu_" + self._id().replace("-", "")[:24]
        self._put("assistant", {"id": "msg_" + tid[6:14], "type": "message", "role": "assistant",
                                "model": "claude-opus-4-5",
                                "content": [{"type": "tool_use", "id": tid, "name": name, "input": inp}],
                                "stop_reason": "tool_use", "usage": {"input_tokens": 9, "output_tokens": 40}})
        self.user([{"tool_use_id": tid, "type": "tool_result", "content": result}],
                  toolUseResult=tur if tur is not None else {"stdout": result, "stderr": "", "interrupted": False})

    def command(self, name, args=""):
        self.user(f"<command-message>{name} is running…</command-message>\n<command-name>/{name}</command-name>"
                  + (f"\n<command-args>{args}</command-args>" if args else ""))
        self.user([{"type": "text", "text": f"Base directory for this skill: {self.cwd}/.claude/skills/{name}\n\n# /{name}"}],
                  isMeta=True)

    def exit(self):
        self.user("<local-command-caveat>Caveat: The messages below were generated by the user while running "
                  "local commands. DO NOT respond to these messages or otherwise consider them in your response "
                  "unless the user explicitly asks you to.</local-command-caveat>", isMeta=True)
        self.user("<command-name>/exit</command-name>\n            <command-message>exit</command-message>\n"
                  "            <command-args></command-args>")
        self.user("<local-command-stdout>Goodbye!</local-command-stdout>")


class Ctx:
    """État d'une session en cours."""

    def __init__(self, i, sid, tr):
        self.i, self.sid, self.tr = i, sid, tr
        self.epoch = 0                 # +1 à chaque compaction (PreToolUse ré-armé)
        self.seen = set()              # (epoch, rel) déjà édités
        self.edited, self.humans = [], []
        self.handoff_touched = False
        self.warned_age = self.warned_size = False


# ── Le simulateur ────────────────────────────────────────────────────────────────────────────

class Sim:
    def __init__(self, key, label, ref, profile, plan, work: Path, seed):
        self.key, self.label, self.ref, self.profile, self.plan, self.seed = key, label, ref, profile, plan, seed
        self.work = work / key
        self.home, self.tmp, self.proj = self.work / "home", self.work / "tmp", self.work / "projet"
        for d in (self.home, self.tmp):
            d.mkdir(parents=True)
        self.env = base_env(self.home)
        self.henv = dict(self.env, CLAUDE_PROJECT_DIR=str(self.proj), TMPDIR=str(self.tmp))
        self.docs = self.proj / ".claude" / "docs"
        self.calls, self.recs, self.inj = [], [], []
        self.skipped, self.noops = {}, {}
        self.gotchas = {}              # n → {target, text, session}
        self.fcount = {}               # rel → nb d'unités de code (contenu déterministe)
        self.upgrade = None
        self.init_docs, self.init_budget = {}, None
        self.error = None
        self.elapsed = 0.0

    # ── état du projet ──
    def version(self):
        return tuple(int(x) for x in re.findall(r"\d+", read(self.proj / ".claude/template-version"))[:3])

    def new_conv(self):
        return self.version() >= (1, 4, 0)

    def is_v15(self):
        return self.version() >= (1, 5, 0)

    def has_skill(self, name):
        return (self.proj / ".claude/skills" / name / "SKILL.md").is_file()

    def git(self, *args, check=True, env=None):
        return sh(["git", *args], cwd=self.proj, env=env or self.env, check=check)

    def branch(self):
        return self.git("branch", "--show-current", check=False).stdout.strip() or "main"

    def tree_state(self):
        """Oracle « trace git » : HEAD + contenu de tout fichier suivi ou non ignoré (hors .cache)."""
        h = hashlib.sha1(self.git("rev-parse", "HEAD", check=False).stdout.encode())
        out = self.git("ls-files", "-co", "--exclude-standard", "-z", check=False).stdout
        for rel in sorted(set(x for x in out.split("\0") if x and not x.startswith(".claude/.cache/"))):
            p = self.proj / rel
            h.update(rel.encode() + b"\0" + (p.read_bytes() if p.is_file() else b"<absent>") + b"\0")
        return h.hexdigest()

    def doc_hashes(self):
        out = {}
        if self.docs.is_dir():
            for p in self.docs.rglob("*"):
                if p.is_file():
                    out[p.relative_to(self.docs).as_posix()] = hashlib.sha1(p.read_bytes()).hexdigest()
        return out

    def shift_time(self, hours):
        """Le temps passe : tous les mtimes du projet reculent (HANDOFF vieillit, le cache aussi)."""
        if not hours:
            return
        ns = int(hours * 3600 * 1e9)
        for dp, dns, fns in os.walk(self.proj):
            if ".git" in dns:
                dns.remove(".git")
            for fn in fns:
                p = os.path.join(dp, fn)
                try:
                    st = os.stat(p, follow_symlinks=False)
                    os.utime(p, ns=(st.st_atime_ns - ns, st.st_mtime_ns - ns), follow_symlinks=False)
                except OSError:
                    pass
        self.git("update-index", "-q", "--refresh", check=False)

    def measure(self):
        r = sh([sys.executable, BUDGET, "--root", self.proj, "--json", "--no-user"], env=self.env, check=False)
        try:
            j = json.loads(r.stdout)
        except ValueError:
            return -1, {}
        return int(j.get("total_tok", -1)), {f["path"]: f["tok"] for f in j.get("files", [])}

    # ── hooks : comme Claude Code (settings du projet, matcher, sh -c, CLAUDE_PROJECT_DIR) ──
    def hooks(self, event, extra, ctx, target=None):
        try:
            settings = json.loads(read(self.proj / ".claude/settings.json") or "{}")
        except ValueError:
            settings = {}
        payload = {"session_id": ctx.sid, "transcript_path": str(ctx.tr.path), "cwd": str(self.proj),
                   "hook_event_name": event, **extra}
        res = []
        for g in (settings.get("hooks") or {}).get(event) or []:
            m = g.get("matcher")
            if m not in (None, "", "*") and target is not None:
                try:
                    if not re.fullmatch(m, target):
                        continue
                except re.error:
                    continue
            for h in g.get("hooks") or []:
                if h.get("type") != "command":
                    continue
                cmd = h.get("command", "")
                t0 = time.time()
                try:
                    r = subprocess.run(["/bin/sh", "-c", cmd], input=json.dumps(payload, ensure_ascii=False),
                                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                                       cwd=self.proj, env=self.henv, timeout=h.get("timeout", 60))
                    rc, out, err = r.returncode, r.stdout, r.stderr
                except subprocess.TimeoutExpired:
                    rc, out, err = -9, "", f"TIMEOUT ({h.get('timeout', 60)} s)"
                names = re.findall(r"[\w.-]+\.(?:py|sh)\b", cmd)
                call = {"event": event, "hook": names[-1] if names else cmd, "rc": rc, "out": out, "err": err,
                        "ms": int((time.time() - t0) * 1000), "session": ctx.i, "target": target}
                problem = ""
                if rc != 0:
                    problem = f"exit {rc}: {err.strip()[-160:]}"
                elif "Traceback" in err:
                    problem = "traceback: " + err.strip().splitlines()[-1][:160]
                elif event in ("PreToolUse", "PostToolUse", "Stop", "PreCompact") and out.strip():
                    try:
                        json.loads(out)
                    except ValueError:
                        problem = "sortie non-JSON: " + out.strip()[:120]
                call["problem"] = problem
                self.calls.append(call)
                res.append(call)
        return res

    # ── écritures (Edit/Write) : PreToolUse → écriture → PostToolUse, transcript ──
    def live_gotchas(self):
        gf = self.docs / "code-map-gotchas.md"
        if gf.is_file():
            src = read(gf)
        else:
            m = re.search(r"(##\s+Gotchas.*?)(?=\n##\s|\Z)", read(self.docs / "code-map.md"), re.S)
            src = m.group(1) if m else ""
        return {int(x) for x in GOTCHA_RE.findall(src)}

    def tool_write(self, tool, rel, inp, content, ctx):
        p = self.proj / rel
        first = (ctx.epoch, rel) not in ctx.seen
        v15, kind = self.is_v15(), file_kind(rel)
        expect, allowed = set(), set()
        if v15 and first and kind != "methode":
            live = self.live_gotchas()
            allowed = {n for n, g in self.gotchas.items() if n in live and targets(g["target"], rel)
                       and (kind == "code" or g["target"] is not None)}
            expect = allowed if kind == "code" else set()   # config : ciblage explicite toléré, pas exigé
        res = self.hooks("PreToolUse", {"tool_name": tool, "tool_input": inp, "permission_mode": "default"}, ctx, tool)
        add = ""
        for c in res:
            try:
                add += (json.loads(c["out"]).get("hookSpecificOutput") or {}).get("additionalContext", "") if c["out"].strip() else ""
            except (ValueError, AttributeError):
                pass
        ctx.seen.add((ctx.epoch, rel))
        got = {int(x) for x in GOTCHA_RE.findall(add)}
        self.inj.append({"session": ctx.i, "rel": rel, "chars": len(add), "first": first, "kind": kind,
                         "v15": v15, "expect_n": len(expect), "missing": expect - got if v15 else set(),
                         "extra": (got - allowed) if (v15 and first and kind != "methode") else set(),
                         "got": got, "placeholder": "{{" in add})
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        self.hooks("PostToolUse", {"tool_name": tool, "tool_input": inp, "permission_mode": "default",
                                   "tool_response": {"filePath": str(p), "success": True}}, ctx, tool)
        ctx.tr.tool(tool, inp, f"The file {p} has been updated successfully.",
                    {"filePath": str(p), "structuredPatch": [], "userModified": False})
        if rel == ".claude/docs/HANDOFF.md":
            ctx.handoff_touched = True

    def write_doc(self, rel_doc, text, ctx):
        rel = f".claude/docs/{rel_doc}"
        p = self.proj / rel
        if p.exists():
            old = read(p)
            if old == text:
                return
            inp = {"file_path": str(p), "old_string": old[-200:], "new_string": text[-2000:]}
            self.tool_write("Edit", rel, inp, text, ctx)
        else:
            self.tool_write("Write", rel, {"file_path": str(p), "content": text[:4000]}, text, ctx)

    def edit_code(self, e, ctx):
        rel = e["path"]
        p = self.proj / rel
        n = self.fcount.get(rel, 0) + 1
        self.fcount[rel] = n
        if rel.endswith(".json"):
            content = n8n_workflow(rel, n, e["trigger"])
            self.tool_write("Write", rel, {"file_path": str(p), "content": content}, content, ctx)
        elif not p.exists():
            content = code_header(rel) + code_unit(rel, n, e["trigger"])
            self.tool_write("Write", rel, {"file_path": str(p), "content": content}, content, ctx)
        else:
            old = read(p)
            last = [l for l in old.split("\n") if l.strip()][-1]
            unit = code_unit(rel, n, e["trigger"])
            sep = "\n\n\n" if rel.endswith(".py") else "\n\n"
            content = old.rstrip("\n") + sep + unit
            self.tool_write("Edit", rel, {"file_path": str(p), "old_string": last,
                                          "new_string": last + sep + unit.rstrip("\n")}, content, ctx)
        if rel not in ctx.edited:
            ctx.edited.append(rel)

    def commit(self, msg, when, ctx):
        if not self.git("status", "--porcelain", check=False).stdout.strip():
            return False
        d = when.strftime("%Y-%m-%dT%H:%M:%S")
        env = dict(self.env, GIT_AUTHOR_DATE=d, GIT_COMMITTER_DATE=d)
        self.git(*GIT[1:], "add", "-A", env=env)
        self.git(*GIT[1:], "commit", "-qm", msg, env=env)
        if ctx:
            ctx.tr.tool("Bash", {"command": f'git add -A && git commit -m "{msg}"', "description": "Commit"},
                        f"[{self.branch()}] {msg}")
        return True

    # ── skills émulés ──
    def skip(self, kind):
        self.skipped[kind] = self.skipped.get(kind, 0) + 1

    def noop(self, kind):
        self.noops[kind] = self.noops.get(kind, 0) + 1

    def action(self, a, s, ctx):
        kind = a["kind"]
        if not self.has_skill(ACTION_SKILL[kind]):
            return self.skip(kind)
        getattr(self, f"act_{kind}")(a, s, ctx)

    def current_spec(self):
        rm = read(self.docs / "ROADMAP.md")
        for state in ("~", " "):
            m = re.search(rf"^- \[{re.escape(state)}\] \[(\d{{3}}-[\w-]+)\]", rm, re.M)
            if m:
                tasks = read(self.docs / "specs" / m.group(1) / "tasks.md")
                return m.group(1), len(re.findall(r"^- \[x\] \*\*T", tasks, re.M)), len(re.findall(r"^- \[[ x]\] \*\*T", tasks, re.M))
        return None

    def act_note(self, a, s, ctx):
        """L'utilisateur ajoute à la main une section non datée dans HANDOFF.md (/handoff < 1.4 la
        « préserve » ; ≥ 1.4 la déplace dans le journal : jamais perdue)."""
        text = read(self.docs / "HANDOFF.md").rstrip("\n")
        self.write_doc("HANDOFF.md", text + f"\n\n## {NOTE_MARK}\n\n- Sophie préfère les démos le vendredi matin\n"
                                            "- Ne jamais toucher au paramétrage TPE sans le prestataire\n", ctx)

    def act_spec(self, a, s, ctx):
        specs = self.docs / "specs"
        ids = [int(m.group()) for d in (specs.iterdir() if specs.is_dir() else []) if (m := re.match(r"\d+", d.name))]
        sid = f"{max(ids, default=0) + 1:03d}"
        date = s["date"].strftime("%Y-%m-%d")
        tpl = self.proj / ".claude/skills/spec/templates"
        ntasks = 0
        for name in ("research", "spec", "plan", "tasks"):
            text = read(tpl / f"{name}.md")
            for k, v in (("{{SPEC_ID}}", sid), ("{{SPEC_TITRE}}", a["titre"]), ("{{SPEC_KEBAB}}", a["kebab"]),
                         ("{{SPEC_DATE}}", date)):
                text = text.replace(k, v)
            if name == "spec" and a["start"]:
                text = text.replace("status: draft", "status: in-progress", 1)
            if name == "tasks":
                ntasks = len(re.findall(r"^- \[ \] \*\*T", text, re.M))
            self.write_doc(f"specs/{sid}-{a['kebab']}/{name}.md", text, ctx)
        line = (f"- [~] [{sid}-{a['kebab']}](specs/{sid}-{a['kebab']}/spec.md) — **EN COURS** 0/{ntasks} tasks"
                if a["start"] else f"- [ ] [{sid}-{a['kebab']}](specs/{sid}-{a['kebab']}/spec.md) — pas commencé")
        rm = self.docs / "ROADMAP.md"
        if rm.is_file():
            lines = read(rm).split("\n")
            try:
                h = next(k for k, l in enumerate(lines) if l.startswith("### Composants"))
                j = next(k for k in range(h + 1, len(lines)) if lines[k].startswith("- ") or lines[k].startswith("#"))
            except StopIteration:
                lines += ["", line]
            else:
                k = j
                while k < len(lines) and lines[k].startswith("- "):
                    k += 1
                block = [b for b in lines[j:k] if "{{" not in b and b.strip() != "- [ ] ..."] + [line]
                lines[j:k] = block
            text = "\n".join(lines)
            text = re.sub(r"^\*\*Dernière MAJ :\*\* .*$", f"**Dernière MAJ :** {date}", text, count=1, flags=re.M)
            self.write_doc("ROADMAP.md", text, ctx)

    def act_feature_done(self, a, s, ctx):
        rm = self.docs / "ROADMAP.md"
        m = re.search(r"^- \[[ ~]\] \[(\d{3}-[\w-]+)\]\(specs/[^)]+\).*$", read(rm), re.M) if rm.is_file() else None
        if not m:
            return self.noop("feature_done")
        spec_id, date = m.group(1), s["date"].strftime("%Y-%m-%d")
        d = f"specs/{spec_id}"
        tasks = read(self.docs / d / "tasks.md")
        total = len(re.findall(r"^- \[[ x]\] \*\*T", tasks, re.M))
        self.write_doc(f"{d}/tasks.md", re.sub(r"^- \[ \] ", "- [x] ", tasks, flags=re.M), ctx)
        spec = read(self.docs / d / "spec.md")
        spec = re.sub(r"^status: \S+", "status: done", spec, count=1, flags=re.M)
        spec = re.sub(r"^progress: \S+", f"progress: {total}/{total}", spec, count=1, flags=re.M)
        self.write_doc(f"{d}/spec.md", spec, ctx)
        titre = re.search(r"^# Spec — (.+)$", spec, re.M)
        titre = titre.group(1) if titre else spec_id
        self.write_doc("ROADMAP.md", read(rm).replace(m.group(0), f"- [x] [{spec_id}]({d}/spec.md) — livré {date}"), ctx)
        self.changelog_add("Added", f"- {titre} ([spec](specs/{spec_id}/spec.md))", ctx)
        # Étape 5 : HANDOFF — Status + Next
        ho = read(self.docs / "HANDOFF.md")
        if "## Status" in ho:
            ho = re.sub(r"(## Status\n\n)", rf"\1- ✅ Feature `{spec_id}` livrée {date}\n", ho, count=1)
            self.write_doc("HANDOFF.md", ho, ctx)

    def changelog_add(self, sub, bullet, ctx):
        cl = self.docs / "CHANGELOG.md"
        if not cl.is_file():
            return
        lines = read(cl).split("\n")
        try:
            u = next(k for k, l in enumerate(lines) if l.startswith("## [Unreleased]"))
            end = next((k for k in range(u + 1, len(lines)) if lines[k].startswith("## ")), len(lines))
            h = next(k for k in range(u + 1, end) if lines[k].strip() == f"### {sub}")
        except StopIteration:
            lines[u + 1:u + 1] = ["", f"### {sub}", "", bullet]
        else:
            j = h + 1
            while j < end and not lines[j].startswith("- "):
                j += 1
            k = j
            while k < end and lines[k].startswith("- "):
                k += 1
            lines[j:k] = [b for b in lines[j:k] if "{{" not in b] + [bullet]
        self.write_doc("CHANGELOG.md", "\n".join(lines), ctx)

    def act_adr(self, a, s, ctx):
        adr = self.docs / "adr"
        nums = [int(m.group()) for p in adr.glob("[0-9]*.md") if (m := re.match(r"\d+", p.name))]
        n = f"{max(nums, default=0) + 1:04d}"
        date = s["date"]
        fname = f"{n}-{a['scope']}-{a['kebab']}.md"
        body = (f"---\nstatus: accepted\nscope: {a['scope']}\nphase: {date.year}-Q{(date.month - 1) // 3 + 1}\n"
                f"supersedes: null\n---\n\n# {n} — {a['titre']}\n\n**Statut :** Accepted\n"
                f"**Date :** {date:%Y-%m-%d}\n**Décideur :** Sophie Martin\n\n## Contexte\n\n"
                "La caisse doit tourner chez un seul commerçant d'abord, puis sur plusieurs boutiques.\n\n"
                "## Options considérées\n\n- **Option A** : la solution retenue — simple, réversible\n"
                "- **Option B** : l'alternative lourde — effort ×3\n- **Option C — ne rien faire** : dette qui grossit\n\n"
                f"## Décision\n\n{a['titre']} — option A, pour sa réversibilité.\n\n## Conséquences\n\n"
                "- ✅ moins de pièces mobiles\n- ⚠️ à revoir au passage multi-boutiques\n\n## Liens\n\n- [ROADMAP](../ROADMAP.md)\n")
        self.write_doc(f"adr/{fname}", body, ctx)
        heading = {"cadrage": "### 📥 cadrage", "mvp": "### 🎨 mvp", "infra": "### 🚀 infra",
                   "operations": "### 🛠️ operations"}.get(a["scope"], "### 🔧 features")
        lines = read(adr / "README.md").split("\n")
        row = f"| [{n}]({fname}) | {a['titre']} | Accepted |"
        try:
            h = next(k for k, l in enumerate(lines) if l.startswith(heading))
        except StopIteration:
            lines += ["", row]
        else:
            end = next((k for k in range(h + 1, len(lines)) if lines[k].startswith("#")), len(lines))
            tbl = [k for k in range(h + 1, end) if lines[k].startswith("|")]
            if not tbl:   # cadrage : liste, pas de table
                bl = [k for k in range(h + 1, end) if lines[k].startswith("- ")]
                entry = f"- [{n}]({fname}) — {a['titre']} (Accepted)"
                if bl and "_(aucune" in lines[bl[0]]:
                    lines[bl[0]] = entry
                else:
                    lines.insert((bl[-1] + 1) if bl else h + 2, entry)
            else:
                ph = next((k for k in tbl[2:] if "_(" in lines[k]), None)
                if ph is not None:
                    lines[ph] = row
                else:
                    lines.insert(tbl[-1] + 1, row)
        self.write_doc("adr/README.md", "\n".join(lines), ctx)
        self.changelog_add("Decided", f"- {a['titre']} ([ADR-{n}](adr/{fname}))", ctx)

    def act_lecon(self, a, s, ctx):
        p = self.docs / "lecons.md"
        titre, contexte, solution, decision = a["lecon"]
        entry = (f"## {s['date']:%Y-%m-%d} — {titre} [L{a['n']}]\n\n**scope:** {a['scope']} | **status:** 🆕 new\n\n"
                 f"{contexte}\n{solution}\n→ {decision}\n")
        lines = read(p).split("\n")
        fence, sep = False, None
        for k, l in enumerate(lines):
            if re.match(r"^\s{0,3}```", l):
                fence = not fence
            elif not fence and l.strip() == "---":
                sep = k
        lines = [l for l in lines if not l.startswith("_(Aucune leçon")]
        if sep is None:
            text = "\n".join(lines).rstrip("\n") + "\n\n" + entry
        else:
            text = "\n".join(lines[:sep + 1]) + "\n\n" + entry + "\n" + "\n".join(lines[sep + 1:]).strip("\n") + "\n"
        self.write_doc("lecons.md", re.sub(r"\n{3,}", "\n\n", text), ctx)

    def act_idee(self, a, s, ctx):
        date = f"{s['date']:%Y-%m-%d}"
        rel, k = f"idees/{date}-{a['kebab']}.md", 2
        while (self.docs / rel).exists():
            rel, k = f"idees/{date}-{a['kebab']}-{k}.md", k + 1
        self.write_doc(rel, f"# Idée — {a['titre']}\n\n**Date :** {date}\n**Source :** en codant\n\n## Pitch\n\n"
                            f"{a['titre']} : gagner du temps en boutique.\n\n## Use case\n\nLe samedi, rush de midi.\n\n"
                            f"## Effort estimé\n\n{a['effort']}\n\n## Statut\n\n💡 Backlog\n", ctx)

    def act_gotcha(self, a, s, ctx):
        n, target = a["n"], a["target"]
        self.gotchas[n] = {"target": target, "text": a["text"], "session": s["i"]}
        bullet = (f"- ⚠️ {a['text']} (piège G{n})" if target is None
                  else f"- ⚠️ `{target}` — {a['text']} (piège G{n})")
        if self.new_conv():
            gf = self.docs / "code-map-gotchas.md"
            text = read(gf) or "# Gotchas — pièges non évidents (injectés à la demande)\n\n## Globaux\n\n## Par zone\n"
            want = "Globaux" if target is None else "Par zone"
            parts = split_h2(text)
            idx = next((k for k, (h, _) in enumerate(parts) if h and want in h), None)
            if idx is None:
                text = text.rstrip("\n") + f"\n\n## {want}\n\n{bullet}\n"
            else:
                h, body = parts[idx]
                kept = [l for l in body.split("\n") if "{{" not in l]   # le gabarit remplacé par du réel
                body = "\n".join(kept).rstrip("\n")
                body = (body + "\n" if body.strip() else "\n") + bullet + "\n"
                parts[idx] = (h, body)
                text = "\n".join((f"{hh}\n{bb}" if hh else bb) for hh, bb in parts)
            self.write_doc("code-map-gotchas.md", re.sub(r"\n{3,}", "\n\n", text), ctx)
        else:
            cm = self.docs / "code-map.md"
            text = read(cm)
            if a["misplaced"] or "## Gotchas" not in text:
                # < 1.4 : gotcha appendé en FIN de code-map.md (sous « Quand mettre à jour ») — vécu
                # 2026-09-08 : 4,7k tokens de ⚠️ auto-chargés à cet endroit sur un projet d'un mois.
                text = text.rstrip("\n") + "\n\n" + bullet + "\n"
            else:
                parts = split_h2(text)
                idx = next(k for k, (h, _) in enumerate(parts) if h and h.startswith("## Gotchas"))
                h, body = parts[idx]
                parts[idx] = (h, body.rstrip("\n") + "\n" + bullet + "\n")
                text = "\n".join((f"{hh}\n{bb}" if hh else bb) for hh, bb in parts)
            self.write_doc("code-map.md", text, ctx)

    def act_coupling(self, a, s, ctx):
        cm = self.docs / "code-map.md"
        text = read(cm)
        rule = f"- ❌ `{a['a']}` ne doit **JAMAIS** importer `{a['b']}` — {a['raison']} (règle C{a['n']})"
        parts = split_h2(text)
        idx = next((k for k, (h, _) in enumerate(parts) if h and h.startswith("## Règles de couplage")), None)
        if idx is None:
            text = text.rstrip("\n") + f"\n\n## Règles de couplage\n\n{rule}\n"
        else:
            h, body = parts[idx]
            lines = body.split("\n")
            last = max((k for k, l in enumerate(lines) if l.startswith("- ")), default=len(lines) - 1)
            lines.insert(last + 1, rule)
            parts[idx] = (h, "\n".join(lines))
            text = "\n".join((f"{hh}\n{bb}" if hh else bb) for hh, bb in parts)
        text = re.sub(r"^\*\*Dernière MAJ :\*\* .*$", f"**Dernière MAJ :** {s['date']:%Y-%m-%d}", text, count=1, flags=re.M)
        if self.new_conv():   # /codemap ≥ 1.4 : code-map.md auto-chargée, budget < 3k tokens → élagage
            while len(text) // 2 > 3000 and COUPLING_RE.search(text):
                text = re.sub(r"^- ❌ .*\(règle C\d+\)\n", "", text, count=1, flags=re.M)
                self.noop("coupling_pruned")
        self.write_doc("code-map.md", text, ctx)

    # ── /handoff ──
    def handoff_state(self, s, ctx, v14: bool):
        ho, date = s["ho"], s["date"]
        spec = self.current_spec()
        spec_line = (f"**Spec en cours** : [{spec[0]}](specs/{spec[0]}/spec.md) ({spec[1]}/{spec[2]} tasks)"
                     if spec else "**Spec en cours** : aucune")
        quote = ("> Court, narratif, versionné. Patterns techniques → auto-memory. Reprise précise → /resume." if v14 else
                 "> Court, narratif, versionné. **Patterns techniques** → auto-memory (Claude le gère).\n"
                 "> **Reprise précise** → utilise `/resume`. Ce fichier = \"où j'en suis\" pour démarrage à froid.")
        files = ", ".join(ctx.edited[:3]) or "aucun"
        lines = [f"# HANDOFF — {date:%Y-%m-%d %Hh%M}", "", quote, "",
                 f"**Branche** : `{self.branch()}`", spec_line, f"**Goal session** : {ho['goal']}", "",
                 "## Status", "", *[f"- {x}" for x in ho["status"]], "",
                 "## Échecs tentés (à ne pas refaire)", "", *[f"- {x}" for x in ho["fails"]], "",
                 "## Blocked on", "", *[f"- {x}" for x in ho["blockers"]], "",
                 "## Next (par ordre)", "", *[f"{k}. {x}" for k, x in enumerate(ho["next"], 1)], "",
                 "## Continuation State (machine-readable — grammaire fixe `Clé: valeur`, 1 ligne chacune)", "",
                 f"Spec: {spec[0] if spec else 'aucune'}", f"Task: {ho['task'] if spec else 'aucune'}",
                 f"Fichiers en cours: {files}", f"Bloqué sur: {ho['blockers'][0]}",
                 f"Commande de reprise: {ho['tests']}"]
        return "\n".join(lines)

    FORMAT = ("Status", "Échecs tentés", "Blocked on", "Next", "Continuation State")

    def do_handoff(self, s, ctx, rec):
        ctx.tr.command("handoff")
        cur = read(self.docs / "HANDOFF.md")
        fresh = len(re.findall(r"\{\{[^}]+\}\}", cur)) > 5
        date = s["date"]
        journal_old, custom = "", []
        if not fresh:
            for h, body in split_h2(cur):
                if h is None:
                    continue
                title = h[3:].strip()
                if title.startswith("Journal"):
                    journal_old = body.strip("\n")
                elif not title.startswith(self.FORMAT):
                    custom.append(f"{h}\n{body.strip(chr(10))}")
        if self.new_conv():
            # ≥ 1.4 : réécriture au format strict (+ pointeur), jamais empilé ; hors-format → journal
            text = self.handoff_state(s, ctx, True) + "\n\n→ **Journal des sessions** (append-only) : " \
                "[HANDOFF-journal.md](HANDOFF-journal.md) — non auto-chargé.\n"
            jp = self.docs / "HANDOFF-journal.md"
            journal = read(jp) or ("# Journal HANDOFF — append-only\n\n> 1 ligne par session, ajoutée par `/handoff`, "
                                   "**jamais réécrite**. Non auto-chargé : lu à la demande.\n\n## Journal\n\n")
            journal = journal.rstrip("\n") + ("\n\n" if journal.rstrip("\n").split("\n")[-1].startswith("#") else "\n")
            if journal_old:
                journal += journal_old + "\n"               # Étape 3bis.2 : migration sans perte
            if custom:   # Étape 2 : sections hors format déplacées telles quelles, avant le § Journal
                block = f"## Archive {date:%Y-%m-%d}\n\n" + "\n\n".join(custom) + "\n\n"
                k = journal.find("\n## Journal")
                journal = journal[:k + 1] + block + journal[k + 1:] if k >= 0 else journal + "\n" + block
            journal += f"- {date:%Y-%m-%d} — Session {s['i']} · {s['ho']['goal']} : {s['ho']['fait']}\n"
            self.write_doc("HANDOFF.md", text, ctx)
            self.write_doc("HANDOFF-journal.md", journal, ctx)
        else:
            # < 1.4 : état réécrit, sections maison « préservées », section datée appendée au § Journal
            ho = s["ho"]
            entry = (f"### {date:%Y-%m-%d} — Session {s['i']} · {ho['goal']}\n\n- Fait : {ho['fait']} "
                     f"({', '.join(ctx.edited[:3]) or 'pas de code'})\n- Décidé : {ho['decide']}\n"
                     f"- Reste : {ho['reste']} ; prochaine étape : {re.sub(r'[*]', '', ho['next'][0])}")
            if ho["stack"]:   # « préserver les sections custom » (v1.3.3) : une section datée ajoutée
                custom.append(f"## {date:%Y-%m-%d} — Point d'étape (S{s['i']})\n\n- {ho['fait']} terminé\n"
                              f"- Décision : {ho['decide']}\n- À surveiller : {ho['reste']}")   # … ne repart jamais
            parts = [self.handoff_state(s, ctx, False), *custom,
                     "## Journal (append-only — 1 ligne par session, NE JAMAIS réécrire)\n\n"
                     + (journal_old + "\n\n" if journal_old else "") + entry]
            self.write_doc("HANDOFF.md", "\n\n".join(parts) + "\n", ctx)
        rec["did_handoff"] = True
        rec["handoff_lines"] = len(read(self.docs / "HANDOFF.md").rstrip("\n").split("\n"))

    # ── compaction ──
    def compact(self, s, ctx, rec):
        self.hooks("PreCompact", {"trigger": "auto", "custom_instructions": ""}, ctx, "auto")
        # La compaction réécrit la suite du transcript : frontière système + résumé porté par une
        # entrée `user` marquée isCompactSummary — ce n'est PAS un message humain.
        ctx.tr._put("system", None, subtype="compact_boundary", content="Conversation compacted",
                    compactMetadata={"trigger": "auto", "preTokens": 167000})
        ctx.tr.user("This session is being continued from a previous conversation that ran out of context. "
                    "The conversation is summarized below:\nAnalysis: l'utilisateur travaille sur la caisse…",
                    isCompactSummary=True, isVisibleInTranscriptOnly=True)
        res = self.hooks("SessionStart", {"source": "compact"}, ctx, "compact")
        out = "".join(c["out"] for c in res)
        ok_ = "Re-injection post-compaction" in out and snapshot_ok(out, ctx.humans)
        empty = len(re.findall(r"^- *$", out, re.M))
        rec["compactions"].append({"ok": ok_, "empty": empty, "chars": len(out)})
        ctx.epoch += 1
        if ctx.edited:   # ré-édition d'un fichier déjà touché : les gotchas doivent revenir (ré-armés)
            self.edit_code({"path": ctx.edited[0], "trigger": None}, ctx)

    # ── Stop ──
    def stop_expect(self, ctx):
        """Oracle 1.5.0 du hook Stop (1 message max par appel, 1×/session et par motif)."""
        ho = self.docs / "HANDOFF.md"
        if not ho.is_file() or (self.proj / ".claude/archived").exists():
            return None
        if ho.stat().st_size > STOP_SIZE_BYTES and not ctx.warned_size:
            ctx.warned_size = True
            return "size"
        if int((time.time() - ho.stat().st_mtime) // 3600) < 24:
            return None
        if not self.git("status", "--short", check=False).stdout.strip() or ctx.warned_age:
            return None
        ctx.warned_age = True
        return "age"

    def stop(self, ctx, rec):
        exp = self.stop_expect(ctx) if self.is_v15() else None
        got = []
        for c in self.hooks("Stop", {"stop_hook_active": False}, ctx):
            try:
                msg = json.loads(c["out"]).get("systemMessage", "") if c["out"].strip() else ""
            except ValueError:
                msg = ""
            if msg:
                got.append("size" if "📏" in msg else "age" if "⏰" in msg else "autre")
        rec["stops"].append({"exp": exp, "got": got})

    # ── une session complète ──
    def run_session(self, s):
        i = s["i"]
        self.shift_time(s["gap_h"])
        sid = det_uuid(f"{self.seed}:{self.key}:{i}")
        tr = Transcript(self.work / "transcripts" / f"{sid}.jsonl", sid, self.proj, self.branch())
        ctx = Ctx(i, sid, tr)
        rec = {"i": i, "sid": sid, "date": s["date"], "version": ".".join(map(str, self.version())),
               "v15": self.is_v15(), "did_handoff": False, "handoff_lines": None, "stops": [], "compactions": []}
        state0 = self.tree_state()
        out = "".join(c["out"] for c in self.hooks("SessionStart", {"source": "startup"}, ctx, "startup"))
        rec.update(filet="Filet mémoire" in out, budget_warn="Budget de contexte dépassé" in out,
                   startup_chars=len(out), filet_text=out if "Filet mémoire" in out else "")
        for turn in s["turns"]:
            tr.human(turn["msg"], as_list=turn["as_list"])
            ctx.humans.append(turn["msg"])
            if turn["reminder"]:
                tr.user([{"type": "text", "text": "<system-reminder>Le fichier a été modifié par l'utilisateur.</system-reminder>"}])
            if turn["bash"]:
                tr.user("<bash-input>git status</bash-input>")
                tr.user("<bash-stdout>On branch main</bash-stdout><bash-stderr></bash-stderr>")
            tr.assistant("Je regarde le code concerné.")
            for k in range(turn["reads"]):
                name = ("Read", "Grep", "Bash")[k % 3]
                tr.tool(name, {"file_path": str(self.proj / "src")} if name == "Read" else {"pattern": "def "},
                        f"{name} : {3 + k} résultats")
            for e in turn["edits"]:
                self.edit_code(e, ctx)
            for a in turn["actions"]:
                self.action(a, s, ctx)
            if turn["interrupt"]:
                tr.user([{"type": "text", "text": "[Request interrupted by user]"}])
            if turn["commit"]:
                self.commit(f"feat: session {i} — {s['feat']}", s["date"], ctx)
            if turn["precompact"]:
                self.compact(s, ctx, rec)
            tr.assistant("C'est fait : tests verts de mon côté.")
            self.stop(ctx, rec)
        if s["handoff"] and self.has_skill("handoff"):
            self.do_handoff(s, ctx, rec)
            if s["commit_docs"]:
                self.commit(f"docs: handoff session {i}", s["date"], ctx)
            tr.assistant("HANDOFF mis à jour.")
            self.stop(ctx, rec)
        elif s["handoff"]:
            self.skip("handoff")
        tr.exit()
        self.hooks("SessionEnd", {"reason": "prompt_input_exit"}, ctx)
        net = self.proj / ".claude/.cache/session-end-snapshot.md"
        rec["net_exists"] = net.is_file()
        rec["git_trace"] = self.tree_state() != state0
        rec["handoff_touched"] = ctx.handoff_touched
        rec["expected_net"] = rec["git_trace"] and not ctx.handoff_touched
        rec["humans"] = ctx.humans[-3:]
        rec["budget"], files = self.measure()
        ho = read(self.docs / "HANDOFF.md")
        rec.update(handoff_lines_end=len(ho.rstrip("\n").split("\n")) if ho else 0, handoff_bytes=len(ho.encode()),
                   codemap_tok=len(read(self.docs / "code-map.md")) // 2,
                   journal_bytes=len(read(self.docs / "HANDOFF-journal.md").encode()),
                   files_tok=files, pretool_chars=sum(x["chars"] for x in self.inj if x["session"] == i))
        cache = self.proj / ".claude/.cache"
        per = [p.name for p in cache.glob("*") if re.match(
            r"(codemap-injected-|handoff-size-warned-|handoff-age-warned-|session-start-|handoff-snapshot-)", p.name)] \
            if cache.is_dir() else []
        rec["cache_files"] = per
        self.recs.append(rec)

    # ── scénario B : personnalisations + upgrade ──
    def do_upgrade(self, when):
        u = {}
        self.commit("wip: fin de sprint avant mise à jour du template", when, None)
        st_p = self.proj / ".claude/settings.json"
        st = json.loads(read(st_p))
        st["permissions"]["allow"].append("Bash(make:*)")
        st_p.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        gw = self.proj / ".claude/rules/git-workflow.md"
        anchor = "- Pas de SemVer (projet client, pas une lib)\n"
        u["custom_line"] = "- ✅ Revue par un pair avant tout merge (règle maison)"
        u["anchor_found"] = anchor in read(gw)
        gw.write_text(read(gw).replace(anchor, anchor + u["custom_line"] + "\n"), encoding="utf-8")
        sk = self.proj / ".claude/skills/deploy-client/SKILL.md"
        sk.parent.mkdir(parents=True)
        u["skill_bytes"] = ("---\nname: deploy-client\ndescription: Déploie chez le client (maison)\n---\n\n"
                            "# /deploy-client\n\n1. `make release`\n2. copie sur le serveur de la boutique\n").encode()
        sk.write_bytes(u["skill_bytes"])
        self.commit("chore: personnalisations locales (allow make, règle de revue, skill deploy-client)", when, None)
        u["before"] = self.content()
        u["docs_before"] = {n: read(self.docs / n) for n in ("HANDOFF.md", "code-map.md")}
        u["budget_before"], _ = self.measure()
        t0 = time.time()
        r = sh([sys.executable, UPGRADE, "--project", self.proj, "--template", ROOT, "--to", "WORKTREE", "--json"],
               env=self.env, check=False)
        u["seconds"] = time.time() - t0
        u["rc"] = r.returncode
        try:
            u["report"] = json.loads(r.stdout)
        except ValueError:
            u["report"] = {"status": "sortie illisible", "error": (r.stdout + r.stderr)[-600:]}
        u["after"] = self.content()
        u["docs_after"] = {n: read(self.docs / n) for n in ("HANDOFF.md", "HANDOFF-journal.md", "code-map.md",
                                                            "code-map-gotchas.md")}
        u["budget_after"], u["files_after"] = self.measure()
        st2 = json.loads(read(st_p) or "{}")
        u["allow_kept"] = "Bash(make:*)" in (st2.get("permissions") or {}).get("allow", [])
        u["line_kept"] = u["custom_line"] in read(gw)
        u["skill_kept"] = sk.is_file() and sk.read_bytes() == u["skill_bytes"]
        u["version_after"] = ".".join(map(str, self.version()))
        u["committed"] = self.commit("chore(template): mise à jour claude-Setup → 1.5.0 (/upgrade-template)", when, None)
        self.upgrade = u

    def content(self):
        d = self.docs
        ho, jr = read(d / "HANDOFF.md"), read(d / "HANDOFF-journal.md")
        cm, gf = read(d / "code-map.md"), read(d / "code-map-gotchas.md")
        ls = lambda p, pat: sorted(x.name for x in p.glob(pat)) if p.is_dir() else []
        return {
            "journal_handoff": {int(x) for x in JOURNAL_RE.findall(ho)},
            "journal_file": {int(x) for x in JOURNAL_RE.findall(jr)},
            "gotchas_codemap": {int(x) for x in GOTCHA_RE.findall(cm)},
            "gotchas_file": {int(x) for x in GOTCHA_RE.findall(gf)},
            "coupling": {int(x) for x in COUPLING_RE.findall(cm)},
            "specs": [x for x in ls(d / "specs", "*") if (d / "specs" / x).is_dir()],
            "adrs": ls(d / "adr", "[0-9]*.md"),
            "lecons": {int(x) for x in LECON_RE.findall(read(d / "lecons.md"))},
            "idees": [x for x in ls(d / "idees", "*.md") if x != "README.md"],
            "note": NOTE_MARK in ho or NOTE_MARK in jr,
            "stack_handoff": {int(x) for x in STACK_RE.findall(ho)},
            "stack_file": {int(x) for x in STACK_RE.findall(jr)},
        }

    # ── déroulé ──
    def setup(self):
        init_project(self.ref, self.profile, self.proj, self.env)
        self.init_docs = self.doc_hashes()
        self.init_budget, _ = self.measure()
        self.init_skills = sorted(p.name for p in (self.proj / ".claude/skills").iterdir() if p.is_dir())

    def run(self, upgrade_after=None):
        t0 = time.time()
        try:
            self.setup()
            for s in self.plan:
                if upgrade_after is not None and s["i"] == upgrade_after + 1:
                    self.do_upgrade(self.plan[upgrade_after - 1]["date"] + timedelta(hours=2))
                self.run_session(s)
        except Exception:
            self.error = traceback.format_exc()
        self.elapsed = time.time() - t0
        return self


# ── Invariants 1.5.0 et métriques ────────────────────────────────────────────────────────────

def invariants(sim, recs):
    """Liste de (clé, libellé, ok) — invariants 1.5.0 sur des sessions consécutives de la phase 1.5."""
    idx = {r["i"] for r in recs}
    out = []
    calls = [c for c in sim.calls if c["session"] in idx]
    bad = [c for c in calls if c["problem"]]
    serr = [c for c in calls if c["err"].strip() and not c["problem"]]
    out.append(("hooks", f"aucun hook en erreur : {len(calls)} appels, 0 exit≠0, 0 traceback, sorties JSON valides"
                + (f" ({len(serr)} avec stderr : {serr[0]['hook']} « {serr[0]['err'].strip()[:80]} »)" if serr else "")
                + (f" — {len(bad)} KO, ex. s{bad[0]['session']} {bad[0]['hook']} ({bad[0]['event']}) : {bad[0]['problem']}" if bad else ""),
                not bad))
    pairs = list(zip(recs, recs[1:]))
    fp = [c["i"] for p, c in pairs if c["filet"] and not p["expected_net"]]
    fn = [c["i"] for p, c in pairs if p["expected_net"] and not c["filet"]]
    src = [r["i"] for r in recs if r["net_exists"] != r["expected_net"]]
    n_exp = sum(1 for p, _ in pairs if p["expected_net"])
    other = sum(1 for p, _ in pairs if not p["did_handoff"] and p["handoff_touched"] and p["git_trace"])
    out.append(("filet", f"filet mémoire au démarrage exact : {n_exp} attendu(s) (session précédente sans mise à jour "
                f"de HANDOFF.md ET avec trace git), {len(fp)} faux positif(s), {len(fn)} faux négatif(s)"
                + (f" — {other} session(s) sans /handoff mais HANDOFF.md mis à jour autrement (/feature-done, édition "
                   f"à la main) : pas de filet, voulu (passation documentée)" if other else "")
                + (f" — FP {fp[:5]} FN {fn[:5]}" if fp or fn else "")
                + (f" — filet écrit à tort/manquant au SessionEnd : s{src[:5]}" if src else ""),
                not fp and not fn and not src))
    filets = [(p, c) for p, c in pairs if c["filet"]]
    badq = [c["i"] for p, c in filets if not snapshot_ok(c["filet_text"], p["humans"])]
    out.append(("filet-msg", f"filet = les 3 derniers messages HUMAINS de la session précédente (ni puce vide, ni /exit) : "
                f"{len(filets) - len(badq)}/{len(filets)}", not badq))
    stop_bad, n_age, n_size, maxs = [], 0, 0, 0
    for r in recs:
        kinds = [k for st in r["stops"] for k in st["got"]]
        n_age += kinds.count("age")
        n_size += kinds.count("size")
        maxs = max(maxs, len(kinds))
        if kinds.count("age") > 1 or kinds.count("size") > 1 or any(
                (st["exp"] or None) != (st["got"][0] if st["got"] else None) or len(st["got"]) > 1 for st in r["stops"]):
            stop_bad.append(r["i"])
    nstops = sum(len(r["stops"]) for r in recs)
    out.append(("stop", f"hook Stop conforme : {nstops} appels, {n_age} rappel(s) d'âge + {n_size} de taille, "
                f"≤ 1×/session et par motif (max {maxs}/session), uniquement si HANDOFF > 24 h ET arbre modifié"
                + (f" — écarts s{stop_bad[:5]}" if stop_bad else ""), not stop_bad))
    injs = [x for x in sim.inj if x["session"] in idx]
    code = [x for x in injs if x["chars"]]
    big = [x for x in injs if x["chars"] > PRETOOL_MAX_CHARS]
    dup = [x for x in injs if x["chars"] and not x["first"]]
    noncode = [x for x in injs if x["chars"] and x["kind"] == "methode"]
    out.append(("pretool", f"PreToolUse : {len(code)} injections sur {len(injs)} Edit/Write, ≤ {PRETOOL_MAX_CHARS} chars "
                f"(max {max((x['chars'] for x in injs), default=0)}), ≤ 1×/(session, fichier), rien sur .claude/"
                + (f" — {len(big)} trop grosses, {len(dup)} répétées, {len(noncode)} sur .claude/" if big or dup or noncode else ""),
                not (big or dup or noncode)))
    exp_n = sum(x["expect_n"] for x in injs)
    miss = [(x["session"], x["rel"], sorted(x["missing"])) for x in injs if x["missing"]]
    extra = [(x["session"], x["rel"], sorted(x["extra"])) for x in injs if x["extra"]]
    per_g = {}
    for sess, rel, ns in miss:
        for n in ns:
            per_g.setdefault(n, []).append((sess, rel))
    out.append(("gotchas", f"gotchas ciblés : chaque gotcha injecté à la 1re édition de son fichier/dossier "
                f"(transversal : de tout fichier de code) ({exp_n - sum(len(m[2]) for m in miss)}/{exp_n}), "
                f"aucun gotcha d'un autre fichier, aucun Globaux sur un .json/.md"
                + (" — manqués : " + " ; ".join(
                    f"G{n} ×{len(v)}" + (" (transversal sans chemin)" if sim.gotchas[n]["target"] is None
                                         else f" (`{sim.gotchas[n]['target']}`)") + f", dès s{v[0][0]} `{v[0][1]}`"
                    for n, v in sorted(per_g.items(), key=lambda kv: -len(kv[1]))) if miss else "")
                + (f" — en trop {extra[:3]}" if extra else ""),
                not miss and not extra))
    hl = [r["handoff_lines"] for r in recs if r["did_handoff"]]
    if hl:
        op, n, fits = handoff_target()
        out.append(("handoff30", f"HANDOFF {op} {n} lignes après chaque /handoff (cible de /handoff Étape 3 ; "
                    f"{len(hl)} /handoff, max {max(hl)} lignes)", all(fits(x) for x in hl)))
        out.append(("handoff-stack", f"HANDOFF réécrit, jamais empilé : {min(hl)}–{max(hl)} lignes sur {len(hl)} /handoff, "
                    f"{max(r['handoff_bytes'] for r in recs)} octets max", max(hl) - min(hl) <= 8))
    b = [r["budget"] for r in recs]
    b5 = b[min(4, len(b) - 1)]
    out.append(("budget", f"budget auto-chargé borné : max {kt(max(b))} ≤ {kt(BUDGET_MAX_TOK)}, dérive session 5 → fin "
                f"{b[-1] - b5:+d} tok ≤ {kt(BUDGET_DRIFT_TOK)}", max(b) <= BUDGET_MAX_TOK and b[-1] - b5 <= BUDGET_DRIFT_TOK))
    comps = [cp for r in recs for cp in r["compactions"]]
    out.append(("compact", f"compaction (PreCompact → SessionStart compact) : snapshot ré-injecté avec les messages humains "
                f"({sum(cp['ok'] for cp in comps)}/{len(comps)})", all(cp["ok"] for cp in comps)))
    last = recs[-1]
    by_sid = {r["sid"]: r["date"] for r in sim.recs}
    stale = [f for f in last["cache_files"]
             if (m := re.search(r"([0-9a-f]{8}-[0-9a-f-]{27})", f)) and m.group(1) in by_sid
             and last["date"] - by_sid[m.group(1)] >= timedelta(days=CACHE_DAYS)]
    orphans = [f for f in last["cache_files"] if f.startswith("session-start-")]
    out.append(("cache", f"cache par-session purgé : {len(last['cache_files'])} fichiers à la fin, 0 de plus de "
                f"{CACHE_DAYS} j, 0 marqueur de début orphelin" + (f" — {stale[:2]} {orphans[:2]}" if stale or orphans else ""),
                not stale and not orphans))
    return out


def metrics(sim, recs):
    idx = {r["i"] for r in recs}
    pairs = list(zip(recs, recs[1:]))
    injs = [x for x in sim.inj if x["session"] in idx]
    stops = [sum(len(st["got"]) for st in r["stops"]) for r in recs]
    snaps = [(c["filet_text"], p["humans"]) for p, c in pairs if c["filet"]]
    comps = [cp for r in recs for cp in r["compactions"]]
    return {
        "filet": sum(c["filet"] for _, c in pairs),
        "fp": sum(1 for p, c in pairs if c["filet"] and not p["expected_net"]),
        "fn": sum(1 for p, c in pairs if p["expected_net"] and not c["filet"]),
        "expected": sum(1 for p, _ in pairs if p["expected_net"]),
        "stop_mean": sum(stops) / max(1, len(stops)), "stop_max": max(stops, default=0),
        "pretool_session": sum(x["chars"] for x in injs) / max(1, len(recs)),
        "pretool_max": max((x["chars"] for x in injs), default=0),
        "snap_bad": sum(1 for t, h in snaps if not snapshot_ok(t, h)) + sum(1 for cp in comps if not cp["ok"]),
        "snap_n": len(snaps) + len(comps),
        "startup_chars": sum(r["startup_chars"] for r in recs) / max(1, len(recs)),
        "budget_final": recs[-1]["budget"], "budget_max": max(r["budget"] for r in recs),
        "handoff_lines": recs[-1]["handoff_lines_end"], "handoff_bytes": recs[-1]["handoff_bytes"],
        "placeholder": sum(1 for x in injs if x["placeholder"]),
        "handoffs": sum(r["did_handoff"] for r in recs),
        "no_handoff_touched": sum(1 for r in recs if not r["did_handoff"] and r["handoff_touched"] and r["git_trace"]),
    }


def checkpoints(n):
    pts = [1] + list(range(10, n + 1, 10))
    return pts if pts[-1] == n else pts + [n]


def print_crash(sim):
    ok(f"{sim.label} : simulation sans exception"
       + (f" — {sim.error.strip().splitlines()[-1][:200]}" if sim.error else ""), not sim.error)
    if sim.error:
        print("\n".join("      " + l for l in sim.error.strip().splitlines()[-12:]))


# ── Constats automatiques (template) ─────────────────────────────────────────────────────────

def handoff_target():
    """Cible de taille déclarée par /handoff Étape 3 (« réécriture complète, < 30 lignes » ou « ≤ 40 lignes ») :
    le harness vérifie ce que le template promet, pas un chiffre figé ici."""
    m = re.search(r"réécriture complète\*\*, ([<≤]) (\d+) lignes", read(ROOT / ".claude/skills/handoff/SKILL.md"))
    op, n = (m.group(1), int(m.group(2))) if m else ("≤", HANDOFF_MAX_LINES)
    return op, n, (lambda lines: lines < n) if op == "<" else (lambda lines: lines <= n)


def handoff_format_lines():
    sk = read(ROOT / ".claude/skills/handoff/SKILL.md")
    m = re.search(r"## Étape 3 .*?```markdown\n(.*?)\n```", sk, re.S)
    return len(m.group(1).split("\n")) if m else None, len(read(ROOT / ".claude/docs/HANDOFF.md").rstrip("\n").split("\n"))


# ── Programme principal ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions", type=int, default=None, help="sessions des scénarios A et B (défaut 60)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--quick", action="store_true", help="mode CI : A 20, B 20, C 8 sessions × 3 profils")
    ap.add_argument("--report", default=None, help="écrit un rapport Markdown")
    ap.add_argument("--keep", action="store_true", help="garde le dossier temporaire (projets, transcripts)")
    ap.add_argument("--scenarios", default="A,B,C")
    ap.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 4))
    a = ap.parse_args()
    n_ab = a.sessions or (20 if a.quick else 60)
    n_c = min(8 if a.quick else 20, n_ab) if a.sessions else (8 if a.quick else 20)
    profiles_c = QUICK_PROFILES if a.quick else PROFILES
    want = {x.strip().upper() for x in a.scenarios.split(",") if x.strip()}
    t_start = time.time()

    tags = sh(["git", "-C", ROOT, "tag", "--list", "v*"], check=False).stdout.split()
    if ({"A", "B"} & want) and OLD_TAG not in tags:
        print(f"⚠️  tag {OLD_TAG} absent (checkout sans historique ?) — en CI : actions/checkout fetch-depth: 0")
        return 1
    head = sh(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], check=False).stdout.strip()
    dirty = bool(sh(["git", "-C", ROOT, "status", "--porcelain", "--untracked-files=no"], check=False).stdout.strip())
    target_v = read(ROOT / ".claude/template-version").strip()
    tmp = Path(tempfile.mkdtemp(prefix="sim-growth-"))
    print(f"🧪 sim-growth — seed {a.seed} · A/B {n_ab} sessions · C {n_c} sessions × {len(profiles_c)} profils · "
          f"template {head}{' (arbre modifié)' if dirty else ''} = {target_v} · {a.jobs} en parallèle")

    sims = {}
    try:
        jobs = []
        if "A" in want:
            plan_a = build_plan(f"{a.seed}-A", n_ab, "py")
            sims["A-old"] = Sim("A-old", f"A {OLD_TAG}", OLD_TAG, "python-app", plan_a, tmp, a.seed)
            sims["A-new"] = Sim("A-new", f"A {target_v}", "WORKTREE", "python-app", plan_a, tmp, a.seed)
            jobs += [(sims["A-old"], None), (sims["A-new"], None)]
        if "B" in want:
            sims["B"] = Sim("B", f"B {OLD_TAG}→{target_v}", OLD_TAG, "python-app", build_plan(f"{a.seed}-B", n_ab, "py"), tmp, a.seed)
            jobs.append((sims["B"], n_ab // 2))
        if "C" in want:
            for p in profiles_c:
                sims[f"C-{p}"] = Sim(f"C-{p}", f"C {p}", "WORKTREE", p, build_plan(f"{a.seed}-C-{p}", n_c, layout_of(p)), tmp, a.seed)
                jobs.append((sims[f"C-{p}"], None))
        jobs.sort(key=lambda j: -len(j[0].plan))   # les plus longs d'abord
        with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
            list(ex.map(lambda j: j[0].run(j[1]), jobs))
        report = Report(a, n_ab, n_c, head, dirty, target_v)

        if "A" in want:
            scenario_a(sims["A-old"], sims["A-new"], n_ab, target_v, report)
        if "B" in want:
            scenario_b(sims["B"], n_ab, target_v, report)
        if "C" in want:
            scenario_c([sims[f"C-{p}"] for p in profiles_c], n_c, report)
        constats(sims, report)
        dur = time.time() - t_start
        print(f"\n⏱️  {dur:.0f} s (projets : " + ", ".join(f"{s.key} {s.elapsed:.0f} s" for s in sims.values()) + ")")
        if a.report:
            report.write(Path(a.report), dur)
            print(f"📝 rapport : {a.report}")
    finally:
        if a.keep:
            print(f"📂 conservé : {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'🎉 SIM OK' if FAIL == 0 else '💥 ÉCHECS'} — {PASS} pass, {FAIL} fail")
    return 0 if FAIL == 0 else 1


def scenario_a(old, new, n, target_v, report):
    section(f"A. progression — même croissance seedée, {n} sessions (python-app) : {OLD_TAG} vs {target_v}")
    print_crash(old)
    print_crash(new)
    if old.error or new.error or not old.recs or not new.recs:
        return
    pts = checkpoints(min(len(old.recs), len(new.recs)))
    info("budget auto-chargé (tok est.) aux sessions " + " / ".join(str(p) for p in pts) + " :")
    for s in (old, new):
        print(f"      {s.label[2:]:<7} " + " / ".join(kt(s.recs[p - 1]["budget"]) for p in pts)
              + f"   (init {kt(s.init_budget)}, max {kt(max(r['budget'] for r in s.recs))})")
    mo, mn = metrics(old, old.recs), metrics(new, new.recs)
    for s, m in ((old, mo), (new, mn)):
        info(f"{s.label} : HANDOFF final {m['handoff_lines']} lignes / {m['handoff_bytes'] // 1024} Ko · "
             f"filet injecté {m['filet']}× ({m['fp']} faux positifs, {m['fn']} faux négatifs, {m['expected']} attendus) · "
             f"Stop {m['stop_mean']:.1f} rappel/session (max {m['stop_max']}) · PreToolUse {m['pretool_session'] / 1000:.1f}k "
             f"chars/session (max {m['pretool_max']}/injection) · snapshots sans messages humains {m['snap_bad']}/{m['snap_n']}")
    report.a = {"old": old, "new": new, "pts": pts, "mo": mo, "mn": mn}
    for key, label, cond in invariants(new, new.recs):
        ok(f"{target_v} : {label}", cond)
    ok(f"{OLD_TAG} plus lourd que {target_v} (progression) : budget final {kt(mo['budget_final'])} > "
       f"{kt(mn['budget_final'])} tok (×{mo['budget_final'] / max(1, mn['budget_final']):.1f})",
       mo["budget_final"] > mn["budget_final"])


def scenario_b(sim, n, target_v, report):
    section(f"B. upgrade à mi-vie — {OLD_TAG} {n // 2} sessions → upgrade.py --to WORKTREE → {target_v} {n - n // 2} sessions")
    print_crash(sim)
    u = sim.upgrade
    if not u:
        ok("upgrade exécuté", False)
        return
    rep = u["report"]
    post = [r for r in sim.recs if r["v15"]]
    pre = [r for r in sim.recs if not r["v15"]]
    acts = {}
    for x in rep.get("actions", []):
        acts[x["action"]] = acts.get(x["action"], 0) + 1
    info(f"upgrade.py : code {u['rc']} en {u['seconds']:.1f} s · statut « {rep.get('status')} » · actions "
         + ", ".join(f"{k} {v}" for k, v in sorted(acts.items())) + " · migrations : "
         + " | ".join(m[:90] for m in rep.get("migrations", [])))
    b_end = post[-1]["budget"] if post else None
    info(f"budget : fin v1.3.3 {kt(u['budget_before'])} → après upgrade {kt(u['budget_after'])} → fin "
         f"{kt(b_end) if b_end is not None else '?'} (max post-upgrade {kt(max(r['budget'] for r in post)) if post else '?'})")
    bf, af = u["before"], u["after"]
    end = sim.content()
    rows = [("journal (entrées)", len(bf["journal_handoff"] | bf["journal_file"]),
             f"{len(af['journal_file'])} dans HANDOFF-journal.md, {len(af['journal_handoff'])} dans HANDOFF.md",
             len(end["journal_handoff"] | end["journal_file"])),
            ("gotchas", len(bf["gotchas_codemap"] | bf["gotchas_file"]),
             f"{len(af['gotchas_file'])} dans code-map-gotchas.md, {len(af['gotchas_codemap'])} dans code-map.md",
             len(end["gotchas_codemap"] | end["gotchas_file"])),
            ("sections datées", len(bf["stack_handoff"] | bf["stack_file"]),
             f"{len(af['stack_handoff'])} dans HANDOFF.md (hors § Journal : non migrées), {len(af['stack_file'])} dans le journal",
             f"{len(end['stack_handoff'] | end['stack_file'])} ({len(end['stack_file'])} archivées dans le journal)"),
            ("règles de couplage", len(bf["coupling"]), len(af["coupling"]), len(end["coupling"])),
            ("specs", len(bf["specs"]), len(af["specs"]), len(end["specs"])),
            ("ADR", len(bf["adrs"]), len(af["adrs"]), len(end["adrs"])),
            ("leçons", len(bf["lecons"]), len(af["lecons"]), len(end["lecons"])),
            ("idées", len(bf["idees"]), len(af["idees"]), len(end["idees"]))]
    for name, b, a_, e in rows:
        info(f"{name:<19} avant {b:>3} · après upgrade {a_} · fin {e}")
    report.b = {"sim": sim, "u": u, "rows": rows, "post": post, "pre": pre, "end": end}
    ok(f"upgrade.py : code 0, aucun conflit (projet personnalisé sans conflit délibéré)"
       + (f" — code {u['rc']}, conflits {rep.get('conflicts')} {rep.get('error', '')[:200]}" if u["rc"] or rep.get("conflicts") else ""),
       u["rc"] == 0 and not rep.get("conflicts"))
    ok(f"personnalisations conservées : allow Bash(make:*) {'✓' if u['allow_kept'] else '✗'}, ligne maison "
       f"git-workflow {'✓' if u['line_kept'] else '✗'}, skill deploy-client {'✓' if u['skill_kept'] else '✗'}",
       u["allow_kept"] and u["line_kept"] and u["skill_kept"] and u["anchor_found"])
    ok(f"projet en {target_v} après upgrade (template-version = {u['version_after']})", u["version_after"] == target_v)
    jb = bf["journal_handoff"] | bf["journal_file"]
    gb = bf["gotchas_codemap"] | bf["gotchas_file"]
    lost = {k: sorted(set(bf[k]) - set(af[k])) for k in ("coupling", "specs", "adrs", "lecons", "idees")}
    ok(f"migration : les {len(jb)} entrées du journal sorties de HANDOFF.md vers HANDOFF-journal.md, aucune perdue",
       jb and jb <= af["journal_file"] and not af["journal_handoff"])
    ok(f"migration : les {len(gb)} gotchas sortis de code-map.md (auto-chargée) vers code-map-gotchas.md, aucun perdu",
       gb and gb <= af["gotchas_file"] and not af["gotchas_codemap"])
    ok("specs, ADR, leçons, idées, règles de couplage et section maison de HANDOFF intacts"
       + (f" — perdus {lost}" if any(lost.values()) else ""), not any(lost.values()) and af["note"] == bf["note"])
    before_lines = [l.strip() for n in ("HANDOFF.md", "code-map.md") for l in u["docs_before"][n].split("\n") if l.strip()]
    after_set = {l.strip() for t in u["docs_after"].values() for l in t.split("\n")}
    replaced = re.compile(r"^(## Journal|## Gotchas \(pièges|> 🧑‍🤝‍🧑 \*\*Multi-agent)")
    gone = [l for l in before_lines if l not in after_set and not replaced.match(l)]
    ok(f"migration sans perte de texte : chaque ligne de HANDOFF.md et code-map.md d'avant l'upgrade se retrouve "
       f"dans HANDOFF(-journal).md / code-map(-gotchas).md" + (f" — {len(gone)} ligne(s) disparue(s), ex. « {gone[0][:110]} »" if gone else ""),
       not gone)
    report.b["gone"] = gone
    sb = bf["stack_handoff"] | bf["stack_file"]
    if sb:
        ok(f"sections datées empilées par /handoff < 1.4 ({len(sb)}) : jamais perdues — restées dans HANDOFF.md par la "
           f"migration, archivées dans HANDOFF-journal.md par le 1er /handoff {target_v}",
           sb <= (af["stack_handoff"] | af["stack_file"]) and (not post or not any(r["did_handoff"] for r in post)
                                                              or (sb <= end["stack_file"] and not end["stack_handoff"])))
    ok(f"budget après upgrade < {kt(BUDGET_AFTER_UPGRADE_TOK)} : {kt(u['budget_before'])} → {kt(u['budget_after'])} tok",
       0 < u["budget_after"] < BUDGET_AFTER_UPGRADE_TOK)
    ok(f"fin de vie : tout le contenu d'avant l'upgrade est toujours là après {len(post)} sessions en {target_v}",
       jb <= (end["journal_handoff"] | end["journal_file"]) and gb <= (end["gotchas_codemap"] | end["gotchas_file"])
       and set(bf["specs"]) <= set(end["specs"]) and set(bf["adrs"]) <= set(end["adrs"])
       and bf["lecons"] <= end["lecons"] and set(bf["idees"]) <= set(end["idees"]) and end["note"])
    if post:
        first = post[0]
        info(f"1re session post-upgrade : filet hérité de {OLD_TAG} (SessionEnd écrivait à chaque fin) "
             f"{'INJECTÉ' if first['filet'] else 'consommé sans injection'} — hors oracle (transition)")
        for key, label, cond in invariants(sim, post):
            ok(f"post-upgrade : {label}", cond)


def scenario_c(sims, n, report):
    section(f"C. profils — {n} sessions à 1.5.0 sur {len(sims)} profils")
    report.c = []
    for sim in sims:
        print_crash(sim)
        if sim.error or not sim.recs:
            continue
        inv = {k: (label, cond) for k, label, cond in invariants(sim, sim.recs)}
        m = metrics(sim, sim.recs)
        present = set(sim.init_skills)
        absent_kinds = sorted({k for k, sk in ACTION_SKILL.items() if sk not in present})
        now_docs = sim.doc_hashes()
        changed = {rel for rel in set(sim.init_docs) | set(now_docs) if sim.init_docs.get(rel) != now_docs.get(rel)}
        allowed = [re.compile(p) for sk, pats in SKILL_DOCS.items() if sk in present for p in pats]
        rogue = sorted(rel for rel in changed if not any(p.search(rel) for p in allowed))
        info(f"{sim.profile:<15} budget {kt(sim.init_budget)} → {kt(m['budget_final'])} (max {kt(m['budget_max'])}) · "
             f"{len(sim.calls)} appels de hooks · filet {m['filet']}× (FP {m['fp']}, FN {m['fn']}) · "
             f"Stop max {m['stop_max']}/session · PreToolUse max {m['pretool_max']} chars · actions sautées "
             + (", ".join(f"{k} ×{v}" for k, v in sorted(sim.skipped.items())) or "aucune")
             + (" · sans objet " + ", ".join(f"{k} ×{v}" for k, v in sorted(sim.noops.items())) if sim.noops else ""))
        report.c.append({"sim": sim, "m": m, "rogue": rogue, "absent": absent_kinds})
        core = ("filet", "filet-msg", "stop", "pretool", "gotchas", "compact", "cache")
        bad = [k for k in core if k in inv and not inv[k][1]]
        ok(f"{sim.profile} : {inv['hooks'][0]}", inv["hooks"][1])
        ok(f"{sim.profile} : invariants 1.5.0 (filet exact, Stop 1×/session, PreToolUse borné et ciblé, compaction, cache)"
           + (" — KO : " + " | ".join(inv[k][0] for k in bad) if bad else ""), not bad)
        if "handoff30" in inv:
            ok(f"{sim.profile} : {inv['handoff30'][0]}", inv["handoff30"][1])
        ok(f"{sim.profile} : {inv['budget'][0]}", inv["budget"][1])
        skipped_ok = all(sim.skipped.get(k, 0) == 0 for k in ACTION_SKILL if k not in absent_kinds)
        ok(f"{sim.profile} : actions sans skill sautées ({', '.join(absent_kinds) or 'aucune'}) et aucun doc écrit par un "
           f"skill absent" + (f" — docs hors périmètre : {rogue[:4]}" if rogue else ""), not rogue and skipped_ok)


def constats(sims, report):
    """Constats sur le template lui-même (pas des contrôles : à trancher par le mainteneur)."""
    section("Constats (template)")
    lines = []
    fmt, tpl = handoff_format_lines()
    op, n, fits = handoff_target()
    if fmt and not (fits(fmt) and fits(tpl)):
        lines.append(f"format strict de /handoff (Étape 3) = {fmt} lignes, gabarit HANDOFF.md post-init = {tpl} lignes "
                     f"— au-delà de la cible « {op} {n} lignes » du même skill")
    v15 = [s for s in sims.values() if s.recs]
    ph = sum(1 for s in v15 for x in s.inj if x["v15"] and x["placeholder"])
    tot = sum(1 for s in v15 for x in s.inj if x["v15"] and x["chars"])
    if ph:
        lines.append(f"{ph}/{tot} injections PreToolUse (1.5.0) portent un gotcha du GABARIT non rempli "
                     f"(« ⚠️ {{{{Piège transversal…}}}} » sous « Globaux ») : injecté à chaque 1re édition de chaque fichier "
                     f"tant que la section Globaux du gabarit n'est pas remplie (le hook ne saute pas les {{{{…}}}})")
    js = [(s.profile, g["target"]) for s in v15 for n, g in s.gotchas.items()
          if g["target"] and not g["target"].endswith("/") and not is_code(g["target"])
          and any(x["rel"] == g["target"] and x["session"] > g["session"] and x["v15"] for x in s.inj)
          and not any(n in x["got"] for x in s.inj if x["rel"] == g["target"])]
    if js:
        lines.append(f"{len(js)} gotcha(s) ciblant un fichier .json ({js[0][0]}, ex. `{js[0][1]}`) ne sont JAMAIS injectés : "
                     f"le hook PreToolUse exclut .json (config) — or en automation-n8n les workflows sont le code")
    v15_sids = {r["sid"] for s in v15 for r in s.recs if r["v15"] and r["compactions"]}
    marks = sum(1 for s in v15 if s.tmp.is_dir() for f in s.tmp.glob("claude-handoff-marker-*.json")
                if f.stem.replace("claude-handoff-marker-", "") in v15_sids)
    if marks:
        lines.append(f"{marks} marqueur(s) claude-handoff-marker-<session>.json laissés dans $TMPDIR par PreCompact "
                     f"(1 par session compactée, jamais purgés — hors .claude/.cache)")
    summ = sum(1 for s in v15 for p, c in zip(s.recs, s.recs[1:]) if c["v15"] and c["filet"]
               and "This session is being continued" in c["filet_text"])
    if summ:
        lines.append(f"{summ} filet(s) listent le RÉSUMÉ de compaction (« This session is being continued… ») parmi les "
                     f"« derniers messages user » : snapshot_common.human_text ne filtre pas les entrées isCompactSummary")
    b = getattr(report, "b", None)
    if b:
        u = b["u"]
        gtext = u["docs_after"].get("code-map-gotchas.md", "")
        heads = {n: h for h, body in split_h2(gtext) for n in map(int, GOTCHA_RE.findall(body))}
        dead = [n for n, g in b["sim"].gotchas.items() if g["target"] is None and n in heads
                and not re.search(r"globa", heads[n] or "", re.I) and g["session"] <= len(b["pre"])]
        if dead:
            lines.append(f"upgrade {OLD_TAG} → 1.5.0 : {len(dead)} gotcha(s) transversal(aux) sans chemin (G{dead[0]}, injecté "
                         f"à CHAQUE édition par le hook {OLD_TAG}) migré(s) sous « {(heads[dead[0]] or '')[3:40]} » de "
                         f"code-map-gotchas.md → plus jamais injecté(s) (seules les entrées sous « Globaux » le sont sans chemin)")
    if b and b.get("gone"):
        lines.append(f"upgrade {OLD_TAG} → 1.5.0 : {len(b['gone'])} ligne(s) de doc perdue(s) par la migration, ex. "
                     f"« {b['gone'][0][:100]} »")
    for l in lines:
        print(f"  ⚠️  {l}")
    if not lines:
        print("  (aucun)")
    report.constats = lines


# ── Rapport Markdown ─────────────────────────────────────────────────────────────────────────

class Report:
    def __init__(self, a, n_ab, n_c, head, dirty, target_v):
        self.args, self.n_ab, self.n_c, self.head, self.dirty, self.v = a, n_ab, n_c, head, dirty, target_v
        self.a = self.b = None
        self.c, self.constats = [], []

    def write(self, path: Path, dur: float):
        L = [f"# Simulation de croissance — claude-Setup {self.v}", "",
             f"- Généré le {datetime.now():%Y-%m-%d %H:%M} · seed {self.args.seed} · "
             f"{'mode --quick' if self.args.quick else 'run complet'} · durée {dur:.0f} s",
             f"- Template : `{self.head}`{' (arbre de travail modifié)' if self.dirty else ''} · A/B : {self.n_ab} sessions · "
             f"C : {self.n_c} sessions/profil",
             f"- Résultat : **{PASS} pass, {FAIL} fail**", ""]
        if self.a:
            old, new, mo, mn = self.a["old"], self.a["new"], self.a["mo"], self.a["mn"]
            L += [f"## A. Progression {OLD_TAG} → {self.v} (python-app, croissance identique)", "",
                  f"| session | budget {OLD_TAG} | budget {self.v} | HANDOFF lignes {OLD_TAG} | HANDOFF lignes {self.v} "
                  f"| code-map tok {OLD_TAG} | code-map tok {self.v} |", "|---:|---:|---:|---:|---:|---:|---:|"]
            n = min(len(old.recs), len(new.recs))
            for p in sorted(set([1] + list(range(5, n + 1, 5)) + [n])):
                ro, rn = old.recs[p - 1], new.recs[p - 1]
                L.append(f"| {p} | {ro['budget']} | {rn['budget']} | {ro['handoff_lines_end']} | {rn['handoff_lines_end']} "
                         f"| {ro['codemap_tok']} | {rn['codemap_tok']} |")
            L += ["", f"| métrique | {OLD_TAG} | {self.v} |", "|---|---:|---:|",
                  f"| budget init → final (max) | {old.init_budget} → {mo['budget_final']} ({mo['budget_max']}) "
                  f"| {new.init_budget} → {mn['budget_final']} ({mn['budget_max']}) |",
                  f"| /handoff joués | {mo['handoffs']} | {mn['handoffs']} |",
                  f"| filet injecté au démarrage | {mo['filet']} | {mn['filet']} |",
                  f"| … dont faux positifs / faux négatifs (attendus : {mn['expected']}) | {mo['fp']} / {mo['fn']} | {mn['fp']} / {mn['fn']} |",
                  f"| sessions sans /handoff, HANDOFF mis à jour autrement (/feature-done, à la main) → pas de filet (voulu) "
                  f"| {mo['no_handoff_touched']} | {mn['no_handoff_touched']} |",
                  f"| snapshots (filet + compaction) sans les messages humains | {mo['snap_bad']}/{mo['snap_n']} | {mn['snap_bad']}/{mn['snap_n']} |",
                  f"| rappels Stop par session (moy / max) | {mo['stop_mean']:.2f} / {mo['stop_max']} | {mn['stop_mean']:.2f} / {mn['stop_max']} |",
                  f"| PreToolUse : chars injectés par session (moy) / max par injection | {mo['pretool_session']:.0f} / {mo['pretool_max']} "
                  f"| {mn['pretool_session']:.0f} / {mn['pretool_max']} |",
                  f"| SessionStart : chars injectés par démarrage (moy) | {mo['startup_chars']:.0f} | {mn['startup_chars']:.0f} |",
                  f"| HANDOFF final (lignes / octets) | {mo['handoff_lines']} / {mo['handoff_bytes']} | {mn['handoff_lines']} / {mn['handoff_bytes']} |", ""]
        if self.b:
            u, rows, post = self.b["u"], self.b["rows"], self.b["post"]
            rep = u["report"]
            L += [f"## B. Upgrade à mi-vie ({OLD_TAG} → {self.v})", "",
                  f"- upgrade.py : code {u['rc']}, statut « {rep.get('status')} », {u['seconds']:.1f} s, conflits : "
                  f"{rep.get('conflicts') or 'aucun'}",
                  *[f"- migration : {m}" for m in rep.get("migrations", [])],
                  f"- budget : fin {OLD_TAG} **{u['budget_before']}** → après upgrade **{u['budget_after']}** → fin "
                  f"**{post[-1]['budget'] if post else '?'}** tok (max post-upgrade {max((r['budget'] for r in post), default=0)})",
                  f"- personnalisations : allow `Bash(make:*)` {'✅' if u['allow_kept'] else '❌'} · ligne maison git-workflow "
                  f"{'✅' if u['line_kept'] else '❌'} · skill `deploy-client` {'✅' if u['skill_kept'] else '❌'}", "",
                  "| contenu | avant upgrade | après upgrade | fin |", "|---|---:|---|---:|"]
            L += [f"| {n} | {b} | {a_} | {e} |" for n, b, a_, e in rows]
            if self.b.get("gone"):
                L += ["", "Lignes de doc disparues pendant la migration :", *[f"- `{g[:140]}`" for g in self.b["gone"][:10]]]
            L += ["", "| session | version | budget | HANDOFF lignes | filet | rappels Stop |", "|---:|---|---:|---:|---|---:|"]
            for r in self.b["sim"].recs:
                if r["i"] in (1, len(self.b["pre"]), len(self.b["pre"]) + 1) or r["i"] % 5 == 0 or r is self.b["sim"].recs[-1]:
                    L.append(f"| {r['i']} | {r['version']} | {r['budget']} | {r['handoff_lines_end']} | "
                             f"{'oui' if r['filet'] else ''} | {sum(len(s['got']) for s in r['stops'])} |")
            L.append("")
        if self.c:
            L += ["## C. Profils (1.5.0)", "",
                  "| profil | skills | budget init → fin (max) | appels hooks | filet (FP/FN) | Stop max/session | "
                  "PreToolUse max chars | HANDOFF max lignes | actions sautées |", "|---|---:|---|---:|---|---:|---:|---:|---|"]
            for c in self.c:
                s, m = c["sim"], c["m"]
                hl = max((r["handoff_lines"] for r in s.recs if r["did_handoff"]), default=0)
                L.append(f"| {s.profile} | {len(s.init_skills)} | {s.init_budget} → {m['budget_final']} ({m['budget_max']}) | "
                         f"{len(s.calls)} | {m['filet']} ({m['fp']}/{m['fn']}) | {m['stop_max']} | {m['pretool_max']} | {hl} | "
                         + (", ".join(f"{k} ×{v}" for k, v in sorted(s.skipped.items())) or "—") + " |")
            L.append("")
        L += ["## Contrôles", ""]
        cur = None
        for sec, good, label in CHECKS:
            if sec != cur:
                L += ["", f"**{sec}**", ""]
                cur = sec
            L.append(f"- {'✅' if good else '❌'} {label}")
        L += ["", "## Constats (template)", ""] + [f"- ⚠️ {c}" for c in self.constats] + ([] if self.constats else ["- aucun"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
