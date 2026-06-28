# Plan d'exécution MVP — Sync ERP→Notion

> ⚠️ **Stable après design** — ne modifier que sur **pivot majeur** (sinon désync avec ROADMAP).
> Pour le status courant et les blockers → voir [../ROADMAP.md](../ROADMAP.md) (dashboard vivant).
>
> Ce fichier = **plan figé** décidé en phase conception : sous-phases, estimations, DoD.
> ROADMAP.md = **état dynamique** mis à jour à chaque session.

**Cible MVP :** 2026-06-15 (présentation board ACME)
**Effort estimé total :** ~15 jours-homme
**Pattern mirror :** ce fichier = équivalent macro de `specs/00X-feature/tasks.md`

---

## Phase 1 — MVP

### 1.1 — Composants (specs détaillées)

| Spec                                                 | Estimation | Status (voir ROADMAP) |
| ---------------------------------------------------- | ---------- | --------------------- |
| [001-erp-connector](specs/001-erp-connector/spec.md) | 5 jours    | En cours              |
| [002-notion-writer](specs/002-notion-writer/spec.md) | 4 jours    | Pas commencé          |
| [003-error-handler](specs/003-error-handler/spec.md) | 3 jours    | Pas commencé          |

### 1.2 — Intégration (assemblage)

- Workflow n8n complet (chaîne 001 + 002 + 003) — **2 jours**
- Tests E2E sur env staging ACME — **1 jour**
- Documentation flow dans [ARCHITECTURE.md section 4](ARCHITECTURE.md) — **0.5 jour**

### 1.3 — Validation & GO prod

- Smoke tests staging 48h sans erreur
- Demo Marie (prévu 2026-06-08)
- Validation écrite Paul IT
- GO prod board ACME (2026-06-15)

### DoD Phase 1 (contrat figé)

- [ ] Toutes specs Phase 1 livrées (DoD individuelles cochées dans `specs/00X/tasks.md`)
- [ ] Workflow tourne stable 48h en staging
- [ ] Marie + Paul ont validé par mail
- [ ] [../RUNBOOK.md](../RUNBOOK.md) créé avec procédures rollback
- [ ] [../CHANGELOG.md](../CHANGELOG.md) à jour avec entry de release
- [ ] Coverage tests >= 80% sur tous les modules Python
- [ ] Sentry recoit bien les erreurs en staging

---

## Phase 2 — Robustesse (post-MVP, cible juillet 2026)

### 2.1 — Observabilité

- Dashboard Grafana sur métriques n8n
- Migration Sentry → compte ACME (vu en validation archi)

### 2.2 — Performance

- 005-backfill-historique : sync initial des commandes < 30j
- 006-rate-limit-handling : gestion fine des 429 Notion

### DoD Phase 2

- [ ] Dashboard Grafana fonctionnel sur prod
- [ ] Backfill 30 jours réussi sans erreur
- [ ] Documentation MAJ

---

## Phase 3 — Évolutions v2 (backlog, à discuter avec Marie)

- Sync inverse Notion → SAP (voir [../idees/2026-05-22-sync-inverse.md](../idees/2026-05-22-sync-inverse.md))
- Notifications Slack (voir [../idees/2026-05-23-slack-alerts.md](../idees/2026-05-23-slack-alerts.md))
- Multi-tenant si autres clients adoptent

### DoD Phase 3

À définir lors du re-cadrage (impact PRD significatif).

---

## Cross-references

- **Status courant :** [../ROADMAP.md](../ROADMAP.md)
- **PRD source :** [PRD.md](PRD.md)
- **Architecture :** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Specs détaillées par feature :** [specs/](specs/)

## En cas de pivot

Si la hiérarchie demande un changement majeur :

1. Réunion documentée dans [../cadrage/reunions/YYYY-MM-DD-pivot.md](../cadrage/reunions/)
2. Update [../cadrage/README.md](../cadrage/README.md) (nouvelle direction)
3. Append section datée dans [research.md](research.md)
4. Bumper [PRD.md](PRD.md) (v1.0 → v2.0)
5. **Refonte de CE FICHIER** : nouvelle section `## Phase X — Refonte v2` avec son propre DoD
6. ROADMAP synchronisé avec les nouvelles phases
