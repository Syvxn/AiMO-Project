"""State contract for the orchestrator agent."""
from __future__ import annotations

from typing import Literal, TypedDict


Route = Literal["teacher", "end"]


class OrchestratorState(TypedDict, total=False):
    user_input: str       # The user's raw request
    route: Route          # Which agent should handle the request
    active_agent: str     # Name of the agent selected
    error: str            # Set when no agent could be matched
