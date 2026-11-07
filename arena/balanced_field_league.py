import sys,json,random,statistics,collections,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'arena'))
ap=argparse.ArgumentParser(description='Equal-appearance mixed league; no promotion or upload.')
ap.add_argument('--out',required=True);ap.add_argument('--blocks',type=int,default=16);ap.add_argument('--seed',default='nc7-balanced-final-20261106');ap.add_argument('--bots',nargs='+');args=ap.parse_args()
import league
from poker_engine.table import SitAndGo,TableRules
from poker_engine.variant import load_variant
from poker_engine.scoring import table_points
repo=league.ROOT;mods={};hashes={}
for folder in sorted((repo/'bots').iterdir()):
 if folder.name in ('nc_v1','nc_v2') or not (folder/'agent.py').exists():continue
 if args.bots and folder.name not in args.bots:continue
 mods[folder.name]=league.load_bot(folder,'final_'+folder.name);hashes[folder.name]=league.fingerprints(folder)
if args.blocks < 1: ap.error('--blocks must be positive')
if args.bots:
 missing=set(args.bots)-set(mods)
 if missing: ap.error('Unknown or blocked policies: '+', '.join(sorted(missing)))
 mods={n:mods[n] for n in args.bots}
if len(mods)<8:raise SystemExit('Select at least eight policies')
names=list(mods);samples=collections.defaultdict(list);fail=collections.Counter();tables=[];rules=TableRules(players=8,variant='flop_discard_reveal');variant=load_variant(rules.variant);seed=args.seed
for block in range(args.blocks):
 order=names[:];random.Random(f'{seed}:block:{block}').shuffle(order)
 for offset in range(len(names)):
  seats=[order[(offset+i)%len(names)] for i in range(8)];it=block*len(names)+offset;random.Random(f'{seed}:seats:{it}').shuffle(seats)
  t=SitAndGo(rules=rules,variant=variant,table_id=f'{seed}:{it}',seed=f'{seed}:{it}');agents=[mods[n].Agent() for n in seats];mem=[b'']*8;fc=[0]*8;dc=[0]*8
  while (s:=t.decision()) is not None:
   p=s.seat;dc[p]+=1
   try:a,m=agents[p].act(s,mem[p]);answered=isinstance(m,bytes) and len(m)<=rules.memory_bytes;mem[p]=m if answered else mem[p]
   except Exception:a=None;answered=False
   if not t.apply(a,answered=answered):fc[p]+=1;fail[seats[p]]+=1
  pts=table_points(t.result(tuple(fc),tuple(dc)),t.payouts)
  for i,n in enumerate(seats):samples[n].append(pts[i])
  tables.append({'seats':seats,'points':pts})
 if block%4==3:print('league tables',len(tables),flush=True)
r={'seed':seed,'tables':len(tables),'appearances_per_bot':len(samples[names[0]]),'sources':hashes,'archetypes_sha256':hashlib.sha256((repo/'arena/archetypes.py').read_bytes()).hexdigest(),'scores':{n:league.mean_ci(v) for n,v in samples.items()},'failures':dict(fail),'ranked':sorted(samples,key=lambda n:statistics.fmean(samples[n]),reverse=True),'table_results':tables,'note':'Equal appearances, eight distinct policies per table; missing competitors are not simulated. CIs approximate, ranks uncertain.'}
Path(args.out).parent.mkdir(parents=True,exist_ok=True)
Path(args.out).write_text(json.dumps(r,indent=2)+'\n')
for i,n in enumerate(r['ranked'],1):print(i,n,round(r['scores'][n]['mean'],3),r['scores'][n]['approx_95ci'],flush=True)
