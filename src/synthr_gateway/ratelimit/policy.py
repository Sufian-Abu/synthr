"""Resolve which rate-limit windows apply to a request, from config.

Limit keys look like `daily_requests` / `weekly_requests` / `monthly_requests` (per_user)
and `daily_per_user` (per_feature). The leading word selects the window. Project limits
override defaults. Each policy is (scope, limit, window_seconds).
"""

from __future__ import annotations

from ..config import Config

WINDOWS = {"daily": 86_400, "weekly": 604_800, "monthly": 2_592_000}

Policy = tuple[str, int, int]


def resolve_policies(config: Config, project_id: str, feature: str, subject: str) -> list[Policy]:
    project = config.projects.get(project_id)
    policies: list[Policy] = []

    per_user = (project.limits.per_user if project and project.limits.per_user else config.defaults.limits.per_user)
    for name, limit in per_user.items():
        window = WINDOWS.get(name.split("_")[0])
        if window:
            policies.append((f"{project_id}:{subject}:{name.split('_')[0]}", limit, window))

    per_feature: dict[str, int] = {}
    if project and feature in project.limits.per_feature:
        per_feature = project.limits.per_feature[feature]
    elif feature in config.defaults.limits.per_feature:
        per_feature = config.defaults.limits.per_feature[feature]
    for name, limit in per_feature.items():
        period = name.split("_")[0]
        window = WINDOWS.get(period)
        if window:
            policies.append((f"{project_id}:{subject}:{feature}:{period}", limit, window))

    return policies
