#!/usr/bin/env python3
"""Fast internal league: tactical gates, frozen sources, balanced eight-seat matches.

Run from the repository root: python arena/league.py [--bots claude_v2 kevin1]
This evaluates versions; it never edits a bot, changes a champion or uploads anything.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import random
import shutil
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from poker_agent_protocol.game import Action, is_legal, state_from_dict, state_to_dict
from poker_engine.scoring import table_points
from poker_engine.table import SitAndGo, TableRules
from poker_engine.variant import load_variant

ROOT = Path(__file__).resolve().parents[1]


def fingerprints(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts and p.suffix != '.pyc' and '.git' not in p.parts}


def snapshot(folder, destination):
    before = fingerprints(folder)
    shutil.copytree(folder, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
    if before != fingerprints(destination) or before != fingerprints(folder):
        raise RuntimeError(f'{folder}: changed during snapshot; rerun after the edit finishes')
    digest = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    return {'folder_sha256': digest, 'files': before}


def load_bot(folder, name):
    spec = importlib.util.spec_from_file_location(f'league_{name}', folder / 'agent.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys.path.insert(0, str(folder))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def traced_action(agent, state, memory):
    """Only used for a handful of tactical cases; catch silently swallowed TypeErrors."""
    errors = []
    previous = sys.gettrace()
    source = Path(sys.modules[agent.__class__.__module__].__file__).resolve() if agent.__class__.__module__ in sys.modules else None
    if source is None:
        import inspect
        source = Path(inspect.getfile(agent.act)).resolve()

    def trace(frame, event, arg):
        if event == 'exception' and Path(frame.f_code.co_filename).resolve() == source:
            kind, value, _ = arg
            # Empty/corrupt memory recovery is expected. Only trace strategy code.
            if frame.f_code.co_name in {'decide', 'preflop', 'postflop', 'analyze', 'select', 'choose_cards', 'equity'}:
                item = f'{frame.f_code.co_name}:{frame.f_lineno}: {kind.__name__}: {value}'
                if item not in errors:
                    errors.append(item)
        return trace

    sys.settrace(trace)
    try:
        action, output = agent.act(state, memory)
    finally:
        sys.settrace(previous)
    return action, output, errors


def tactical_checks(module, cases):
    rows = []
    for case in cases:
        state = state_from_dict(case['state'])
        row = {'case': case['id'], 'severity': case['severity']}
        try:
            # Evaluate the actual wrapper at normal speed. Tracing is a second call:
            # tracing overhead must not alter deadline-sensitive policy outcomes.
            action, memory = module.Agent().act(state, b'')
            _, _, swallowed = traced_action(module.Agent(), state, b'')
            legal = is_legal(action, state.legal_actions)
            good_memory = isinstance(memory, bytes) and len(memory) <= state.config.memory_bytes
            row.update(action=action.kind, amount=action.amount, swallowed_exceptions=swallowed,
                       passed=legal and good_memory and action.kind in case['allowed_actions'] and not swallowed)
        except Exception as exc:
            row.update(passed=False, error=repr(exc))
        rows.append(row)
    return rows


def mean_ci(values):
    mean = statistics.fmean(values)
    radius = 1.96 * statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else None
    return {'tables': len(values), 'mean': mean,
            'approx_95ci': [mean-radius, mean+radius] if radius is not None else None}


def play_match(names, modules, tables, seed, incident_file):
    """4 vs 4. Average copies inside each table before estimating uncertainty."""
    rules = TableRules(players=8, variant='flop_discard_reveal')
    variant = load_variant(rules.variant)
    stats = {n: {'decisions': 0, 'failures': 0, 'latency': [], 'errors': [], 'streets': Counter(),
                 'early_busts': 0, 'seat_tables': 0} for n in names}
    samples = defaultdict(list)
    for iteration in range(tables):
        seats = [names[0]]*4 + [names[1]]*4
        random.Random(f'{seed}:{iteration}:seats').shuffle(seats)
        table = SitAndGo(rules=rules, variant=variant, table_id=f'league-{seed}-{iteration}', seed=f'{seed}:{iteration}')
        agents = [modules[n].Agent() for n in seats]
        memory = [b'']*8
        failures, decisions = [0]*8, [0]*8
        early_states = defaultdict(list)
        while (state := table.decision()) is not None:
            seat = state.seat; name = seats[seat]; st = stats[name]
            decisions[seat] += 1; st['decisions'] += 1
            began = time.perf_counter_ns()
            try:
                action, output = agents[seat].act(state, memory[seat])
                if not isinstance(action, Action):
                    raise TypeError('act() did not return an Action')
                if not isinstance(output, bytes) or len(output) > rules.memory_bytes:
                    raise ValueError('invalid memory type/size')
                answered = True
            except Exception as exc:
                action, output, answered = None, memory[seat], False
                if len(st['errors']) < 5:
                    st['errors'].append(repr(exc))
            st['latency'].append((time.perf_counter_ns()-began)/1e6)
            if state.hand_number <= 20:
                recent = early_states[state.hand_number,seat]
                recent.append((state, repr(action)))
                del recent[:-3]
            legal = answered and is_legal(action, state.legal_actions)
            # Follow official event acknowledgement: an answered illegal action still
            # acknowledges events and its memory. A missing reply keeps old memory.
            if answered:
                memory[seat] = output
                st['streets'][f'{state.phase}:{len(state.board)}:{action.kind}'] += 1
            applied = table.apply(action, answered=answered)
            if not legal or not applied:
                failures[seat] += 1; st['failures'] += 1
                if st['failures'] <= 3:
                    incident_file.write(json.dumps({'kind':'failed_decision','bot':name,'seed':seed,'iteration':iteration,
                                                    'state':state_to_dict(state)})+'\n')
        result = table.result(tuple(failures), tuple(decisions))
        scores = table_points(result, table.payouts)
        for name in names:
            samples[name].append(statistics.fmean(scores[i] for i,n in enumerate(seats) if n == name))
            stats[name]['seat_tables'] += 4
        for hand in table.log:
            for seat,(before,after) in enumerate(zip(hand['stacks_before'],hand['stacks_after'])):
                if before and not after and hand['hand'] <= 20:
                    stats[seats[seat]]['early_busts'] += 1
                    if stats[seats[seat]]['early_busts'] <= 2:
                        # Public diagnostic log; an early bust is a review lead, not a failure.
                        incident_file.write(json.dumps({'kind':'early_bust_review','bot':seats[seat],'seat':seat,
                                                        'seed':seed,'iteration':iteration,'hand':hand,
                                                        'own_last_decisions':[{'state':state_to_dict(s),'action':a} for s,a in early_states[hand['hand'],seat]]})+'\n')
    for st in stats.values():
        lat = sorted(st.pop('latency'))
        st['latency_ms'] = {f'p{q}':lat[min(len(lat)-1,int(q/100*len(lat)))] if lat else 0 for q in (50,99,99.9)}
        st['latency_note'] = 'direct computation only; use official subprocess check before upload'
    return {'bots': names, 'seed': seed, 'scores': {n:mean_ci(samples[n]) for n in names},
            'difference_a_minus_b': mean_ci([a-b for a,b in zip(samples[names[0]],samples[names[1]])]), 'health':stats}


def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--bots', nargs='+', help='names under bots/; default: discover all')
    p.add_argument('--focus', help='only compare this changed bot against the others')
    p.add_argument('--tables', type=int, default=24, help='tables per pairing (quick triage, not promotion proof)')
    p.add_argument('--seed', default=None, help='default: fresh run ID; reuse only to reproduce')
    p.add_argument('--checks-only', action='store_true')
    args=p.parse_args()
    if args.tables < 2: p.error('--tables must be at least 2')
    # arch_* are local arena helper policies, not standalone submitted contenders.
    # They import shared arena code outside the bot folder; use arena.py for those.
    folders = {f.parent.name:f.parent for f in sorted((ROOT/'bots').glob('*/agent.py'))
               if not f.parent.name.startswith('arch_')}
    chosen=args.bots or list(folders)
    if len(set(chosen)) != len(chosen) or any(n not in folders for n in chosen): p.error('unknown or duplicate bot names')
    if args.focus and args.focus not in chosen:p.error('--focus must be a selected bot')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    run=ROOT/'arena/runs'/run_id;run.mkdir(parents=True)
    cases=json.loads((ROOT/'arena/critical_cases.json').read_text())['cases']
    report={'run_id':run_id,'seed':args.seed or run_id,'mode':'checks-only' if args.checks_only else 'quick-triage',
            'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'league_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'cases_sha256':hashlib.sha256((ROOT/'arena/critical_cases.json').read_bytes()).hexdigest(),
            'python':sys.version,
            'sources':{},'checks':{},'matches':[],'notes':[
                'Exact bot-folder hashes identify sources, including uncommitted edits.',
                'Independent unit is a table, not each of four correlated copies.',
                'Normal confidence intervals are approximate; short samples are not promotion proof.',
                'No automatic champion changes, bot edits, learning across tables, or uploads.']}
    modules={};eligible=[]
    for name in chosen:
        try:
            report['sources'][name]=snapshot(folders[name],run/'bots'/name)
            modules[name]=load_bot(run/'bots'/name,name)
            report['checks'][name]=tactical_checks(modules[name],cases)
            passed=all(r['passed'] for r in report['checks'][name] if r['severity']=='block')
        except Exception as exc:
            report['checks'][name]=[{'case':'load','severity':'block','passed':False,'error':repr(exc)}];passed=False
        if passed:eligible.append(name)
        print(f'{name}: {"PASS" if passed else "BLOCKED"}',flush=True)
    if not args.checks_only:
        with (run/'incidents.jsonl').open('w') as incidents:
            for a,b in itertools.combinations(eligible,2):
                if args.focus and args.focus not in (a,b):continue
                match=play_match([a,b],modules,args.tables,f'{report["seed"]}:{a}:{b}',incidents)
                report['matches'].append(match)
                diff=match['difference_a_minus_b']
                print(f'{a} vs {b}: {match["scores"][a]["mean"]:.2f} / {match["scores"][b]["mean"]:.2f}; delta {diff["mean"]:+.2f}, CI {diff["approx_95ci"]}',flush=True)
                (run/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    changed=[n for n in chosen if n in report['sources'] and fingerprints(folders[n]) != report['sources'][n]['files']]
    report['sources_changed_during_run']=changed
    (run/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=[f'# Internal league — {run_id}','',f'Seed: `{report["seed"]}`. Short triage; no automatic promotion.','',
           '| Bot | Critical checks | Folder SHA-256 |','|---|---|---|']
    for n in chosen:
        lines.append(f'| {n} | {"PASS" if n in eligible else "BLOCKED"} | {report["sources"].get(n,{}).get("folder_sha256","load failed")} |')
    lines+=['','| Pair | Points A / B | Difference A − B (approx. 95% CI) |','|---|---|---|']
    for m in report['matches']:
        a,b=m['bots'];d=m['difference_a_minus_b'];lo,hi=d['approx_95ci']
        lines.append(f'| {a} / {b} | {m["scores"][a]["mean"]:.2f} / {m["scores"][b]["mean"]:.2f} | {d["mean"]:+.2f} [{lo:+.2f}, {hi:+.2f}] |')
    if changed:lines+=['',f'Sources changed while running: {", ".join(changed)}. Results describe frozen snapshots only.']
    lines+=['','See report.json for failures, street actions, latency and exact source hashes. Early busts in incidents.jsonl are review leads, not evidence of a bad decision.']
    (run/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
    print(f'Report: {run.relative_to(ROOT)}/SUMMARY.md')
    if args.focus and args.focus not in eligible:return 2
    return 0 if eligible else 2


if __name__=='__main__':raise SystemExit(main())
