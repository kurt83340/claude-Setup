#!/usr/bin/env python3
"""
SessionStart hook — deux flux d'injection selon la source :

1. source="compact" (matcher compact) — comportement historique :
   re-inject le snapshot pré-compaction pointé par le marker
   /tmp/claude-handoff-marker-<session_id>.json (écrit par precompact-snapshot-handoff.py).

2. source="startup" (matcher startup) — filet « n'oublie rien » :
   si .claude/.cache/session-end-snapshot.md (écrit par sessionend-snapshot.py) est
   PLUS FRAIS que .claude/docs/HANDOFF.md → la session précédente s'est fermée sans
   /handoff → injecter le snapshot. Dans TOUS les cas, le consommer (unlink) pour ne
   jamais réinjecter un filet périmé.

Payload sans champ "source" (schéma historique) → flux marker (1).
Stdout = injecté automatiquement dans le contexte par Claude Code (documenté).
"""

import json
import os
import sys
import tempfile
from pathlib import Path


def inject_compact_marker(data) -> None:
    """Flux 1 : ré-injection post-compaction via marker par-session."""
    session_id = data.get("session_id", "unknown")

    marker_path = Path(tempfile.gettempdir()) / f"claude-handoff-marker-{session_id}.json"
    if not marker_path.exists():
        # Pas de marker → pas de re-injection nécessaire (session normale)
        return

    try:
        marker = json.loads(marker_path.read_text())
    except Exception:
        return

    if not marker.get("needs_inject"):
        return

    snapshot_path = Path(marker.get("snapshot_path", ""))
    if not snapshot_path.exists():
        return

    try:
        snapshot = snapshot_path.read_text(encoding="utf-8")
    except Exception:
        return
    if not snapshot:
        return

    # Stdout direct = injection auto par Claude Code dans le contexte
    print(
        f"""## 🔄 Re-injection post-compaction

Le contexte vient d'être compacté. Voici le snapshot HANDOFF.md récent pour reprendre où on en était :

{snapshot[:5000]}

→ Lis aussi `.claude/docs/HANDOFF.md` pour l'historique complet si besoin.
→ Continue ton travail. Si tu finis ta session, lance `/handoff` pour propre snapshot."""
    )

    # Flip needs_inject à false
    marker["needs_inject"] = False
    marker_path.write_text(json.dumps(marker))


def inject_session_end_net(data) -> None:
    """Flux 2 : filet fin de session — injecte si plus frais que HANDOFF.md, puis consomme."""
    cwd = data.get("cwd", os.getcwd())
    snap = Path(cwd) / ".claude" / ".cache" / "session-end-snapshot.md"
    if not snap.exists():
        return

    handoff = Path(cwd) / ".claude" / "docs" / "HANDOFF.md"
    try:
        snap_mtime = snap.stat().st_mtime
        handoff_mtime = handoff.stat().st_mtime if handoff.exists() else 0.0
        if snap_mtime > handoff_mtime:
            content = snap.read_text(encoding="utf-8")[:5000]
            print(
                f"""## ⚠️ Filet mémoire — session précédente fermée sans /handoff

Le snapshot auto de fin de session est plus récent que `.claude/docs/HANDOFF.md` (probable /handoff oublié) :

{content}

→ Croise avec `.claude/docs/HANDOFF.md` (possiblement stale) et propose à l'utilisateur de consolider via `/handoff`."""
            )
    except Exception:
        pass
    finally:
        # Consommé dans tous les cas : un filet ne se réinjecte jamais deux fois,
        # et si HANDOFF est plus frais c'est que /handoff a déjà capturé l'état.
        try:
            snap.unlink()
        except OSError:
            pass


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if data.get("source") == "startup":
        inject_session_end_net(data)
    else:
        inject_compact_marker(data)

    sys.exit(0)


if __name__ == "__main__":
    main()
