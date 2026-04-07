"""Snapshot GitHub repo metrics for TCP and append to vault history.

Captures:
- Per-asset download counts (cumulative, from /releases)
- Repo views (14-day window)
- Repo clones (14-day window)
- Top referrers
- Top paths
- Stargazers count
- Forks count

Output:
- Appends a daily JSON line to: D:\\Vaults\\Mainframe\\02_Projects\\Terminal Copy Paste\\Metrics\\downloads.jsonl
- Updates summary at: D:\\Vaults\\Mainframe\\02_Projects\\Terminal Copy Paste\\Metrics\\Latest Snapshot.md
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = "CodeWarrior4Life/TerminalCopyPaste"
VAULT_METRICS = Path(r"D:\Vaults\Mainframe\02_Projects\Terminal Copy Paste\Metrics")
HISTORY_FILE = VAULT_METRICS / "downloads.jsonl"
SUMMARY_FILE = VAULT_METRICS / "Latest Snapshot.md"


def gh(path: str) -> dict | list:
    result = subprocess.run(
        ["gh", "api", path],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    VAULT_METRICS.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()

    snapshot: dict = {
        "timestamp": now,
        "repo": REPO,
    }

    repo_meta = gh(f"repos/{REPO}")
    snapshot["stargazers"] = repo_meta.get("stargazers_count", 0)
    snapshot["forks"] = repo_meta.get("forks_count", 0)
    snapshot["watchers"] = repo_meta.get("subscribers_count", 0)

    releases = gh(f"repos/{REPO}/releases")
    snapshot["releases"] = []
    for r in releases:
        rel = {
            "tag": r["tag_name"],
            "name": r.get("name", r["tag_name"]),
            "published_at": r.get("published_at"),
            "assets": [],
        }
        for a in r.get("assets", []):
            rel["assets"].append(
                {
                    "name": a["name"],
                    "size": a["size"],
                    "download_count": a.get("download_count", 0),
                }
            )
        snapshot["releases"].append(rel)

    snapshot["total_downloads"] = sum(
        a["download_count"] for r in snapshot["releases"] for a in r["assets"]
    )

    try:
        views = gh(f"repos/{REPO}/traffic/views")
        snapshot["traffic_views_14d"] = {
            "count": views.get("count", 0),
            "uniques": views.get("uniques", 0),
        }
    except subprocess.CalledProcessError:
        snapshot["traffic_views_14d"] = None

    try:
        clones = gh(f"repos/{REPO}/traffic/clones")
        snapshot["traffic_clones_14d"] = {
            "count": clones.get("count", 0),
            "uniques": clones.get("uniques", 0),
        }
    except subprocess.CalledProcessError:
        snapshot["traffic_clones_14d"] = None

    try:
        referrers = gh(f"repos/{REPO}/traffic/popular/referrers")
        snapshot["top_referrers"] = referrers
    except subprocess.CalledProcessError:
        snapshot["top_referrers"] = []

    try:
        paths = gh(f"repos/{REPO}/traffic/popular/paths")
        snapshot["top_paths"] = paths
    except subprocess.CalledProcessError:
        snapshot["top_paths"] = []

    with HISTORY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(snapshot) + "\n")

    summary_lines = [
        "---",
        "type: note",
        f"updated: {now}",
        "tags: [project/tcp, metrics, downloads]",
        "summary: TCP download counts and repo traffic snapshot",
        "---",
        "",
        "# TCP Latest Metrics Snapshot",
        "",
        f"**As of:** {now}",
        f"**Repo:** {REPO}",
        "",
        "## Repo",
        f"- Stars: {snapshot['stargazers']}",
        f"- Forks: {snapshot['forks']}",
        f"- Watchers: {snapshot['watchers']}",
        "",
        "## Downloads (cumulative)",
        f"- **Total: {snapshot['total_downloads']}**",
        "",
    ]

    for r in snapshot["releases"]:
        summary_lines.append(f"### {r['tag']}")
        if not r["assets"]:
            summary_lines.append("- (no assets)")
        for a in r["assets"]:
            summary_lines.append(
                f"- `{a['name']}` ({a['size']:,} bytes): {a['download_count']} downloads"
            )
        summary_lines.append("")

    if snapshot.get("traffic_views_14d"):
        v = snapshot["traffic_views_14d"]
        summary_lines += [
            "## Traffic (14-day rolling)",
            f"- Views: {v['count']} ({v['uniques']} unique)",
        ]
    if snapshot.get("traffic_clones_14d"):
        c = snapshot["traffic_clones_14d"]
        summary_lines.append(f"- Clones: {c['count']} ({c['uniques']} unique)")
        summary_lines.append("")

    if snapshot.get("top_referrers"):
        summary_lines.append("## Top Referrers")
        for ref in snapshot["top_referrers"][:10]:
            summary_lines.append(
                f"- {ref.get('referrer', '?')}: {ref.get('count', 0)} ({ref.get('uniques', 0)} unique)"
            )
        summary_lines.append("")

    if snapshot.get("top_paths"):
        summary_lines.append("## Top Paths")
        for p in snapshot["top_paths"][:10]:
            summary_lines.append(
                f"- `{p.get('path', '?')}`: {p.get('count', 0)} ({p.get('uniques', 0)} unique)"
            )
        summary_lines.append("")

    SUMMARY_FILE.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"Snapshot written to {HISTORY_FILE}")
    print(f"Summary updated at {SUMMARY_FILE}")
    print(f"Total downloads: {snapshot['total_downloads']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
