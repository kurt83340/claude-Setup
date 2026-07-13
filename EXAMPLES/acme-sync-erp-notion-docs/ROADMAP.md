# Roadmap — Sync ERP→Notion (DASHBOARD)

> **Vue dynamique** : status courant + blockers + ce qui bouge.
> **Plan figé** (sous-phases, estimations, DoD) → [conception/tasks.md](conception/tasks.md).
> MAJ à chaque session ou via `/feature-done`.

**Dernière MAJ :** 2026-05-24 (Julien)

## ✅ Phase 0 — Setup (livré 2026-05-22)

Cadrage + conception + setup local : tout OK.

## 🚧 Phase 1 — MVP (en cours, cible 2026-06-15)

**Plan détaillé :** [conception/tasks.md](conception/tasks.md) section Phase 1

### Composants

- [~] [001-erp-connector](specs/001-erp-connector/spec.md) — **EN COURS** 5/8 tasks ([détail](specs/001-erp-connector/tasks.md))
- [ ] [002-notion-writer](specs/002-notion-writer/spec.md) — spec écrite, 0/7 tasks
- [ ] [003-error-handler](specs/003-error-handler/spec.md) — spec écrite, 0/8 tasks

### Intégration

- [ ] Workflow n8n complet (assemble 001+002+003)
- [ ] Tests E2E staging
- [ ] Validation Marie + Paul → GO prod

### Risques courants

- ⏳ VPN ACME instable cette semaine → bloque tests E2E (voir [HANDOFF.md](HANDOFF.md))
- ⏳ Marie pas encore partagé la DB Notion (voir [ACCESS.md](ACCESS.md))

## 📋 Phase 2 — Robustesse (post-MVP)

Voir [conception/tasks.md](conception/tasks.md) section Phase 2.

- [ ] 004-monitoring-dashboard
- [ ] 005-backfill-historique
- [ ] 006-rate-limit-handling

## 💡 Backlog v2 (à discuter)

- Sync inverse (voir [idees/2026-05-22-sync-inverse.md](idees/2026-05-22-sync-inverse.md))
- Notifications Slack (voir [idees/2026-05-23-slack-alerts.md](idees/2026-05-23-slack-alerts.md))
- Multi-tenant

---

## Conventions

- `[ ]` = planifié, pas commencé
- `[~]` = en cours (mettre en **gras**)
- `[x]` = livré
- Numéro de spec continue (001 → 002 → 003 → …) — pas de reset entre phases
- Format `X/Y tasks` = compté depuis `specs/00X/tasks.md`
