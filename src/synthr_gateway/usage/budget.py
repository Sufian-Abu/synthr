"""Hard budget caps — reject a request once a project is over its daily/monthly limit.

Caps are evaluated against the usage log (prior requests this period). Cache hits cost $0
but still count toward request caps.
"""

from __future__ import annotations

import time
from datetime import datetime

from ..config import BudgetCfg
from ..core import errors
from .log import UsageLog


def _day_start() -> float:
    now = datetime.now()
    return time.mktime(now.replace(hour=0, minute=0, second=0, microsecond=0).timetuple())


def _month_start() -> float:
    now = datetime.now()
    return time.mktime(now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timetuple())


def enforce_budget(usage: UsageLog, budget: BudgetCfg, project: str, feature: str) -> None:
    if budget.daily_usd is not None or budget.daily_requests is not None:
        day = usage.aggregate(project, _day_start())
        if budget.daily_requests is not None and day["requests"] >= budget.daily_requests:
            raise errors.budget_exceeded(f"Daily request cap ({budget.daily_requests}) reached for this project.")
        if budget.daily_usd is not None and day["cost"] >= budget.daily_usd:
            raise errors.budget_exceeded(f"Daily spend cap (${budget.daily_usd:g}) reached for this project.")

    if budget.monthly_usd is not None or budget.monthly_requests is not None:
        month = usage.aggregate(project, _month_start())
        if budget.monthly_requests is not None and month["requests"] >= budget.monthly_requests:
            raise errors.budget_exceeded(f"Monthly request cap ({budget.monthly_requests}) reached for this project.")
        if budget.monthly_usd is not None and month["cost"] >= budget.monthly_usd:
            raise errors.budget_exceeded(f"Monthly spend cap (${budget.monthly_usd:g}) reached for this project.")

    cap = budget.per_feature_daily_requests.get(feature)
    if cap is not None and usage.feature_count(project, feature, _day_start()) >= cap:
        raise errors.budget_exceeded(f"Daily cap ({cap}) for feature {feature!r} reached.")
