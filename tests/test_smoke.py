"""Smoke test (claude-03): the combined app imports and serves /dashboard and /call without any API call."""
from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from src.app import MOUNTED, app


class SmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_lists_mounted_packages(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ok")
        self.assertTrue(body["mounted"].get("voice"))
        self.assertTrue(body["mounted"].get("dashboard"))
        self.assertEqual(MOUNTED, body["mounted"])

    def test_root_redirects_to_dashboard(self):
        res = self.client.get("/", follow_redirects=False)
        self.assertIn(res.status_code, (302, 307))
        self.assertEqual(res.headers["location"], "/dashboard")

    def test_three_demo_pages_answer_200(self):
        """/call, /live and /dashboard must never 404 (the builders' parts are mounted)."""
        for path in ("/call", "/live", "/dashboard"):
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, path)
            self.assertIn("text/html", res.headers["content-type"], path)

    def test_dashboard_200(self):
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers["content-type"])
        self.assertIn("DawnDispatch", res.text)

    def test_call_200_start_page(self):
        res = self.client.get("/call")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers["content-type"])
        self.assertIn("Start call", res.text)
        self.assertIn("/ws/chat", res.text)
        self.assertIn("/static/js/synced-audio-player.js", res.text)
        self.assertNotIn("ringtone", res.text.lower())
        self.assertIn("navigator.wakeLock.request('screen')", res.text)

    def test_call_sim_200_and_its_backend_routes(self):
        res = self.client.get("/call/sim")
        self.assertEqual(res.status_code, 200)
        self.assertIn("/static/voice/call.js", res.text)
        if MOUNTED.get("voice_sim"):
            from src.app import _existing_paths

            self.assertIn("/ws/call", _existing_paths())
            self.assertIn("/api/end_call", _existing_paths())

    def test_dashboard_api_routes_are_included(self):
        for path in ("/api/graph/before", "/api/graph/after", "/api/actions", "/api/transcript", "/api/agenda"):
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, path)

    def test_call_agenda_and_state(self):
        res = self.client.get("/api/call/agenda")
        self.assertEqual(res.status_code, 200)
        items = res.json()["items"]
        self.assertEqual(len(items), 4)
        self.assertTrue(any(it["is_irreversible"] for it in items))
        res = self.client.get("/api/call/state")
        self.assertEqual(res.status_code, 200)
        self.assertIn("call", res.json())

    def test_collisions_between_standalone_apps_are_resolved(self):
        """src/voice/app.py and src/dashboard/app.py both define /, /api/agenda, /api/transcript, /api/health
        and mount /static and /assets. The combined app keeps exactly one of each."""
        from src.app import _existing_paths

        paths = _existing_paths()
        for path in ("/", "/api/health", "/api/agenda", "/api/transcript", "/call", "/dashboard"):
            self.assertIn(path, paths, path)
        # one route object per colliding path (no shadowed duplicates in the route table)
        flat = []
        for r in app.routes:
            inner = getattr(r, "original_router", None)
            flat.extend(inner.routes if inner is not None else [r])
        for path in ("/", "/api/health", "/api/agenda", "/api/transcript", "/call"):
            self.assertEqual(sum(1 for r in flat if getattr(r, "path", None) == path), 1, path)
        mounts = [getattr(r, "path", None) for r in app.routes if type(r).__name__ == "Mount"]
        self.assertEqual(mounts.count("/static"), 1)
        self.assertEqual(mounts.count("/assets"), 1)
        # winners: our redirect + health, the dashboard's agenda/transcript, our /call
        self.assertIn("mounted", self.client.get("/api/health").json())
        self.assertEqual(self.client.get("/", follow_redirects=False).headers["location"], "/dashboard")
        self.assertIsInstance(self.client.get("/api/agenda").json(), list)
        self.assertIn("turns", self.client.get("/api/transcript").json())
        self.assertEqual(self.client.get("/static/style.css").status_code, 200)      # dashboard css
        self.assertEqual(self.client.get("/static/voice/call.css").status_code, 200)  # voice css
        self.assertEqual(self.client.get("/assets/titelbild-v3.jpg").status_code, 200)

    def test_ws_chat_route_exists(self):
        # FastAPI >= 0.143 keeps included routers nested, so look at the voice router itself
        from src.voice.server import router as voice_router

        self.assertIn("/ws/chat", {getattr(r, "path", None) for r in voice_router.routes})
        self.assertTrue(MOUNTED.get("voice"))
        # and the HTTP side of the same router is reachable through the app
        self.assertEqual(self.client.get("/api/audio-config").status_code, 200)

    def test_static_mounts(self):
        self.assertEqual(self.client.get("/static/style.css").status_code, 200)
        self.assertEqual(self.client.get("/static/voice/call.css").status_code, 200)
        if MOUNTED.get("gradbot_js"):
            self.assertEqual(self.client.get("/static/js/synced-audio-player.js").status_code, 200)


if __name__ == "__main__":
    unittest.main()
