"""orchestrator — Orchestrator agent package

Contains everything the orchestrator agent needs:
  agent.py   — node function that validates input, calls the LLM, and returns a route
  prompts.py — the routing prompt template

The orchestrator is intentionally small and stateless.
It only decides which agent handles a request — it never produces content itself.
"""
