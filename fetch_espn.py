import json, datetime, urllib.request, pathlib
LEAGUE_ID=562354279
ROOT=pathlib.Path(__file__).resolve().parent
URL=f'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2026/segments/0/leagues/{LEAGUE_ID}'
VIEWS='?view=mTeam&view=mRoster&view=mMatchupScore&view=mScoreboard&view=mLiveScoring&view=mSettings'
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=35) as response:return json.load(response)
def valid_number(value):
 try:
  if value is None:return None
  return round(float(value),2)
 except (TypeError,ValueError):return None
def projection(side):
 for key in ('totalProjectedPointsLive','totalProjectedPoints'):
  if side.get(key) is not None:return valid_number(side[key])
 return None
def score(side,week,current):
 if week>current:return None
 return valid_number(side.get('totalPoints'))
def standings_from_games(games,team_ids,through):
 wins={i:0 for i in team_ids};losses={i:0 for i in team_ids};ties={i:0 for i in team_ids};pts={i:0 for i in team_ids}
 for g in games:
  if g['week']>through or g['homeScore'] is None or g['awayScore'] is None:continue
  h,a=g['homeId'],g['awayId']
  if h not in wins or a not in wins:continue
  pts[h]+=g['homeScore'];pts[a]+=g['awayScore']
  if g['homeScore']>g['awayScore']:wins[h]+=1;losses[a]+=1
  elif g['homeScore']<g['awayScore']:wins[a]+=1;losses[h]+=1
  else:ties[h]+=1;ties[a]+=1
 return sorted(team_ids,key=lambda i:(-wins[i],-pts[i],i))
def main():
 raw=get(URL+VIEWS)
 current=int(raw.get('scoringPeriodId') or raw.get('status',{}).get('currentMatchupPeriod') or 1)
 teams=[]
 for t in raw.get('teams',[]):
  record=t.get('record',{}).get('overall',{})
  teams.append({'id':t['id'],'name':t.get('name') or ((t.get('location','')+' '+t.get('nickname','')).strip()),'logo':t.get('logo',''),'wins':record.get('wins',0),'losses':record.get('losses',0),'ties':record.get('ties',0),'pointsFor':record.get('pointsFor',0)})
 if not teams:raise ValueError('ESPN returned no teams')
 photos={}
 for t in raw.get('teams',[]):
  for item in t.get('roster',{}).get('entries',[]):
   player=item.get('playerPoolEntry',{}).get('player',{})
   name=player.get('fullName')
   pid=player.get('id')
   if name and pid and int(pid)>0:
    photos[name]={'id':pid,'headshot':f'https://a.espncdn.com/i/headshots/nfl/players/full/{pid}.png'}
 schedule=raw.get('schedule',[])
 # The league-wide matchup view may omit schedule periods. Supplement it with the
 # period-specific scoreboard when necessary, while keeping any real scores.
 periods=sorted(set(int(m.get('matchupPeriodId',0)) for m in schedule if m.get('matchupPeriodId'))|set(range(1,19)))
 all_games=[]
 for week in periods:
  matches=[m for m in schedule if int(m.get('matchupPeriodId',0))==week]
  if not matches:
   try:
    period=get(URL+VIEWS+f'&scoringPeriodId={week}&matchupPeriodId={week}')
    matches=[m for m in period.get('schedule',[]) if int(m.get('matchupPeriodId',0))==week]
   except Exception as exc:
    print('Could not fetch week',week,exc)
  for m in matches:
   h,a=m.get('home',{}),m.get('away',{})
   if not h or not a or h.get('teamId') is None or a.get('teamId') is None:continue
   all_games.append({'week':week,'homeId':h['teamId'],'awayId':a['teamId'],'homeScore':score(h,week,current),'awayScore':score(a,week,current),'homeProjected':projection(h) if week>=current else None,'awayProjected':projection(a) if week>=current else None,'status':'upcoming' if week>current else ('completed' if week<current else 'current')})
 ids=[t['id'] for t in teams]
 previous=standings_from_games(all_games,ids,current-2)
 for t in teams:
  t['previousStanding']=previous.index(t['id'])+1 if current>1 else None
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 games=[{k:v for k,v in g.items() if k!='week'} for g in all_games if g['week']==current]
 data=ROOT/'data';data.mkdir(exist_ok=True)
 (data/'league.json').write_text(json.dumps({'week':current,'updatedAt':now,'teams':teams,'matchups':games,'schedule':all_games,'playerPhotos':photos},indent=2)+'\n')
 hp=data/'history.json'
 try:history=json.loads(hp.read_text())
 except (OSError,json.JSONDecodeError):history=[]
 for g in all_games:
  if g['week']!=current:continue
  if g['homeProjected'] is None or g['awayProjected'] is None:continue
  history.append({'week':current,'at':now,'homeId':g['homeId'],'awayId':g['awayId'],'homeProjected':g['homeProjected'],'awayProjected':g['awayProjected']})
 history=history[-12000:]
 hp.write_text(json.dumps(history,indent=2)+'\n')
 print('Saved',len(teams),'teams,',len(all_games),'scheduled matchups, week',current)
if __name__=='__main__':main()
