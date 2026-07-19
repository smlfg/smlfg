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


def dotted_line(label: str, value: str, width: int = 49) -> tuple[str, str, str]:
    dots = "." * max(2, width - len(label) - len(value))
    return label, dots, value


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

    control_loop = (
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
    diagram_markup = "\n".join(
        f'<tspan x="18" y="{30 + index * 20}">{line}</tspan>'
        for index, line in enumerate(control_loop)
    )

    profile_lines = (
        ("header", "samuel@fleig  ───────────────────────────────────────────"),
        ("line", dotted_line("Role", "AI Engineering student")),
        ("line", dotted_line("Site", "human-agent-interface.com")),
        ("line", dotted_line("Focus", "human-agent workflow acceptance")),
        ("line", dotted_line("Environment", "Pop!_OS / COSMIC")),
        ("blank", ""),
        ("line", dotted_line("Agents.Primary", "Codex, Claude, Hermes")),
        ("line", dotted_line("Context", "routing, memory, knowledge graphs")),
        ("line", dotted_line("Method", "failure -> contract -> evidence")),
        ("line", dotted_line("Thesis", "human authority, machine execution")),
        ("blank", ""),
        ("header", "- GitHub Signals ─────────────────────────────────────────"),
        ("line", dotted_line("Public Repositories", metrics["repositories"])),
        ("line", dotted_line("Public Events / 30d", metrics["recent_events"])),
        ("line", dotted_line("Public Stars", metrics["stars"])),
        ("line", dotted_line("Generated", metrics["updated"])),
    )
    profile_markup: list[str] = []
    y = 30
    for kind, content in profile_lines:
        if kind == "header":
            profile_markup.append(f'<text x="390" y="{y}" class="text">{content}</text>')
        elif kind == "line":
            label, dots, value = content
            profile_markup.append(
                f'<text x="390" y="{y}"><tspan class="muted">. </tspan>'
                f'<tspan class="key">{label}</tspan>'
                f'<tspan class="muted">: {dots} </tspan>'
                f'<tspan class="value">{value}</tspan></text>'
            )
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
