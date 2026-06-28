# Journal des leçons

> Sas entre observation et action. Tu notes ici ce que tu observes (bugs, patterns, alertes), tu décides ensuite quoi en faire.
> **Complémentaire à auto-memory** (qui tourne automatiquement) — ici c'est la **mémoire intentionnelle versionnée**.

## Statuts

- 🆕 `new` — observé, pas décidé
- 📜 `→ ADR-00XX` — promu en ADR structurant (lien)
- 🔧 `→ rule X` — promu en règle Claude (path)
- 🧠 `→ memory only` — laissé à auto-memory (Claude apprend seul, pas besoin de plus)
- ❌ `discarded` — pas pertinent finalement
- 📦 `archived` — fermé après promotion (gardé pour historique)

## Scopes (même conv que ADR)

`cadrage` | `mvp` | `feature-00X` | `infra` | `operations`

## Workflow

```
Tu codes, tu observes
     ↓
Append une entry ici (status 🆕 new) — 4 lignes max
     ↓
Review (hebdo, fin de feature, ou via /doc-health) :
  ├─► Décision structurante  → 📜 ADR
  ├─► Convention à appliquer  → 🔧 Rule
  ├─► Pattern technique mineur → 🧠 memory only
  └─► Pas pertinent           → ❌ discarded
     ↓
Update le status
     ↓
Archive 📦 au bout de N mois (entries promues stables)
```

---

## 2026-05-24 — Pagination SAP B1

**scope:** mvp | **status:** 🔧 → `.claude/rules/api-externe.md`

Bug : `SapClient.get_orders_since()` cassait sur > 20 commandes (SAP limite à 20 par défaut, paramètre `$top` à expliciter).
Solution : utiliser `@odata.nextLink` pour paginer automatiquement.
→ Promu en règle (pattern réutilisable pour toute API REST OData paginée).

## 2026-05-23 — SDK Python officiel SAP B1 abandonné

**scope:** mvp | **status:** 🧠 → memory only

Tenté `b1sl` (SDK Python communautaire). Pas maintenu depuis 2022, bugs sur les filtres OData (`$filter` mal sérialisé).
Décision : utiliser `httpx` directement avec wrapper maison.
→ Pas besoin d'ADR, mais Claude doit garder en tête : "SDK Python SAP B1 = pas fiable, partir sur httpx direct".

## 2026-05-23 — VPN ACME instable

**scope:** operations | **status:** 🆕 new

VPN ACME coupe sans préavis 1-2 fois/jour, bloque tests d'intégration.
À décider :

- Pattern de résilience automatique (reconnect + retry) ? → potentiel ADR-00XX si récurrent
- Juste mitigation locale (retry tenacity) ? → memory only suffit

→ À revoir après 1 semaine d'observations.

## 2026-05-22 — httpx vs requests

**scope:** mvp | **status:** 📜 → potentiel ADR-0007 si v2 confirme besoin async

Choix lib HTTP. `httpx` retenu vs `requests` car async-ready pour la v2.
Pas d'ADR créé maintenant : la décision n'est pas encore "structurante" (peut changer).
→ À promouvoir en ADR-0007 dès que v2 lance async pour de bon.

## 2026-05-22 — Ruff config 100 chars

**scope:** mvp | **status:** ❌ discarded

Initialement gênant que ruff casse les chaînes longues. Mais après config `line-length: 100` dans `pyproject.toml`, plus de souci.
→ Faux problème, juste paramétrage.
