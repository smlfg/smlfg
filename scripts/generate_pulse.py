#!/usr/bin/env python3
"""Generate the public HAI profile pulse SVGs.

Only GitHub's public API is queried. A temporary API failure intentionally
produces a usable SVG with unavailable counters instead of failing the workflow.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USERNAME = os.environ.get("PROFILE_USERNAME", "smlfg")
TOKEN = os.environ.get("GITHUB_TOKEN")


def github_json(url: str) -> object | None:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-profile-pulse",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def public_metrics() -> dict[str, str]:
    repositories = github_json(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner&sort=updated"
    )
    events = github_json(
        f"https://api.github.com/users/{USERNAME}/events/public?per_page=100"
    )

    metrics = {
        "repositories": "—",
        "stars": "—",
        "recent_events": "—",
        "updated": datetime.now(UTC).strftime("%Y-%m-%d"),
    }

    if isinstance(repositories, list):
        public_repositories = [repo for repo in repositories if not repo.get("private", True)]
        metrics["repositories"] = str(len(public_repositories))
        metrics["stars"] = str(sum(repo.get("stargazers_count", 0) for repo in public_repositories))

    if isinstance(events, list):
        since = datetime.now(UTC) - timedelta(days=30)
        recent = 0
        for event in events:
            created_at = event.get("created_at")
            if not created_at:
                continue
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if created >= since:
                recent += 1
        metrics["recent_events"] = str(recent)

    return metrics


def terminal_line(y: int, label: str, value: str) -> str:
    """Render one terminal property with explicit columns.

    Explicit x positions keep the SVG readable in GitHub and simpler SVG
    rasterizers; inline tspans are not consistently laid out everywhere.
    """

    label_x = 410
    value_x = 640
    character_width = 9.6
    label_end = label_x + len(label) * character_width
    dot_count = max(2, int((value_x - label_end) / character_width) - 2)
    return (
        f'<text x="390" y="{y}" class="muted">. </text>'
        f'<text x="{label_x}" y="{y}" class="key">{escape(label)}</text>'
        f'<text x="{label_end:.1f}" y="{y}" class="muted">: {"." * dot_count} </text>'
        f'<text x="{value_x}" y="{y}" class="value">{escape(value)}</text>'
    )


def svg(theme: str, metrics: dict[str, str]) -> str:
    palette = {
        "dark": {
            "background": "#161b22",
            "border": "#30363d",
            "text": "#c9d1d9",
            "muted": "#8b949e",
            "key": "#ffa657",
            "value": "#a5d6ff",
            "accent": "#3fb950",
        },
        "light": {
            "background": "#ffffff",
            "border": "#d0d7de",
            "text": "#24292f",
            "muted": "#57606a",
            "key": "#9a6700",
            "value": "#0969da",
            "accent": "#1a7f37",
        },
    }[theme]

    _original_control_loop = (
        "     _   _    _    ___ ",
        "    | | | |  / \\  |_ _|",
        "    | |_| | / _ \\  | | ",
        "    |  _  |/ ___ \\ | | ",
        "    |_| |_/_/   \\_\\___|",
        "",
        "       .------------.",
        "       |    HUMAN   |",
        "       '-----+------'",
        "             |",
        "       .-----v------.",
        "       |   CONTEXT  |",
        "       '-----+------'",
        "             |",
        "       .-----v------.",
        "       |    AGENT   |",
        "       '-----+------'",
        "             |",
        "       .-----v------.",
        "       |    PROOF   |",
        "       '-----+------'",
        "             |",
        "       .-----v------.",
        "       |    OWNER   |",
        "       '------------'",
    )
    # Concrete V1.6 execution example; the earlier block remains only as
    # source history for the original HAI mark.
    control_loop = (
        "       HAI / V1.6",
        "  $ hai loop --example",
        "",
        "        [ human ]",
        "  accepts NEXT_STEP.md",
        "             |",
        "             v",
        "     [ hai-executer ]",
        "   allowed changes only",
        "             |",
        "             v",
        "     [ hai-validator ]",
        "      verdict: ACCEPT?",
        "        +---+---+",
        "       yes      no",
        "        |        |",
        "        v        v",
        "  [ human gate ] repair route",
        "   commit / push      |",
        "        |             +----> executer",
        "        v",
        " [ proof: report + result ]",
    )

    diagram_markup = "\n".join(
        f'<tspan x="18" y="{30 + index * 20}">{line}</tspan>'
        for index, line in enumerate(control_loop)
    )

    profile_lines = (
        ("header", "samuel@fleig  ───────────────────────────────────────────"),
        ("line", ("Role", "AI Engineering student")),
        ("line", ("Work", "AIDVANCE, Berlin (Working Student)")),
        ("line", ("Title", "AI Operations & Agent Enablement")),
        ("line", ("Site", "human-agent-interface.com")),
        ("line", ("Focus", "human-agent workflow acceptance")),
        ("line", ("Environment", "Pop!_OS / COSMIC")),
        ("blank", ""),
        ("line", ("Agents.Primary", "Codex, Claude, Hermes")),
        ("line", ("Context", "routing, memory, knowledge graphs")),
        ("line", ("Method", "failure -> contract -> evidence")),
        ("line", ("Thesis", "human authority, machine execution")),
        ("blank", ""),
        ("header", "- GitHub Signals ─────────────────────────────────────────"),
        ("line", ("Public Repositories", metrics["repositories"])),
        ("line", ("Public Events / 30d", metrics["recent_events"])),
        ("line", ("Public Stars", metrics["stars"])),
        ("line", ("Generated", metrics["updated"])),
        ("blank", ""),
        ("header", "- Build Lineage ───────────────────────────────────────────"),
        ("milestone", ("2025.11", "SelfAI", "planner, tools, memory")),
        ("milestone", ("2026", "Sidecar", "activity -> outcome proof")),
        ("milestone", ("2026", "HAI", "human contract, model-agnostic")),
        ("milestone", ("2026.07", "Learning proof", "context -> active human work")),
    )
    profile_markup: list[str] = []
    y = 30
    for kind, content in profile_lines:
        if kind == "header":
            profile_markup.append(f'<text x="390" y="{y}" class="text">{content}</text>')
        elif kind == "line":
            label, value = content
            profile_markup.append(terminal_line(y, label, value))
        elif kind == "milestone":
            year, project, evidence = content
            profile_markup.append(terminal_line(y, f"{year} {project}", evidence))
        y += 20

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="985" height="530" viewBox="0 0 985 530" role="img" aria-labelledby="title description">
  <title id="title">Samuel Fleig — Human-Agent Interface profile</title>
  <desc id="description">A terminal profile for Samuel Fleig and Human-Agent Interface.</desc>
  <style>
    text, tspan {{ white-space: pre; }}
    .ascii {{ fill: {palette["accent"]}; font: 16px Consolas, "Courier New", monospace; }}
    .text {{ fill: {palette["text"]}; font: 16px Consolas, "Courier New", monospace; }}
    .muted {{ fill: {palette["muted"]}; font: 16px Consolas, "Courier New", monospace; }}
    .key {{ fill: {palette["key"]}; font: 16px Consolas, "Courier New", monospace; }}
    .value {{ fill: {palette["value"]}; font: 16px Consolas, "Courier New", monospace; }}
  </style>
  <rect width="985" height="530" rx="15" fill="{palette["background"]}"/>
  <rect x="0.5" y="0.5" width="984" height="529" rx="14.5" fill="none" stroke="{palette["border"]}"/>
  <text x="18" y="30" class="ascii">{diagram_markup}</text>
  {"".join(profile_markup)}
</svg>
'''


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    metrics = public_metrics()
    for theme in ("light", "dark"):
        (ASSETS / f"hai-pulse-{theme}.svg").write_text(svg(theme, metrics), encoding="utf-8")


if __name__ == "__main__":
    main()
