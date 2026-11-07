import gzip,json,collections,sys,argparse
from pathlib import Path
import eval7
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'arena'))
ap=argparse.ArgumentParser(description='Scan own hands for provable heads-up river decision errors.')
ap.add_argument('history');ap.add_argument('--out',required=True);ap.add_argument('--examples',help='Optional private hand-level evidence file; keep outside Git')
args=ap.parse_args()
import league
V=league.load_bot(ROOT/'bots/claude_v6','full_old_v6')
path=args.history
C=collections.Counter();examples=[];deck={r+s:eval7.Card(r+s) for r in '23456789TJQKA' for s in 'cdhs'}
with gzip.open(path,'rt') as f:
 header=json.loads(next(f))
 for line in f:
  t=json.loads(line);o=json.loads(next(f))['you'];me=o['seat']
  if t['fillers'][me]:continue
  C['tables']+=1;kept={(e['hand'],e['kind']):e['cards'] for e in o.get('private_events',[])}
  for hi,h in enumerate(t['hands']):
   if not h['stacks_before'][me]:continue
   board=[];bets=[0]*8;stacks=h['stacks_before'][:];active={i for i,x in enumerate(stacks) if x>0};revealed={};pot=0;raised=limped=False;hero_acted=False;flop_called=False
   for ei,e in enumerate(h['events']):
    k=e['kind'];s=e.get('seat');amt=e.get('amount',0)
    if k=='board':board+=e['cards'];bets=[0]*8;continue
    if k=='reveal':revealed[s]=e['cards'][0]
    if s is None:continue
    price=min(stacks[s],max(bets)-bets[s]);paid=amt-bets[s] if k=='raise' else amt
    if s==me and k in ('fold','call','raise','check'):
     total=stacks[s]+bets[s];held=kept.get((h['hand'],'kept'))
     if not board and not hero_acted and not raised and not limped and k!='check':
      bb=total/h['blinds'][1];bucket='12to16' if 12<bb<=16 else '16to20' if 16<bb<=20 else None
      if bucket:C['open_'+bucket+'_n']+=1;C['open_'+bucket+'_shove']+=k=='raise' and paid>=stacks[s]
     hero_acted=True
     if len(board)==3 and k=='call':flop_called=True
     if len(board)>=4 and k=='fold' and flop_called:C['flop_call_later_fold']+=1
     if board and held:
      if k=='fold':
       val=eval7.evaluate([deck[c] for c in held+board]);C['fullhouse_plus_folds']+=(val>>24)>=6
      if k=='call' and price>=.4*total and held[0][0]==held[1][0] and len(set(c[0] for c in board))<len(board):
       a=V.analyze(tuple(held),tuple(board))
       if a['cls']==2:C['large_paired_board_pocket_calls']+=1
      opponents=active-{me}
      if len(board)==5 and len(opponents)==1 and k in ('call','fold'):
       other=next(iter(opponents))
       if other in revealed:
        used=set(o['cards'][hi]+board+list(revealed.values()));ours=eval7.evaluate([deck[c] for c in held+board]);fixed=[deck[c] for c in board+[revealed[other]]];wins=ties=losses=0
        for card,obj in deck.items():
         if card in used:continue
         theirs=eval7.evaluate(fixed+[obj]);wins+=ours>theirs;ties+=ours==theirs;losses+=ours<theirs
        C['enumerated_hu_river_'+k]+=1
        kind='provably_lost_call' if k=='call' and wins+ties==0 else 'cannot_lose_fold' if k=='fold' and losses==0 else None
        if kind:
         C[kind]+=1;C[kind+'_chips']+=price
         if len(examples)<20:examples.append({'kind':kind,'iteration':t['iteration'],'table':t['table'],'hand':h['hand'],'held':held,'board':board[:],'shown':revealed[other],'price':price,'pot':pot})
    if k=='fold':active.discard(s)
    if k in ('blind','ante','call','raise'):
     stacks[s]-=paid;pot+=paid
     if k!='ante':bets[s]+=paid
     if not board and k=='raise':raised=True
     if not board and k=='call' and not raised:limped=True
   C['flop_call_hands']+=flop_called
  if C['tables']%5000==0:print('processed',C['tables'],flush=True)
Path(args.out).write_text(json.dumps(dict(C),indent=2)+'\n')
if args.examples: Path(args.examples).write_text(json.dumps(examples,indent=2)+'\n')
print(json.dumps(dict(C),indent=2),flush=True)
