"""Request model for workflows — an ordered chain of features.

Each step runs a feature; later steps can reference earlier outputs with `${N.key}`
placeholders (N = 0-based step index, key = a field in that step's result). With a
`webhook`, the workflow runs as a background job and POSTs the final result there.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    feature: str
    with_: dict = Field(default_factory=dict, alias="with")  # this step's payload (may use ${N.key})

    model_config = {"populate_by_name": True}


class WorkflowRequest(BaseModel):
    steps: list[WorkflowStep] = Field(min_length=1)
    webhook: str | None = None  # if set, run async and POST the result here

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "steps": [
                        {
                            "feature": "extract",
                            "with": {"text": "Acme billed $1290 on 2026-02-01", "schema": {"vendor": "string", "amount": "number"}},
                        },
                        {"feature": "summarize", "with": {"text": "Vendor ${0.vendor} charged ${0.amount}."}},
                    ]
                }
            ]
        }
    }
