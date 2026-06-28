---
name: init-from-template
description: Initialise un nouveau projet depuis le template. Pose 10 questions via AskUserQuestion (PROJECT_NAME, type projet, CLIENT_NAME, décideur, commandes stack), substitue les CORE placeholders (UPPER_SNAKE) via render.py, puis lance cleanup-for-type.py adapté au type (script-jetable -80%, automation-n8n copie les skills n8n depuis EXAMPLES, etc.). À invoquer UNE FOIS après copy du template.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(find:*), Bash(sed:*), Bash(python3:*), Bash(chmod:*), Bash(git init:*), Bash(git add:*), Bash(git commit:*), AskUserQuestion
disable-model-invocation: true
---

# /init-from-template — Initialise un nouveau projet

Ton rôle : transformer ce template (placeholders `{{...}}`) en un projet concret rempli avec les infos du user.

## Étape 0 — Prérequis techniques (CRITIQUE)

Avant toute substitution, vérifier/exécuter :

```bash
# 1. Hooks exécutables (sinon settings.json hooks bloquent)
chmod +x .claude/hooks/*.py .claude/hooks/*.sh

# 2. Git init pour rollback possible si l'init foire
[ ! -d .git ] && git init && git add . && git commit -m "chore: snapshot pre-init"

# 3. Vérifier Python 3 dispo (pour les hooks + script render.py)
python3 --version || { echo "❌ Python 3 requis"; exit 1; }
```

Si l'un échoue → STOP, demander au user de fixer.

## Convention placeholders : CORE vs CONTENT

Le template a 2 types de placeholders :

| Type        | Format                      | Qui substitue  | Exemples                              |
| ----------- | --------------------------- | -------------- | ------------------------------------- |
| **CORE**    | `{{COMPOUND_UPPER_SNAKE}}`  | `/init` (auto) | `{{PROJECT_NAME}}`, `{{CLIENT_NAME}}` |
| **CONTENT** | `{{texte libre minuscule}}` | User (au fil)  | `{{seuil}}`, `{{situation actuelle}}` |

Pattern CORE : au moins 2 lettres maj + underscore + 2+ chars (élimine `{{X}}`, `{{URL}}`, `{{ADR}}` qui sont CONTENT).

**Ce skill ne traite QUE les CORE.** Les CONTENT sont laissés intacts — l'user les remplit au fur et à mesure du projet.

## Étape 1 — Collecter les infos via AskUserQuestion

Pose les questions suivantes (groupées en 2-3 batches AskUserQuestion) :

### Batch 1 — Identité projet

1. **`{{PROJECT_NAME}}`** : nom du projet (ex: "Sync ERP Notion", "Dashboard Sales")
2. **`{{PROJECT_FOLDER}}`** : nom du dossier (kebab-case, ex: "sync-erp-notion")
3. **Type de projet** :
   - `automation-n8n` (n8n + helpers)
   - `python-app` (Python pur, FastAPI, scripts)
   - `web-app` (Next.js, React, etc.)
   - `bdd-migration` (migration BDD)
   - `script-jetable` (one-shot, doc minimaliste)
   - `other` (libre)

### Batch 2 — Contexte client

4. **`{{CLIENT_NAME}}`** : nom du client / projet (ex: "ACME Corp")
5. **`{{NOM_DECIDEUR}}`** + **`{{EMAIL_DECIDEUR}}`** : décideur principal
6. **`{{TON_NOM}}`** + **`{{TON_EMAIL}}`** : toi (dev owner technique)

### Batch 3 — Commandes de la stack

7. **`{{COMMANDE_INSTALL}}`** : ex. `uv pip install -r requirements.txt` / `npm install` / `pnpm install`
8. **`{{COMMANDE_TESTS}}`** : ex. `pytest` / `npm test` / `vitest`
9. **`{{COMMANDE_RUN}}`** : ex. `python src/main.py` / `npm run dev`

## Étape 2 — Substituer les placeholders CORE via render.py

Écris les réponses dans un `vars.json` temporaire, puis lance le script bundled :

```bash
# 1. Créer vars.json depuis les réponses
cat > /tmp/init-vars.json <<'EOF'
{
  "PROJECT_NAME": "...",
  "PROJECT_FOLDER": "...",
  "CLIENT_NAME": "...",
  "NOM_DECIDEUR": "...",
  "EMAIL_DECIDEUR": "...",
  "TON_NOM": "...",
  "TON_EMAIL": "...",
  "COMMANDE_INSTALL": "...",
  "COMMANDE_TESTS": "...",
  "COMMANDE_RUN": "..."
}
EOF

# 2. Lancer render.py (depuis racine projet)
python3 .claude/skills/init-from-template/scripts/render.py \
  --vars /tmp/init-vars.json

# 3. Vérifier qu'aucun CORE ne reste
python3 .claude/skills/init-from-template/scripts/render.py --check
```

Le script :

- Substitue UNIQUEMENT les placeholders CORE (UPPER_SNAKE) → ne touche pas aux CONTENT
- Affiche en fin de run : `✅ Tous les CORE substitués` + nombre de CONTENT restants (normal)
- `--check` retourne `1` (exit code) si des CORE manquent → utilisable en CI

## Étape 3 — Adapter selon le type de projet (cleanup automatique)

Lance le script bundled qui supprime/garde les bons fichiers selon le type :

```bash
# Toujours faire un dry-run d'abord pour montrer au user
python3 .claude/skills/init-from-template/scripts/cleanup-for-type.py \
  --type <type> --dry-run

# Si user OK → exécuter pour de vrai
python3 .claude/skills/init-from-template/scripts/cleanup-for-type.py \
  --type <type>
```

### Profils

| Type             | Impact   | Ce que ça supprime                                                                                                                                                                                     |
| ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `script-jetable` | **-80%** | Toute la conception (PRD/ARCHITECTURE/specs), ADRs, idees, ROADMAP, RUNBOOK, code-map, stack, ACCESS, lecons, GLOSSARY, hooks code, agents, skills overkill (adr/codemap/doc-health/feature-done/spec) |
| `automation-n8n` | léger    | `.claude/docs/RUNBOOK.md` (créé post-prod uniquement)                                                                                                                                                  |
| `python-app`     | moyen    | `workflows/`, `.claude/docs/RUNBOOK.md`                                                                                                                                                                |
| `web-app`        | moyen    | `workflows/`, `.claude/docs/RUNBOOK.md`                                                                                                                                                                |
| `bdd-migration`  | léger    | `workflows/`                                                                                                                                                                                           |

### Garantie : skills "vitaux" toujours conservés

Pour TOUS les types : `handoff`, `lecon`, `init-from-template` restent disponibles.

### Si le user n'est pas sûr du type

Choisir `automation-n8n` ou `python-app` par défaut (impact léger, peut affiner ensuite avec un autre cleanup).

## Étape 4 — Cleanup final

Demander au user pour chaque action (optionnel) :

1. **`EXAMPLES/`** — supprimer du projet actif ?
   - ⚠️ **Note** : `EXAMPLES/` n'est PAS copié par défaut si tu utilises `rsync --exclude='EXAMPLES/'` (recommandé). Si tu l'as copié, tu peux le retirer :

   ```bash
   rm -rf EXAMPLES/  # uniquement si présent et user confirme
   ```

   - Le dossier `EXAMPLES/` reste dans le template source pour servir de référence aux futurs projets.

2. **Skill `init-from-template`** — supprimer ? (utilisé qu'une fois mais peut servir pour re-init partielle / re-cleanup type)
   ```bash
   rm -rf .claude/skills/init-from-template/  # uniquement si user confirme
   ```
3. **Commit initial** :
   ```bash
   git add .
   git commit -m "feat: init projet <nom> depuis template"
   ```
4. Confirmer à l'user : "Projet initialisé. Prochaines étapes : remplir `.claude/docs/cadrage/README.md` (verbatim demande client) + planifier le kickoff."

## Sortie attendue

```
✅ Template initialisé pour {{PROJECT_NAME}}
   - 23 fichiers personnalisés
   - 487 placeholders remplacés
   - EXAMPLES/ supprimé
   - Git commit initial créé

🚀 Prochaines étapes :
   1. Remplir .claude/docs/cadrage/README.md avec verbatim demande client
   2. Lancer kickoff → archiver compte-rendu dans cadrage/reunions/
   3. Quand brief mûr → .claude/docs/conception/PRD.md
```

## Notes techniques

- Si placeholder non rempli → laisser tel quel avec warning user
- Si projet `script-jetable` → confirmer avant de supprimer 80% des fichiers
- Toujours faire git commit AVANT toute substitution destructive (rollback possible)
