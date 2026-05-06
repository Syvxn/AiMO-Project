"""Public package surface for the AiMO agents project."""

from .agents import build_graph


# Keep runner imports lazy so `python -m aimo_agents.runner` does not import
# the runner module twice (which triggers runpy warnings on Windows).
def run_once(*args, **kwargs):
    from .runner import run_once as _run_once

    return _run_once(*args, **kwargs)


def run_cli(*args, **kwargs):
    from .runner import run_cli as _run_cli

    return _run_cli(*args, **kwargs)


__all__ = ["build_graph", "run_cli", "run_once"]
