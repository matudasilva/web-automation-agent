from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PostPublishStatus = Literal[
    "published_visible",
    "submitted_for_approval",
    "publish_blocked_or_unavailable",
    "publish_unconfirmed",
]


@dataclass(frozen=True)
class PostPublishOutcome:
    status: PostPublishStatus
    observed_text: str
    signal: str
