"""dawn/from_repo.py: a valid dawn/prompt.txt from any git repo, with Gemini mocked (no network, no keys)."""
from __future__ import annotations

import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from dawn import from_repo

MODEL_REPLY = """**BRIEFING:**
Over the last days the team shipped the parser and fixed two bugs. 3 commits landed on main, one branch is open.

THREADS
Thread 1: Release 1.0: tag now, wait for the docs, or ship as beta.
Thread 2: Open branch feature/export: merge, review first, or drop it.
Thread 3: TODO list: the CSV import is still open.
Thread 4: README promises a web UI that does not exist yet.
Thread 5: Tests: 12 pass, the slow one could be skipped.

OPENING: Morning Alex, the parser landed last night and all twelve tests are green,
nice walk?
"""


def git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def make_repo(root: pathlib.Path) -> pathlib.Path:
    repo = root / "demo-repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "dev@example.com")
    git(repo, "config", "user.name", "Dev")
    (repo / "README.md").write_text("# Demo Repo\n\nA small parser library with a CLI.\n", encoding="utf-8")
    (repo / "TODO.md").write_text("- [ ] CSV import\n- [x] JSON export\n", encoding="utf-8")
    (repo / "CHANGELOG").write_text("1.0.0 - parser added\n", encoding="utf-8")
    (repo / "notes-private.txt").write_text("not a status file\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "feat(parser): first version")
    (repo / "parser.py").write_text("def parse(x):\n    return x\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "fix(parser): handle empty input")
    git(repo, "checkout", "-q", "-b", "feature/export")
    (repo / "export.py").write_text("print('export')\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "wip: export")
    git(repo, "checkout", "-q", "main")
    return repo


class CollectContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = make_repo(pathlib.Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_context_has_readme_commits_branches_and_status_files(self):
        parts = from_repo.collect_context(self.repo)
        text = from_repo.render_context(parts)
        self.assertIn("Name: demo-repo", text)
        self.assertIn("Current branch: main", text)
        self.assertIn("A small parser library", text)                 # README
        self.assertIn("fix(parser): handle empty input", text)        # commits
        self.assertIn("feat(parser): first version", text)
        self.assertIn("feature/export", text)                         # branches
        self.assertIn("### TODO.md", text)                            # status files
        self.assertIn("### CHANGELOG", text)
        self.assertNotIn("notes-private", text)
        self.assertNotIn("wip: export", parts["Last 30 commits (newest first)"])  # HEAD log excludes the branch

    def test_commit_limit_is_respected(self):
        for i in range(5):
            (self.repo / f"f{i}.txt").write_text("x", encoding="utf-8")
            git(self.repo, "add", ".")
            git(self.repo, "commit", "-q", "-m", f"chore: file {i}")
        parts = from_repo.collect_context(self.repo, commits=3)
        log = parts["Last 3 commits (newest first)"]
        self.assertEqual(len(log.splitlines()), 3)
        self.assertIn("chore: file 4", log)

    def test_resolve_repo_rejects_non_git_directory(self):
        with self.assertRaises(SystemExit):
            from_repo.resolve_repo(self.tmp.name)

    def test_resolve_repo_clones_urls_into_clone_dir(self):
        clones = pathlib.Path(self.tmp.name) / "clones"
        dest = from_repo.resolve_repo(f"file://{self.repo}", clone_dir=clones)
        self.assertEqual(dest, clones / "demo-repo")
        self.assertTrue((dest / "README.md").is_file())
        # second call updates instead of cloning again
        self.assertEqual(from_repo.resolve_repo(f"file://{self.repo}", clone_dir=clones), dest)


class PromptTest(unittest.TestCase):
    def test_parse_sections_tolerates_colons_and_markdown(self):
        s = from_repo.parse_sections(MODEL_REPLY)
        self.assertEqual(set(s), {"BRIEFING", "THREADS", "OPENING"})
        self.assertTrue(s["BRIEFING"].startswith("Over the last days"))
        self.assertEqual(len(s["THREADS"].splitlines()), 5)
        self.assertEqual(s["OPENING"], "Morning Alex, the parser landed last night and all twelve tests are green, nice walk?")

    def test_parse_sections_reports_missing_section(self):
        with self.assertRaises(ValueError) as cm:
            from_repo.parse_sections("BRIEFING\nsomething\n\nTHREADS\nthread\n")
        self.assertIn("OPENING", str(cm.exception))

    def test_compose_and_validate(self):
        text = from_repo.compose_prompt(from_repo.parse_sections(MODEL_REPLY), "Alex")
        self.assertEqual(from_repo.validate_prompt(text), [])
        self.assertIn("project agent of Alex's software project", text)
        self.assertNotIn("Philipp", text)
        self.assertTrue(text.endswith("nice walk?\n"))
        self.assertEqual(from_repo.validate_prompt("BRIEFING\nx\n"), ["rules block missing",
                                                                      "missing section(s): BRIEFING, THREADS, OPENING",
                                                                      "OPENING must be the last line, one spoken sentence"])

    def test_ask_gemini_needs_a_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as cm:
                from_repo.ask_gemini("hello")
        self.assertIn("GEMINI_API_KEY", str(cm.exception))


class MainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = make_repo(pathlib.Path(self.tmp.name))
        self.out = pathlib.Path(self.tmp.name) / "prompt.txt"

    def tearDown(self):
        self.tmp.cleanup()

    def test_main_writes_valid_prompt_with_mocked_gemini(self):
        asked: dict[str, str] = {}

        def fake_gemini(ask, model=None, timeout=120):
            asked["ask"], asked["model"] = ask, model
            return MODEL_REPLY

        with mock.patch.object(from_repo, "ask_gemini", side_effect=fake_gemini):
            rc = from_repo.main([str(self.repo), "--name", "Alex", "--out", str(self.out), "--model", "test-model"])
        self.assertEqual(rc, 0)
        self.assertEqual(asked["model"], "test-model")
        self.assertIn("open the call with Alex", asked["ask"])
        self.assertIn("fix(parser): handle empty input", asked["ask"])   # repo context reached the model
        text = self.out.read_text(encoding="utf-8")
        self.assertEqual(from_repo.validate_prompt(text), [])
        self.assertTrue(text.strip().endswith("nice walk?"))             # bridge reads the opening from the last line
        with mock.patch.object(from_repo, "PROMPT_PATH", self.out):
            from dawn import bridge
            self.assertEqual(bridge.load_opening(self.out),
                             "Morning Alex, the parser landed last night and all twelve tests are green, nice walk?")

    def test_main_rejects_garbage_from_the_model(self):
        with mock.patch.object(from_repo, "ask_gemini", return_value="Sorry, I cannot help with that."):
            rc = from_repo.main([str(self.repo), "--out", str(self.out)])
        self.assertEqual(rc, 2)
        self.assertFalse(self.out.exists())

    def test_dry_run_makes_no_api_call(self):
        with mock.patch.object(from_repo, "ask_gemini", side_effect=AssertionError("must not be called")):
            rc = from_repo.main([str(self.repo), "--dry-run", "--out", str(self.out)])
        self.assertEqual(rc, 0)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
