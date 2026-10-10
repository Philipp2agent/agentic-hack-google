"""DawnDispatch live mission-control screen (/live) and its in-process event bus.

Contract: docs/LIVE-EVENTS.md. Owned by claude-04. Mounted from src/app.py via
``from src.live.router import router`` (try-import); the voice side publishes with
``from src.live.bus import publish``.
"""
