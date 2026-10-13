"""Collect weekly starting-lineup leaders and completed trade activity from ESPN."""
import json, datetime, urllib.request, pathlib, collections
ROOT=pathlib.Path(__file__).resolve().parent
BASE="https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2026/segments/0/leagues/562354279"
POSITIONS={0:"QB",2:"RB",4:"WR",6:"TE",16:"D/ST",17:"K"}
SLOTS={0:"QB",2:"RB",4:"WR",6:"TE",16:"D/ST",17:"K",23:"FLEX",24:"FLEX"}
def request(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
def write(name,obj):
    p=ROOT/"data"/name;p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(obj,indent=2)+"\n")
def load(name,default):
    try:return json.loads((ROOT/"data"/name).read_text())
    except (OSError,ValueError):return default
def entries_for_week(raw,week):
    for game in raw.get("schedule",[]):
        if game.get("matchupPeriodId")!=week:continue
        for side in ("home","away"):
            team=game.get(side) or {}
            for entry in (team.get("rosterForCurrentScoringPeriod") or team.get("rosterForMatchupPeriod") or {}).get("entries",[]):
                yield team.get("teamId"),entry
def points(entry,week):
    p=entry.get("playerPoolEntry",{}).get("player",{})
    stats=p.get("stats",[])
    actual=[s for s in stats if s.get("scoringPeriodId")==week and s.get("statSourceId")==0]
    if not actual:actual=[s for s in stats if s.get("scoringPeriodId")==week and s.get("statSourceId") in (None,0)]
    return (actual[0].get("appliedTotal") if actual else entry.get("playerPoolEntry",{}).get("appliedStatTotal"))
def starters(raw,week):
    best={}; allpoints={}
    for team_id,e in entries_for_week(raw,week):
        slot=e.get("lineupSlotId")
        p=e.get("playerPoolEntry",{}).get("player",{})
        pid=p.get("id");score=points(e,week)
        if pid is not None and score is not None:allpoints[str(pid)]=float(score)
        if slot not in SLOTS or score is None:continue
        position=POSITIONS.get(p.get("defaultPositionId"))
        if not position:continue
        candidate={"position":position,"name":p.get("fullName") or p.get("name") or "Unknown","playerId":pid,"teamId":team_id,"points":round(float(score),2),"lineupSlot":SLOTS[slot],"headshot":f"https://a.espncdn.com/i/headshots/nfl/players/full/{pid}.png" if pid else None}
        if position not in best or candidate["points"]>best[position]["points"]:best[position]=candidate
    return best,allpoints
def trade_records(raw):
    records=[]
    for tx in raw.get("transactions",[]):
        if tx.get("type")!="TRADE" or tx.get("status") not in ("EXECUTED","ACCEPTED","PROCESSED"):continue
        date=tx.get("processDate") or tx.get("executionDate") or tx.get("proposedDate")
        items=[]
        for item in tx.get("items",[]):
            if item.get("type") in ("TRADE","TRADED","TRADE_ACCEPTED","TRADE_PROPOSAL") or item.get("fromTeamId") is not None:
                items.append({"playerId":item.get("playerId"),"fromTeamId":item.get("fromTeamId"),"toTeamId":item.get("toTeamId")})
        if not items:continue
        records.append({"id":tx.get("id"),"date":datetime.datetime.fromtimestamp(date/1000,datetime.timezone.utc).isoformat() if isinstance(date,(int,float)) else None,"items":items})
    return records
def main():
    current=load("league.json",{}).get("week",1)
    last=max(1,int(current)-1)
    weekly=load("player_weekly.json",{})
    best={}
    for week in range(1,last+1):
        try:
            raw=request(BASE+f"?view=mBoxscore&scoringPeriodId={week}")
            leaders,scores=starters(raw,week)
            if scores:weekly[str(week)]=scores
            if week==last:best=leaders
        except Exception as exc:print(f"Week {week} boxscore unavailable: {exc}")
    write("player_weekly.json",weekly)
    if best:write("team_of_week.json",{"week":last,"leaders":list(best.values()),"note":"Only ESPN starting lineup slots are eligible; FLEX players compete in their natural position."})
    try:
        raw=request(BASE+"?view=mTransactions2")
        trades=trade_records(raw)
        for trade in trades:
            if not trade["date"]:continue
            timestamp=datetime.datetime.fromisoformat(trade["date"])
            # Week-level scoring can only be attributed after the trade's effective week.
            trade_week=next((w for w in range(1,last+2) if datetime.datetime.fromisoformat("2026-09-08T00:00:00+00:00")+datetime.timedelta(days=7*(w-1))>timestamp),last+1)
            for item in trade["items"]:
                pid=str(item["playerId"]);scores=[v[pid] for w,v in weekly.items() if int(w)>=trade_week and pid in v]
                item["pointsSinceTrade"]=round(sum(scores),2) if scores else None
                item["gamesRecorded"]=len(scores)
        write("trades.json",{"trades":trades,"note":"Points are from recorded weekly ESPN box scores after the trade effective week. Missing data is not treated as zero."})
    except Exception as exc:print("Trades unavailable:",exc)
if __name__=="__main__":main()
