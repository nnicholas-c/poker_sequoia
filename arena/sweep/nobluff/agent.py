import importlib.util
_s = importlib.util.spec_from_file_location("knobbed_nobluff", '/home/claude/poker_sequoia/bots/claude_v4/agent.py'); M = importlib.util.module_from_spec(_s); _s.loader.exec_module(M)
M.K.update({"bluff_river": 0.0, "raise_bluff": 0.0})
Agent = M.Agent
