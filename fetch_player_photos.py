"""Refresh ESPN NFL headshot URLs for every commissioner Team of the Week pick.
Uses ESPN's public NFL team roster endpoint, independently of fantasy league access.
"""
import json, pathlib, urllib.request, unicodedata, re, time

ROOT=pathlib.Path(__file__).resolve().parent
TEAMS=['ari','atl','bal','buf','car','chi','cin','cle','dal','den','det','gb','hou','ind','jax','kc','lv','lac','lar','mia','min','ne','no','nyg','nyj','phi','pit','sf','sea','tb','ten','wsh']
def key(s):
 s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
 return re.sub('[^a-z0-9]','',s)
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=18) as res:return json.load(res)
def collect(obj,found):
 if isinstance(obj,list):
  for v in obj:collect(v,found)
 elif isinstance(obj,dict):
  if obj.get('id') and (obj.get('displayName') or obj.get('fullName')) and (obj.get('position') or obj.get('headshot')):
   name=obj.get('displayName') or obj.get('fullName')
   pid=str(obj['id'])
   if pid.isdigit() and name:
    h=obj.get('headshot')
    if isinstance(h,dict):h=h.get('href')
    found[key(name)]={'id':pid,'headshot':h if isinstance(h,str) and h.startswith('https://') else f'https://a.espncdn.com/i/headshots/nfl/players/full/{pid}.png'}
  for v in obj.values():collect(v,found)
def main():
 dest=ROOT/'data'/'player_photos.json'
 try:photos=json.loads(dest.read_text())
 except (OSError,ValueError):photos={}
 for team in TEAMS:
  try:
   data=fetch('https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/'+team+'/roster')
   collect(data,photos)
  except Exception as exc:print('Roster lookup failed for',team,exc)
  time.sleep(.1)
 # Preserve IDs previously recovered from the league's fantasy roster.
 try:
  league=json.loads((ROOT/'data'/'league.json').read_text())
  for name,entry in league.get('playerPhotos',{}).items():
   if entry.get('id'):photos[key(name)]=entry
 except (OSError,ValueError):pass
 selected=json.loads((ROOT/'data'/'commissioner_totw.json').read_text())
 missing=sorted({p['player'] for p in selected if p.get('slot')!='D/ST' and key(p['player']) not in photos})
 dest.write_text(json.dumps(photos,indent=2,sort_keys=True)+'\n')
 print('ESPN portraits:',len(photos),'matched, missing selections:',missing)
if __name__=='__main__':main()
