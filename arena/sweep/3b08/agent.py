import importlib.util
_s = importlib.util.spec_from_file_location("knobbed_3b08", '/home/claude/poker_sequoia/bots/claude_v4/agent.py'); M = importlib.util.module_from_spec(_s); _s.loader.exec_module(M)
M.K.update({"three_bet": 0.08})
Agent = M.Agent
