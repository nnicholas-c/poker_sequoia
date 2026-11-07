"""Knob sweep: build variant folders of a knobbed bot and run each in the same field.
python arena/sweep.py bots/claude_v4 --tables 150 --field bots/arch_tag bots/arch_tag bots/arch_loose bots/arch_nit kit/examples/check_or_fold bots/kevin1
"""
import argparse, json, os, subprocess, sys, re
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument('bot'); ap.add_argument('--tables', type=int, default=150)
ap.add_argument('--field', nargs='+', required=True); ap.add_argument('--variants', default=None, help='json file of {name: {knob: value}}')
args = ap.parse_args()
base = Path(args.bot).resolve()
variants = json.load(open(args.variants)) if args.variants else {
    "base": {}, "open08": {"open_mult": 0.8}, "open12": {"open_mult": 1.2}, "lam25": {"lam": 0.25}, "lam60": {"lam": 0.60},
    "cbet_lo": {"cbet_dry": 0.35, "cbet_rand": 0.15}, "strong62": {"strong": 0.62}, "strong54": {"strong": 0.54},
    "callm04": {"call_margin": 0.04}, "callm-03": {"call_margin": -0.03}, "3b08": {"three_bet": 0.08}, "nobluff": {"bluff_river": 0.0, "raise_bluff": 0.0},
}
root = Path('arena/sweep'); root.mkdir(exist_ok=True)
for name, knobs in variants.items():
    d = root / name; d.mkdir(exist_ok=True)
    (d / 'agent.py').write_text(f'''import importlib.util
_s = importlib.util.spec_from_file_location("knobbed_{name}", {str(base / "agent.py")!r}); M = importlib.util.module_from_spec(_s); _s.loader.exec_module(M)
M.K.update({json.dumps(knobs)})
Agent = M.Agent
''')
results = {}
procs = {}
for name in variants:
    cmd = [sys.executable, 'arena/arena.py', str(root / name), str(root / name)] + args.field + ['--tables', str(args.tables), '--quiet']
    procs[name] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
for name in variants:
    out = procs[name].communicate()[0]
    pts = []
    for line in out.split("\nbot ")[1].splitlines() if "\nbot " in out else []:
        m = re.match(rf'^{re.escape(name)}#\d\s+([\d.]+)\s+([\d.]+)', line)
        if m: pts.append(float(m.group(1)))
    bust = re.findall(rf'^{re.escape(name)}#\d.*?\s(\d+)\s+1:', out, re.M)
    results[name] = (sum(pts) / len(pts) if pts else float('nan'), pts)
    print(f"{name:12s} avg {results[name][0]:6.2f}  copies {pts}  knobs {variants[name]}", flush=True)
