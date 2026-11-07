#!/usr/bin/env python3
"""Paired single-hero evaluation. Usage: python arena/survival_switch_eval.py holdout 192.
Synthetic profiles test robustness; they are not a reconstruction of live rivals.
"""
import sys,json,random,statistics,hashlib,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import league
from poker_engine.table import SitAndGo,TableRules
from poker_engine.variant import load_variant
from poker_engine.scoring import table_points,table_places
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT;OUT=ROOT/'arena/runs'/('survival-switch-'+str(time.time_ns()));OUT.mkdir(parents=True)
paths={'candidate':ROOT/'bots/codex_survival_switch_v1','gto_final':ROOT/'bots/gto_final_reference','gto_original':ROOT/'bots/gto_supplied','v6':ROOT/'bots/claude_v6'}
pools={
 'balanced':{'nc_v9':.18,'kevin1':.12,'codex_merge_v4_v6':.12,'codex_reveal_v1':.08,'arch_tag':.20,'arch_loose':.08,'arch_limper':.08,'arch_nit':.06,'arch_maniac':.04,'arch_station':.04},
 'pressure':{'nc_v9':.30,'kevin1':.16,'codex_merge_v4_v6':.10,'codex_reveal_v1':.06,'arch_tag':.12,'arch_loose':.10,'arch_limper':.02,'arch_nit':.02,'arch_maniac':.08,'arch_station':.04}}
for name in pools['balanced']:paths[name]=REPO/'bots'/name
mods={n:league.load_bot(p,'ss_'+n) for n,p in paths.items()}
rules=TableRules(players=8,variant='flop_discard_reveal');variant=load_variant(rules.variant)
def run(hero,opponents,seat,seed):
 names=opponents[:seat]+[hero]+opponents[seat:];t=SitAndGo(rules=rules,variant=variant,table_id=seed,seed=seed);agents=[mods[n].Agent() for n in names];mem=[b'']*8;fails=[0]*8;dec=[0]*8
 while (s:=t.decision()) is not None:
  p=s.seat;dec[p]+=1
  try:a,m=agents[p].act(s,mem[p]);answered=isinstance(m,bytes) and len(m)<=rules.memory_bytes
  except Exception:a=None;m=mem[p];answered=False
  if answered:mem[p]=m
  if not t.apply(a,answered=answered):fails[p]+=1
 r=t.result(tuple(fails),tuple(dec));points=table_points(r,t.payouts);places=table_places(r)
 early=any(h['hand']<=20 and h['stacks_before'][seat]>0 and h['stacks_after'][seat]==0 for h in t.log)
 return {'points':points[seat],'cash':float(places[seat]<=3),'first':float(places[seat]==1),'early_bust':float(early),'failed_decisions':fails[seat],'all_failed_decisions':sum(fails)}
if __name__=='__main__':
 stage=sys.argv[1];count=int(sys.argv[2]);assert count >= 2;heroes=['candidate','gto_final','gto_original','v6']
 report={'stage':stage,'tables_per_profile':count,'profiles':pools,'sources':{n:league.fingerprints(p) for n,p in paths.items()},'rows':[],'summary':{},'paired_differences':{}}
 for profile,pool in pools.items():
  for i in range(count):
   seed=f'survival-switch-{stage}-1:{profile}:{i}';rng=random.Random(seed+':lineup');opps=rng.choices(list(pool),list(pool.values()),k=7);seat=i%8;row={'profile':profile,'seed':seed,'hero_seat':seat,'opponents':opps,'results':{}}
   # Same table seed, seat and opponent lineup for every candidate comparison.
   for hero in heroes:row['results'][hero]=run(hero,opps,seat,seed)
   report['rows'].append(row)
   if (i+1)%40==0:print(stage,profile,i+1,flush=True)
 for group in ['all',*pools]:
  rows=[r for r in report['rows'] if group=='all' or r['profile']==group];report['summary'][group]={};report['paired_differences'][group]={}
  for h in heroes:
   report['summary'][group][h]={k:league.mean_ci([r['results'][h][k] for r in rows]) for k in ['points','cash','first','early_bust']}
   report['summary'][group][h]['failed_decisions']=sum(r['results'][h]['failed_decisions'] for r in rows)
  for b in heroes[1:]:report['paired_differences'][group][b]={k:league.mean_ci([r['results']['candidate'][k]-r['results'][b][k] for r in rows]) for k in ['points','cash','first','early_bust']}
 (OUT/(stage+'.json')).write_text(json.dumps(report,indent=2)+'\n')
 print('Report:', OUT/(stage+'.json'), flush=True)
 print(json.dumps({'summary':report['summary'],'paired_differences':report['paired_differences']},indent=2),flush=True)
