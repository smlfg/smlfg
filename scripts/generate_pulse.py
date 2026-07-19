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


def svg(theme: str, metrics: dict[str, str]) -> str:
    palette = {
        "dark": {
            "background": "#0d1117",
            "panel": "#161b22",
            "border": "#30363d",
            "text": "#f0f6fc",
            "muted": "#8b949e",
            "accent": "#3fb950",
            "accent_soft": "#1f6f3a",
        },
        "light": {
            "background": "#ffffff",
            "panel": "#f6f8fa",
            "border": "#d0d7de",
            "text": "#24292f",
            "muted": "#57606a",
            "accent": "#1a7f37",
            "accent_soft": "#b6e3c6",
        },
    }[theme]

    stat_x = (72, 350, 628)
    stats = (
        (metrics["repositories"], "PUBLIC REPOSITORIES"),
        (metrics["recent_events"], "PUBLIC EVENTS / 30D"),
        (metrics["stars"], "PUBLIC STARS"),
    )
    stat_markup = "\n".join(
        f'''<text x="{x}" y="225" class="number">{value}</text>
        <text x="{x}" y="254" class="label">{label}</text>'''
        for x, (value, label) in zip(stat_x, stats, strict=True)
    )

    stages = ("INTENT", "CONTEXT", "SCOPE", "VERIFY", "OWNER")
    stage_markup = "\n".join(
        f'''<rect x="{72 + index * 165}" y="311" width="126" height="34" rx="17" class="stage"/>
        <text x="{135 + index * 165}" y="333" text-anchor="middle" class="stageText">{stage}</text>'''
        for index, stage in enumerate(stages)
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="400" viewBox="0 0 1000 400" role="img" aria-labelledby="title description">
  <title id="title">Samuel Fleig — HAI public build pulse</title>
  <desc id="description">Public GitHub metrics and the Human-Agent Interface control loop.</desc>
  <style>
    .eyebrow {{ fill: {palette["accent"]}; font: 600 13px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: 1.8px; }}
    .title {{ fill: {palette["text"]}; font: 700 34px ui-sans-serif, system-ui, sans-serif; letter-spacing: -0.8px; }}
    .subtitle {{ fill: {palette["muted"]}; font: 400 16px ui-sans-serif, system-ui, sans-serif; }}
    .number {{ fill: {palette["text"]}; font: 700 38px ui-monospace, SFMono-Regular, Menlo, monospace; }}
    .label {{ fill: {palette["muted"]}; font: 600 11px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: 0.9px; }}
    .stage {{ fill: {palette["panel"]}; stroke: {palette["border"]}; stroke-width: 1; }}
    .stageText {{ fill: {palette["text"]}; font: 600 11px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: 0.6px; }}
    .connector {{ stroke: {palette["accent_soft"]}; stroke-width: 2; }}
  </style>
  <rect width="1000" height="400" rx="14" fill="{palette["background"]}"/>
  <rect x="0.5" y="0.5" width="999" height="399" rx="13.5" fill="none" stroke="{palette["border"]}"/>
  <circle cx="72" cy="59" r="5" fill="{palette["accent"]}"/>
  <text x="88" y="64" class="eyebrow">SAMUEL FLEIG / HUMAN-AGENT INTERFACE</text>
  <text x="72" y="118" class="title">PUBLIC BUILD PULSE</text>
  <text x="72" y="148" class="subtitle">Human control loops for reliable agent work</text>
  <text x="928" y="64" text-anchor="end" class="label">UPDATED {metrics["updated"]}</text>
  <line x1="72" y1="181" x2="928" y2="181" stroke="{palette["border"]}"/>
  {stat_markup}
  <line x1="72" y1="283" x2="928" y2="283" stroke="{palette["border"]}"/>
  <line x1="198" y1="328" x2="237" y2="328" class="connector"/>
  <line x1="363" y1="328" x2="402" y2="328" class="connector"/>
  <line x1="528" y1="328" x2="567" y2="328" class="connector"/>
  <line x1="693" y1="328" x2="732" y2="328" class="connector"/>
  {stage_markup}
  <text x="928" y="374" text-anchor="end" class="label">PUBLIC GITHUB SIGNALS ONLY</text>
</svg>
'''


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    metrics = public_metrics()
    for theme in ("light", "dark"):
        (ASSETS / f"hai-pulse-{theme}.svg").write_text(svg(theme, metrics), encoding="utf-8")


if __name__ == "__main__":
    main()
