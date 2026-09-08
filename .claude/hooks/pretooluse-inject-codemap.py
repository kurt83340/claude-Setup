#!/usr/bin/env python3
"""
PreToolUse hook (matcher: "Edit|Write|MultiEdit") — réinjecte le NON-DÉDUCTIBLE avant une
édition de code, **sous budget** : une fois par session, ciblé par fichier.

Pourquoi : Claude retrouve seul le rôle/les imports/les tests d'un fichier (agentic search).
Ce qu'il NE PEUT PAS deviner : les *règles de couplage* (« ne jamais importer X »),
l'*intention* et les *gotchas*. C'est ça — et seulement ça — qu'on réinjecte.

Budget (v1.4.0 — mesuré 2026-09-08) : l'ancienne version réinjectait couplage + intention +
TOUS les gotchas (~2,2k tokens) à CHAQUE Edit/Write, et une injection reste dans le transcript
pour toute la session (vérifié via `claude -p --resume`) → 40 éditions ≈ 90k tokens. Maintenant :

  1. **Couplage + intention** (code-map.md, déjà auto-chargée au démarrage) : UNE fois par
     session — marker `.claude/.cache/codemap-injected-<session_id>.json`. Le hook SessionStart
     (source=compact) efface le marker → ré-armé après chaque compaction (là où le rappel compte).
  2. **Gotchas** : depuis `code-map-gotchas.md` (v1.4, non auto-chargé) — ou § Gotchas de
     code-map.md (projet < 1.4) — UNIQUEMENT les entrées qui ciblent le fichier édité :
     chemin / nom de fichier / dossier cité en backticks dans l'entrée (ou son heading `###`),
     plus les entrées sous un heading « Globaux ». Une fois par (session, fichier).

Trigger : avant chaque Edit/Write sur un fichier de code (src/, lib/, app/, tests/).
Input stdin : {"session_id": "...", "tool_name": "Edit"|"Write", "tool_input": {"file_path": "..."}, "cwd": "..."}
Output JSON : {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "..."}}
Non-bloquant : toute erreur → exit 0 silencieux.
"""

import json
import os
import re
import sys
from pathlib import Path

MAX_CHARS = 4000            # cap global de l'additionalContext (doc : 10k max)
MAX_GOTCHA_CHARS = 2500     # part réservée aux gotchas ciblés
COUPLING_TITLES = ["Règles de couplage", "Intention & décisions locales"]
CODE_DIRS = ["/src/", "/tests/", "/lib/", "/app/"]
NON_CODE_EXT = (".md", ".json", ".yaml", ".yml", ".toml")


def extract_section(text: str, title: str) -> str:
    """Capture « ## <title> … » jusqu'au prochain « ## » ou la fin."""
    m = re.search(rf"(##\s+{re.escape(title)}.*?)(?=\n##\s|\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def gotcha_entries(text: str):
    """Découpe un texte de gotchas en (heading_courant, entrée). Une entrée = un bullet
    (`- ` / `* ` / `⚠️`) + ses lignes de continuation indentées. Les headings `#`/`##`/`###`
    changent le groupe courant (un heading peut lui-même cibler un dossier/fichier)."""
    entries, heading, cur = [], "", []
    for line in text.split("\n"):
        if re.match(r"#{1,4} ", line):
            if cur:
                entries.append((heading, "\n".join(cur)))
                cur = []
            heading = line
            continue
        if re.match(r"\s*([-*]|⚠️)\s", line):
            if cur:
                entries.append((heading, "\n".join(cur)))
            cur = [line.rstrip()]
        elif cur and line.startswith((" ", "\t")) and line.strip():
            cur.append(line.rstrip())
        elif cur and not line.strip():
            entries.append((heading, "\n".join(cur)))
            cur = []
    if cur:
        entries.append((heading, "\n".join(cur)))
    return entries


def path_tokens(s: str):
    """Tokens en backticks qui ressemblent à un chemin ou un nom de fichier (`src/x/`, `x.py`)."""
    toks = re.findall(r"`([^`\n]+)`", s)
    return [t.strip() for t in toks if ("/" in t or "." in t) and " " not in t.strip()]


def targets_file(tokens, rel: str, name: str) -> bool:
    rel_n = rel.replace("\\", "/")
    for t in tokens:
        t = t.lstrip("./")
        if not t:
            continue
        if t == name or rel_n.endswith("/" + t) or rel_n == t or t in rel_n:
            return True
    return False


def heading_tokens(heading: str):
    """Un heading cible par backticks (`src/x/`) OU par token nu contenant un « / » (### src/jobs/)."""
    bare = [t for t in heading.lstrip("#").split() if "/" in t and "`" not in t]
    return path_tokens(heading) + bare


def targeted_gotchas(text: str, rel: str, name: str) -> str:
    out = []
    for heading, entry in gotcha_entries(text):
        if re.search(r"globa", heading, re.IGNORECASE):
            out.append(entry)
        elif targets_file(heading_tokens(heading) + path_tokens(entry), rel, name):
            out.append(entry)
    return "\n".join(out)


def load_marker(path: Path) -> dict:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(d, dict):
            d.setdefault("coupling", False)
            d.setdefault("files", [])
            return d
    except Exception:
        pass
    return {"coupling": False, "files": []}


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get("tool_name", "") not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)
    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)
    # Gate : seulement les fichiers de code (pas .md, pas config)
    if not any(seg in file_path for seg in CODE_DIRS) or file_path.endswith(NON_CODE_EXT):
        sys.exit(0)

    cwd = Path(data.get("cwd", os.getcwd()))
    docs = cwd / ".claude" / "docs"
    codemap = docs / "code-map.md"
    gotchas_file = docs / "code-map-gotchas.md"
    if not codemap.exists() and not gotchas_file.exists():
        sys.exit(0)

    try:
        rel = os.path.relpath(file_path, cwd).replace("\\", "/")
    except ValueError:
        rel = file_path
    name = Path(file_path).name
    session_id = re.sub(r"[^\w.-]", "_", str(data.get("session_id", "nosession")))
    marker_path = cwd / ".claude" / ".cache" / f"codemap-injected-{session_id}.json"
    marker = load_marker(marker_path)

    blocks = []
    try:
        codemap_text = codemap.read_text(encoding="utf-8") if codemap.exists() else ""
    except Exception:
        codemap_text = ""

    # 1. Couplage + intention : une fois par session (ré-armé après compaction)
    if not marker["coupling"] and codemap_text:
        coupling = "\n\n".join(s for s in (extract_section(codemap_text, t) for t in COUPLING_TITLES) if s)
        if coupling:
            blocks.append(coupling[: MAX_CHARS - MAX_GOTCHA_CHARS])
            marker["coupling"] = True

    # 2. Gotchas ciblés : une fois par (session, fichier)
    if rel not in marker["files"]:
        try:
            gsrc = gotchas_file.read_text(encoding="utf-8") if gotchas_file.exists() \
                else extract_section(codemap_text, "Gotchas")
        except Exception:
            gsrc = ""
        g = targeted_gotchas(gsrc, rel, name) if gsrc else ""
        if g:
            blocks.append("## Gotchas ciblant ce fichier\n\n" + g[:MAX_GOTCHA_CHARS])
        marker["files"].append(rel)

    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(json.dumps(marker), encoding="utf-8")
    except Exception:
        pass

    if not blocks:
        sys.exit(0)

    context = f"""## 🗺️  Code Map — contraintes à respecter pour ce fichier

Tu vas éditer `{rel}`. Ce que la code-map impose et que tu ne peux PAS deviner en lisant le code :

{chr(10).join(blocks)[:MAX_CHARS]}

⚠️  Respecte les **règles de couplage**. Le rôle du fichier, ses imports et ses tests :
retrouve-les directement dans le code (grep/lecture). (Injecté une fois par session — budget contexte.)"""

    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "additionalContext": context}}))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
