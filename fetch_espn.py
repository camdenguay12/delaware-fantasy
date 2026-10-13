import json,datetime,urllib.request,pathlib
LEAGUE_ID=562354279
ROOT=pathlib.Path(__file__).resolve().parent
URL=f'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2026/segments/0/leagues/{LEAGUE_ID}?view=mTeam&view=mMatchupScore&view=mScoreboard&view=mLiveScoring&view=mSettings'
def get():
 req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
def main():
 raw=get()
 week=int(raw.get('scoringPeriodId') or raw.get('status',{}).get('currentMatchupPeriod') or 1)
 teams=[]
 for t in raw.get('teams',[]):
  record=t.get('record',{}).get('overall',{})
  teams.append({'id':t['id'],'name':t.get('name') or ((t.get('location','')+' '+t.get('nickname','')).strip()),'logo':t.get('logo',''),'wins':record.get('wins',0),'losses':record.get('losses',0),'ties':record.get('ties',0),'pointsFor':record.get('pointsFor',0)})
 games=[]
 for m in raw.get('schedule',[]):
  if int(m.get('matchupPeriodId',0))!=week:continue
  a,b=m.get('home',{}),m.get('away',{})
  if not a or not b:continue
  def total(v):
   return v.get('totalPoints',0)
  def proj(v):
   return v.get('totalProjectedPointsLive') if v.get('totalProjectedPointsLive') is not None else v.get('totalProjectedPoints')
  games.append({'homeId':a.get('teamId'),'awayId':b.get('teamId'),'homeScore':total(a),'awayScore':total(b),'homeProjected':proj(a),'awayProjected':proj(b)})
 if not teams:raise ValueError('ESPN response contained no teams; refusing to overwrite last valid data')
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 output={'week':week,'updatedAt':now,'teams':teams,'matchups':games}
 data=ROOT/'data';data.mkdir(exist_ok=True)
 (data/'league.json').write_text(json.dumps(output,indent=2)+'\n')
 hp=data/'history.json'
 try:history=json.loads(hp.read_text())
 except (OSError,json.JSONDecodeError):history=[]
 for g in games:history.append({'week':week,'at':now,**{k:g[k] for k in ('homeId','awayId','homeProjected','awayProjected')}})
 history=history[-12000:]
 hp.write_text(json.dumps(history,indent=2)+'\n')
 print('Saved',len(teams),'teams and',len(games),'matchups in week',week)
if __name__=='__main__':main()
