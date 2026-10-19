/* Season-to-date league records; completed weeks only. */
(()=>{
const el=()=>document.getElementById('records-list');
const fmt=n=>Number(n).toFixed(2);
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function draw(){
 const node=el();if(!node||!window.league)return;
 const l=window.league,teams=l.teams||[],games=(l.schedule||[]).filter(g=>+g.week<+l.week&&Number.isFinite(+g.homeScore)&&Number.isFinite(+g.awayScore)&&g.homeScore!==null&&g.awayScore!==null);
 const name=id=>teams.find(t=>String(t.id)===String(id))?.name||'Team '+id;
 const entries=games.flatMap(g=>[{id:g.homeId,week:g.week,score:+g.homeScore,margin:+g.homeScore-(+g.awayScore),opp:g.awayId},{id:g.awayId,week:g.week,score:+g.awayScore,margin:+g.awayScore-(+g.homeScore),opp:g.homeId}]);
 const best=(arr,field,high)=>arr.length?[...arr].sort((a,b)=>high?b[field]-a[field]:a[field]-b[field])[0]:null;
 const records=[];
 function add(title,item,metric,description){records.push({title,value:item?metric(item):'—',detail:item?name(item.id)+' · Week '+item.week+(description?' · '+description(item):''):'Awaiting verified ESPN results'})}
 add('MOST POINTS IN A WEEK',best(entries,'score',true),x=>fmt(x.score)+' PTS');
 add('LEAST POINTS IN A WEEK',best(entries,'score',false),x=>fmt(x.score)+' PTS');
 add('BIGGEST WINNING MARGIN',best(entries.filter(x=>x.margin>0),'margin',true),x=>'+'+fmt(x.margin)+' PTS',x=>'vs '+name(x.opp));
 add('BIGGEST LOSING MARGIN',best(entries.filter(x=>x.margin<0),'margin',false),x=>fmt(x.margin)+' PTS',x=>'vs '+name(x.opp));
 for(const [title,win] of [['LONGEST WIN STREAK',true],['LONGEST LOSING STREAK',false]]){
  let top=null;
  for(const t of teams){
   const rows=entries.filter(x=>String(x.id)===String(t.id)).sort((a,b)=>a.week-b.week);let streak=0,previous=null;
   for(const x of rows){if(x.margin===0){streak=0;previous=x.week;continue}
    streak=(x.margin>0===win&&previous===x.week-1)?streak+1:(x.margin>0===win?1:0);
    if(streak>(top?.count||0))top={id:t.id,week:x.week,count:streak};
    previous=x.week;
   }
  }
  records.push({title,value:top?top.count+' '+(top.count===1?'GAME':'GAMES'):'—',detail:top?name(top.id)+' · through Week '+top.week:'Awaiting completed games'});
 }
 node.innerHTML='<p class="records-intro">2026 SEASON · VERIFIED COMPLETED MATCHUPS THROUGH WEEK '+Math.max(0,(l.week||1)-1)+'</p><div class="records-grid">'+records.map(r=>'<article class="record-card"><span>'+escape(r.title)+'</span><strong>'+escape(r.value)+'</strong><p>'+escape(r.detail)+'</p></article>').join('')+'</div><div class="records-accuracy"><h3>MANAGER ACCURACY · BEST AND WORST</h3><p>Awaiting complete weekly ESPN starting and bench player scores. Accuracy requires comparing actual lineup points against the optimal legal starting lineup, including position and FLEX eligibility; incomplete roster data will not be presented as a record.</p></div>';
}
window.renderLeagueRecords=draw;
window.addEventListener('league-updated',draw);
document.addEventListener('DOMContentLoaded',draw);
})();
