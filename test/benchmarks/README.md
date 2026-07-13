# Benchmarks comportementaux des skills

> Un SKILL.md est du **code d'instruction** → il se teste. Pattern emprunté aux
> `__benchmarks__/` de [Citadel](https://github.com/SethGammon/Citadel) (MIT), adapté à notre
> outillage 2-tiers : **structure vérifiée en CI** (`python3 test/test_skills.py` — sans LLM),
> **comportement joué en agentique** (`test/PROTOCOL-E2E.md` Phase B, sur un projet jetable,
> à chaque version majeure).

## Format d'un scénario — `test/benchmarks/<skill>/<cas>.md`

```markdown
---
name: <slug-du-cas>
skill: <nom du skill — doit être un dossier de .claude/skills/>
input: <ce qu'on demande dans la session de test (l'invocation + le contexte en 1 phrase)>
state: <préparation du jetable AVANT l'input — prose courte, reproductible>
assert-contains:
  - <fragment attendu dans la sortie OU les fichiers produits>
assert-not-contains:
  - <fragment interdit — crash, écrasement, placeholder résiduel…>
---

## Attendu

- <3 à 5 puces de comportement, chacune vérifiable par l'agent testeur>
```

## Conventions

- **1 fichier = 1 cas.** Nom du dossier = nom du skill (vérifié par `test_skills.py`).
- Couvrir en priorité : le **happy path** + 1 **cas limite** (état vide, placeholders
  résiduels, entrée ambiguë) — c'est le cas limite qui attrape les régressions.
- Les `assert-*` portent sur des **choses observables** (sortie affichée, contenu de fichier,
  `git status`) — jamais « l'agent a compris ».
- Un scénario qui teste un refus (le skill doit dire NON) est aussi précieux qu'un happy path
  (cf. `test/PROTOCOL-E2E.md` Phase E).

## Exécution (agentique — Phase B du protocole E2E)

Pour chaque scénario : préparer `state` sur le jetable → jouer `input` dans une session →
vérifier chaque `assert-contains`/`assert-not-contains` + les puces de « Attendu » →
verdict ✅/⚠️/❌ dans le rapport (gabarit en fin de PROTOCOL-E2E.md).
