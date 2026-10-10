"""Tests for examples/sample-project structure and completeness."""
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent.parent / "examples" / "sample-project"

def test_sample_project_structure():
    assert SAMPLE_DIR.is_dir(), "examples/sample-project directory must exist"
    
    # Required documentation and status files
    readme = SAMPLE_DIR / "README.md"
    stand = SAMPLE_DIR / "STAND.md"
    todo = SAMPLE_DIR / "TODO.md"
    changelog = SAMPLE_DIR / "CHANGELOG.md"
    commits = SAMPLE_DIR / "COMMITS.md"
    git_log = SAMPLE_DIR / "git-log.txt"

    for path in [readme, stand, todo, changelog, commits, git_log]:
        assert path.is_file(), f"{path.name} must exist"
        assert len(path.read_text(encoding="utf-8").strip()) > 50, f"{path.name} must not be empty"

def test_commits_count():
    git_log = SAMPLE_DIR / "git-log.txt"
    lines = [line for line in git_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 30, f"Expected at least 30 commits in git-log.txt, got {len(lines)}"

def test_sample_project_python_syntax():
    src_dir = SAMPLE_DIR / "src" / "paypulse"
    assert (src_dir / "__init__.py").is_file()
    assert (src_dir / "webhooks.py").is_file()
    assert (src_dir / "ledger.py").is_file()
    assert (src_dir / "config.py").is_file()
    assert (src_dir / "main.py").is_file()

def test_sample_project_init_script():
    init_script = SAMPLE_DIR / "init_repo.sh"
    assert init_script.is_file()
    assert init_script.stat().st_mode & 0o111, "init_repo.sh must be executable"
