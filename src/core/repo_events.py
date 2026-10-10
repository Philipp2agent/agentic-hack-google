"""Repo Event Aggregator for DawnDispatch.

Extracts overnight swarm activities from Git commits, branch statuses,
and STAND.md, converting them into standardized OvernightEvent records.
"""

from pathlib import Path
import re
import subprocess
from typing import Sequence

from src.core.models import OvernightEvent, save_events, SeverityType


def _map_agent_id(author_name: str, author_email: str, message: str) -> str:
    combined = f"{author_name} {author_email} {message}".lower()
    for candidate in ("hack-chef", "hack-bau1", "hack-bau2", "hack-bau3", "hack-visual"):
        if candidate in combined:
            return candidate
    if "philipp" in combined:
        return "Philipp2agent"
    return "hack-swarm"


def _determine_severity(text: str) -> SeverityType:
    t = text.lower()
    if any(k in t for k in ("conflict", "error", "fail", "broken", "critical", "bug")):
        return "ERROR"
    if any(k in t for k in ("warning", "checkpoint", "irreversible", "wipe", "purge", "port", "blocked")):
        return "WARNING"
    return "INFO"


def _determine_proposed_action(title: str, severity: SeverityType) -> str:
    t = title.lower()
    if severity == "ERROR":
        return "Triage failure with lead and roll back or apply immediate fix"
    if severity == "WARNING":
        if "checkpoint" in t or "wipe" in t or "purge" in t:
            return "Hold for human checkpoint sign-off before proceeding"
        return "Review changes and approve deployment during morning commute"
    if "feat" in t or "update" in t or "add" in t:
        return "Proceed with integration into active pipeline"
    return "Review diff and proceed to next milestone"


def parse_git_commits(repo_dir: Path | str = ".", limit: int = 10) -> list[OvernightEvent]:
    """Parse recent git commits into OvernightEvent instances."""
    r_path = Path(repo_dir)
    cmd = [
        "git",
        "-C",
        str(r_path),
        "log",
        f"-n{limit}",
        "--pretty=format:%H%x09%h%x09%an%x09%ae%x09%s%x09%b%x1e",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        return []

    events: list[OvernightEvent] = []
    raw_records = res.stdout.strip().split("\x1e")

    for idx, rec in enumerate(raw_records, start=1):
        rec = rec.strip()
        if not rec:
            continue
        parts = rec.split("\t")
        if len(parts) < 5:
            continue
        _full_sha, short_sha, author_name, author_email, subject = parts[:5]
        body = parts[5].strip() if len(parts) > 5 else ""

        agent = _map_agent_id(author_name, author_email, f"{subject} {body}")
        severity = _determine_severity(f"{subject} {body}")
        proposed_action = _determine_proposed_action(subject, severity)

        details = body if body else f"Commit {short_sha} by {author_name}: {subject}"
        event = OvernightEvent(
            id=f"evt-{idx:03d}",
            source=f"git commit {short_sha}",
            agent_id=agent,
            title=subject,
            details=details,
            severity=severity,
            proposed_action=proposed_action,
        )
        events.append(event)

    return events


def check_stand_file(repo_dir: Path | str = ".") -> OvernightEvent | None:
    """Inspect STAND.md for open blockers, questions, or assignments."""
    stand_path = Path(repo_dir) / "STAND.md"
    if not stand_path.exists():
        return None
    try:
        content = stand_path.read_text(encoding="utf-8")
    except OSError:
        return None

    # Check for open questions or unassigned roles
    questions_match = re.search(r"## FRAGEN AN PHILIPP\s*([\s\S]*?)(?=##|$)", content)
    questions = questions_match.group(1).strip() if questions_match else ""
    has_open_questions = bool(questions and "- " in questions)

    if has_open_questions:
        return OvernightEvent(
            id="evt-stand-01",
            source="STAND.md / swarm coordination",
            agent_id="hack-chef",
            title="Swarm assignment & role coordination question",
            details=f"Open items in STAND.md: {questions[:250]}",
            severity="WARNING",
            proposed_action="Resolve role delegation (voice & dashboard) during morning commute call",
        )
    return None


def collect_repo_events(
    repo_dir: Path | str = ".",
    limit: int = 5,
    include_seed_fallbacks: bool = True,
) -> list[OvernightEvent]:
    """Aggregate all overnight repo events into a unified list."""
    events = parse_git_commits(repo_dir, limit=limit)
    stand_evt = check_stand_file(repo_dir)
    if stand_evt:
        # Insert as prominent item
        events.insert(0, stand_evt)

    # Re-index IDs cleanly: evt-001, evt-002, ...
    for idx, e in enumerate(events, start=1):
        e.id = f"evt-{idx:03d}"

    # If too few events found and seed fallbacks requested, append default seed events
    if len(events) < 3 and include_seed_fallbacks:
        seed_events = [
            OvernightEvent(
                id=f"evt-{len(events)+1:03d}",
                source="PR #4 merge conflict check",
                agent_id="hack-bau2",
                title="Voice pipeline migration to WebSocket streaming",
                details="Changes touch network interfaces and gradbot audio buffer. Irreversible deployment step pending confirmation.",
                severity="WARNING",
                proposed_action="Request human decision: Approve production audio port bind (8090)",
            ),
            OvernightEvent(
                id=f"evt-{len(events)+2:03d}",
                source="agent log / STAND.md update",
                agent_id="hack-visual",
                title="Visual assets generation completed",
                details="Hero banners and app icons generated via Nano Banana. Storage footprint 1.2MB.",
                severity="INFO",
                proposed_action="Bundle into dashboard static assets",
            ),
        ]
        events.extend(seed_events)

    return events[:max(limit, 3)]


def aggregate_and_save(
    repo_dir: Path | str = ".",
    output_path: Path | str = "src/data/overnight_events.json",
    limit: int = 5,
) -> list[OvernightEvent]:
    """Aggregate repo events and write to JSON output."""
    events = collect_repo_events(repo_dir, limit=limit)
    save_events(events, output_path)
    return events


if __name__ == "__main__":
    evts = aggregate_and_save()
    print(f"Aggregated {len(evts)} events to src/data/overnight_events.json")
    for e in evts:
        print(f"  [{e.severity}] {e.id} ({e.agent_id}): {e.title}")
