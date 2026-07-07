# Audit multi-agent & qualité — 2026-06-28

> ⚠️ **Document historique** (audit du 2026-06-28) : plusieurs conclusions sont périmées — not. « skills-n8n/ à garder » (remplacé en v0.14.0 par le plugin officiel [czlonkowski/n8n-skills](https://github.com/czlonkowski/n8n-skills)) et les chemins `EXAMPLES/skills-*`. État actuel → [.github/CHANGELOG.md](../.github/CHANGELOG.md).

> Complément à `AUDIT-2026-06-28.md` (qui couvrait coût-contexte/bloat/keys mais **excluait explicitement le multi-agent**). Méthode : fan-out de 4 agents (docs / skills+agent / hooks+settings / méta-alignement), chemins & lignes vérifiés.

## Verdict

« Trop de fichiers ? » → pas en **nombre**, mais en **(1) duplication** (même contenu dit 3-4×, déjà en drift), **(2) cérémonie par défaut** au lieu d'opt-in, **(3) stubs livrés** contre la règle « create-on-demand ». Le gain n'est pas de supprimer des fichiers mais de **single-sourcer**.

## 6 thèmes (convergence des 4 agents)

1. **Source-de-vérité multiple** — gouvernance dite 3× (`rules/template-maintenance.md` _(rule auto-chargée)_ + `USAGE.md` + `STRUCTURE.md`) ; inventaire skills en 4 endroits (déjà drifté : `/idee` manque dans une table de template-maintenance) ; format HANDOFF ×4 ; table macro↔micro ×3 ; convention diagrammes ×4. → 1 source canonique, le reste linke + check CI.
2. **Ré-implémentation skills/agent** — `doc-maintainer` redéfinit /handoff,/feature-done,/doc-health,/pivot au lieu de les invoquer ; /feature-done duplique /adr ; /pivot drifté (9 vs « 7 » étapes). → l'agent orchestre.
3. **« Générique » = faux (Python/n8n-couplé)** — settings.json (alembic/pytest/ruff/mypy), rules/\* 100% Python, `.env.example` hardcodé ACME, /db-migration = pur Alembic. → scoper rules `paths:`, /db-migration→EXAMPLES, génériciser, ou renommer honnêtement.
4. **Stubs livrés ⟂ create-on-demand** — GLOSSARY/RUNBOOK/ACCESS livrés vides (RUNBOOK dit « à créer au 1er déploiement, pas avant »). → retirer, laisser les triggers créer.
5. **Cérémonie = plancher** — ≥8 docs design/feature à ~100% ; `conception/tasks.md` (figé) vs `ROADMAP` (vivant) se recouvrent. → défaut maigre, cérémonie opt-in.
6. **Sécurité multi-agent (bloquant)** — `HANDOFF.md` partagé écrasé par /handoff ; snapshot cross-contamination HIGH (un seul `.cache/`) ; courses numérotation specs/ADR ; Stop ×N. → worktree-per-teammate corrige le gros ; lead-owns-HANDOFF + numérotation par-lead + Stop lead-only + snapshot par-session pour le reste ; **rôle teammate manquant**.

## Bugs / sécu / refs mortes

- `trigger` toujours « auto » (lu dans `tool_input`, vide en PreCompact ; **le test confirme le bug**).
- `[ ]→[~]` jamais posé → greps `/feature-done`+`/doc-health` échouent en silence.
- `/doc-health` étape 11 (link-check) = `:` (stub mort).
- `script-jetable` garde `/lecon` mais supprime sa cible `/adr` + `lecons.md`.
- Code mort (assistant msgs jamais rendus) + placeholders TODO réinjectés ; `grep -P` GNU-only ; MultiEdit ignoré ; frontmatter `arguments:`/`memory:` non reconnus ; frontmatter ADR parasite sur `template-maintenance.md`.
- 🔓 `ACCESS.md` (coffre creds) lisible (`Read(./**)`) ; denies poreux ; `.growth-suggestions.md` livré avec cruft d'une autre machine (`/home/jleroy/…`).
- 🔗 `/push-n8n` inexistant ; rsync exclut `EXAMPLES/` mais des fichiers copiés y réfèrent (liens morts + init n8n = 0 skill) ; `EXAMPLES/acme/_CLAUDE.md` = 19 `@`-imports (vs règle phare des 3).

## EXAMPLES

`skills-n8n/` → garder (dép. fonctionnelle de l'init). `acme/` (40 fichiers) → slim ou cut (drifté + duplique les exemples inline de `STRUCTURE.md`).

## Plan priorisé

| Tier                         | Actions                                                                                                                                                                 |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0** (avant agent-teams)   | snapshot par-session · stratégie HANDOFF d'équipe (lead-owns) · numérotation par-lead · Stop lead-only · rôle teammate (A)                                              |
| **P1** (dédup/allègement)    | single-source gouvernance + inventaire skills (+CI) · agent invoque les skills · retirer stubs · dé-Python-ifier/scoper rules · /db-migration→EXAMPLES                  |
| **P2** (correctness/hygiène) | bug trigger · transition `[~]` · stub doc-health · jetable · code mort/TODO · grep -P · sécu ACCESS+denies · gitignore growth-suggestions · refs mortes · trancher acme |

_Statut : application en cours (déléguée par zone à 4 agents + lead). Voir CHANGELOG._
