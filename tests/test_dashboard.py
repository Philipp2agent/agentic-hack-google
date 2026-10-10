"""Unit and Integration Tests for DawnDispatch Web Dashboard."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from starlette.testclient import TestClient

from src.dashboard.app import app
from src.core.graph_engine import generate_and_save_graph_after


class TestDashboardApp(unittest.TestCase):
    """Test suite for FastAPI Dashboard application."""

    @classmethod
    def setUpClass(cls):
        cls.data_dir = Path("src/data")
        cls.backup_actions = cls.data_dir / "actions.json.test_bak"
        cls.backup_graph = cls.data_dir / "knowledge_graph_after.json.test_bak"
        if (cls.data_dir / "actions.json").exists():
            shutil.copy(cls.data_dir / "actions.json", cls.backup_actions)
        if (cls.data_dir / "knowledge_graph_after.json").exists():
            shutil.copy(cls.data_dir / "knowledge_graph_after.json", cls.backup_graph)

    @classmethod
    def tearDownClass(cls):
        if cls.backup_actions.exists():
            shutil.move(cls.backup_actions, cls.data_dir / "actions.json")
        if cls.backup_graph.exists():
            shutil.move(cls.backup_graph, cls.data_dir / "knowledge_graph_after.json")

    def setUp(self):
        self.client = TestClient(app)

    def test_root_redirect(self):
        """Test GET / redirects to /dashboard."""
        response = self.client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/dashboard")

    def test_dashboard_page(self):
        """Test GET /dashboard returns index.html."""
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("DawnDispatch", response.text)
        self.assertIn("svg-before", response.text)
        self.assertIn("svg-after", response.text)
        self.assertIn("Human Checkpoint", response.text)

    def test_dashboard_checkpoint_route(self):
        """Test GET /dashboard/checkpoint/{item_id} returns HTML interface."""
        response = self.client.get("/dashboard/checkpoint/agenda-02")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("DawnDispatch", response.text)

    def test_api_health(self):
        """Test GET /api/health."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("service", data)

    def test_api_graph_before(self):
        """Test GET /api/graph/before."""
        response = self.client.get("/api/graph/before")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("stage"), "BEFORE")
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreater(len(data["nodes"]), 0)

    def test_api_graph_after(self):
        """Test GET /api/graph/after."""
        response = self.client.get("/api/graph/after")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("stage"), "AFTER")
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertGreater(len(data["nodes"]), 0)

    def test_api_transcript(self):
        """Test GET /api/transcript."""
        response = self.client.get("/api/transcript")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("turns", data)
        self.assertGreater(len(data["turns"]), 0)
        first_turn = data["turns"][0]
        self.assertIn("speaker", first_turn)
        self.assertIn("text", first_turn)

    def test_api_actions(self):
        """Test GET /api/actions."""
        response = self.client.get("/api/actions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_api_static_files(self):
        """Test static files are served."""
        css_resp = self.client.get("/static/style.css")
        self.assertEqual(css_resp.status_code, 200)
        self.assertIn("DawnDispatch", css_resp.text)

        js_resp = self.client.get("/static/graph.js")
        self.assertEqual(js_resp.status_code, 200)
        self.assertIn("DawnDispatch", js_resp.text)

    def test_confirm_checkpoint_flow(self):
        """Test 1-click checkpoint confirmation."""
        # Check current actions
        actions = self.client.get("/api/actions").json()
        # Find or make a blocked action
        blocked_action = next((a for a in actions if a["status"] == "BLOCKED_ON_CHECKPOINT"), None)
        if blocked_action is None:
            # Revert one to blocked for test
            action_id = actions[0]["action_id"]
        else:
            action_id = blocked_action["action_id"]

        confirm_resp = self.client.post(f"/api/actions/{action_id}/confirm")
        self.assertEqual(confirm_resp.status_code, 200)
        result = confirm_resp.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["action"]["status"], "COMPLETED")
        self.assertTrue(result["action"]["artifacts"].get("checkpoint_confirmed"))

        # Verify through GET /api/actions
        updated_actions = self.client.get("/api/actions").json()
        updated = next(a for a in updated_actions if a["action_id"] == action_id)
        self.assertEqual(updated["status"], "COMPLETED")

    def test_confirm_invalid_checkpoint(self):
        """Test confirming a non-existent checkpoint returns 404."""
        response = self.client.post("/api/actions/nonexistent-action-999/confirm")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
