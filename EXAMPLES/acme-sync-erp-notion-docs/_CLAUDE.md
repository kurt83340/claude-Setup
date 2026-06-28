# Projet ACME — Sync ERP→Notion

Automatisation n8n + Python pour synchroniser les commandes SAP B1 → Notion DB ACME.

## 🧭 Comment vivre avec ce template

**Lis EN PREMIER** : @.claude/rules/template-maintenance.md
→ explique la structure, le workflow fin/début de session, quel skill/agent invoquer.

## Documentation projet

### 📥 Cadrage (capture initiale + évolutions/pivots)

- Synthèse cadrage : @.claude/docs/cadrage/README.md

### 🎨 Conception (design macro + micro)

- Research / brainstorm : @.claude/docs/conception/research.md
- Vision produit (PRD) : @.claude/docs/conception/PRD.md
- Architecture : @.claude/docs/conception/ARCHITECTURE.md
- Plan d'exécution MVP (figé) : @.claude/docs/conception/tasks.md
- Specs détaillées par feature : `.claude/docs/conception/specs/00X-feature/`

### 🔄 Vivants (lus/MAJ tous les jours)

- Roadmap : @.claude/docs/ROADMAP.md
- Reprise session : @.claude/docs/HANDOFF.md ⭐
- Accès requis : @.claude/docs/ACCESS.md
- Changelog : @.claude/docs/CHANGELOG.md
- Journal leçons : @.claude/docs/lecons.md
- **Code map** : @.claude/docs/code-map.md ⭐ (à lire AVANT d'éditer le code)
- **Stack technique** : @.claude/docs/stack.md (inventaire libs + services + LLM)

### 📚 Transversaux

- Décisions tech (ADR) : @.claude/docs/adr/
- Glossaire métier : @.claude/docs/GLOSSARY.md
- Procédures ops (post-prod) : @.claude/docs/RUNBOOK.md

## Conventions techniques

- Code style : @.claude/rules/code-style.md
- Tests : @.claude/rules/testing.md
- Git : @.claude/rules/git-workflow.md

## Skills projet (slash)

- `/n8n-push` → publish workflow n8n sur tenant ACME
- `/n8n-seed-db` → fixtures de test en local
- `/n8n-deploy` → push prod (migration BDD + workflow) — `disable-model-invocation: true`
- `/handoff` → update HANDOFF.md fin de session ⭐
- `/feature-done` → coche ROADMAP + entrée CHANGELOG après livraison

## Reminders critiques

- Credentials **JAMAIS** dans le repo (voir ACCESS.md pour le stockage)
- HANDOFF.md à update **à chaque fin de session** (via `/handoff`)
- Décision tech structurante → créer un ADR
