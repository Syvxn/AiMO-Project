"""teacher — Teacher agent package

Contains everything the teacher agent needs:
  agent.py   — three node functions forming the ReAct loop (llm_call, tool_node, should_continue)
  prompts.py — the MCQ quiz generation prompt template
  tools.py   — @tool-decorated functions the LLM can call during its ReAct loop

ReAct loop flow
---------------
  teacher_llm_call
    └─► teacher_should_continue ──(tool calls)──► teacher_tool_node ──► teacher_llm_call
                                ──(no tool calls)────────────────────────────────────► END
"""
