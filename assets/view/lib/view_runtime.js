/* view runtime — ONE script for every host: the offline report and the served page.
   viewMount(root, view, state) draws a view at the lens state.level, in the FORM that lens's row names:
     story        (orient)      meaning before machinery: stages in plain words, technologies linked to their manuals
     schematic    (understand)  the drawing: parts by what they do, flows, gates, one hinge — no live value, and an address
                                only on a private page (`view.visibility`), each part's own, in its box
     health-chain (operate)     the drawing's own vital sign in its archetype's shape (reservoir, lanes, roster, gauges,
                                board, scoreboard, funnel, race), or tiles in flow order as the fallback; blind spots
                                shown; actions where they act; correlate blocks — values on one time axis — beneath
     anatomy      (inspect)     evidence: the wiring, a card of each part's own facts, the procedure bound to its parts
   state = {level, live, values:{bindId: number | [{name, value}]}, history:{bindId:[[t,v]..]}, onAction(a), historyUrl}
   A value is formatted by its unit, as the law's `units` rows give it: a binding carries its unit, the quantity the
   unit measures (`q`) and its factor to that quantity's coherent unit (`f`, two whole numbers).
   The INSPECTOR is one card for every lens: it anchors to the element (not the mouse), is fixed-positioned so no
   container clips it, flips at the screen edges, pins on click (so its links are clickable), closes on Esc or an
   outside click, opens on keyboard focus, and survives a re-render by remembering which element it was pinned to. */
(function(){
const W=(typeof window!=='undefined')?window:this;
function h(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
const PCT={unit:'percent',q:'ratio',f:[1,100]},SEC={unit:'second',q:'duration',f:[1,1]};
function coherent(b,v){return b&&b.f?v*b.f[0]/b.f[1]:v;}
function dur(s){if(s==null||isNaN(s))return '—';s=Math.max(0,Math.round(+s));
 if(s>=172800)return (s/86400).toFixed(s>=864000?0:1)+' d';
 const hh=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;
 return hh?hh+' h '+String(m).padStart(2,'0')+' min':m?m+' min'+(m<10&&x?' '+x+' s':''):x+' s';}
function bytes(n){const u=['B','kB','MB','GB','TB','PB'];let i=0;while(Math.abs(n)>=1000&&i<u.length-1){n/=1000;i++;}return (i?n.toFixed(1):Math.round(n))+' '+u[i];}
function bits(n){const u=['bit/s','kbit/s','Mbit/s','Gbit/s','Tbit/s'];let i=0;while(Math.abs(n)>=1000&&i<u.length-1){n/=1000;i++;}return (i?n.toFixed(1):Math.round(n))+' '+u[i];}
function num(v){return (Math.abs(v)>=100?Math.round(v):v.toFixed(v%1?1:0))+'';}
function fmt(v,b){if(v==null||isNaN(v))return '—';v=+v;const u=(b&&b.unit)||'',q=(b&&b.q)||'';
 if(u==='percent')return v.toFixed(1)+'%';
 if(q==='duration')return v*b.f[0]/b.f[1]<1&&v>0?Math.round(v*b.f[0]/b.f[1]*1000)+' ms':dur(coherent(b,v));
 if(q==='information')return bytes(coherent(b,v));
 if(q==='data-rate')return bits(coherent(b,v)*8);
 return u?num(v)+' '+u:num(v);}
function pctOf(b,v){return b&&b.q==='ratio'?coherent(b,v)*100:v;}
function stateOf(b,v,live){if(!live)return 'nd';if(v==null)return 'nd';
 if(b.live==='live-state')return v>=1?'up':'down';
 return b.crit!=null&&v>=b.crit?'down':b.warn!=null&&v>=b.warn?'warn':'up';}

/* ---------------- the inspector ----------------
   A HOVER CARD WITH INTENT. It opens 90 ms after the pointer rests on an inspectable element and stays open while
   the pointer travels into it (a 280 ms grace), so every link inside is clickable WITHOUT pinning. Nested
   elements (a chip inside a stage card) resolve to the INNERMOST one under the pointer. Clicking an element that
   is not itself a link pins its card (for touch and for keeping it while scrolling); clicking a link follows it —
   a chip's own link goes straight to the manual. Esc or a click outside closes a pinned card; keyboard focus
   opens it like hover. The card is fixed-positioned (no container clips it) and flips at the screen edges. */
const INS={el:null,key:null,pinned:false,over:null,t:null,fns:new WeakMap()};
function insEl(){if(!INS.el){INS.el=document.createElement('div');INS.el.className='vw vw-ins';INS.el.setAttribute('role','dialog');
 document.body.appendChild(INS.el);
 document.addEventListener('keydown',e=>{if(e.key==='Escape')insHide(true);});
 document.addEventListener('pointerover',e=>{const t=e.target;
  if(INS.el.contains(t)){clearTimeout(INS.t);return;}                       // travelling into the card keeps it
  const n=t.closest&&t.closest('[data-ins]');
  if(n===INS.over)return;INS.over=n;clearTimeout(INS.t);
  if(n)INS.t=setTimeout(()=>insShow(n,false),90);
  else if(!INS.pinned)INS.t=setTimeout(()=>insHide(false),280);},true);
 document.addEventListener('pointerleave',()=>{if(!INS.pinned)insHide(false);});
 document.addEventListener('click',e=>{const t=e.target;if(INS.el.contains(t))return;
  const n=t.closest&&t.closest('[data-ins]');
  if(!n){if(INS.pinned)insHide(true);return;}
  if(t.closest('a,button,[data-click]'))return;                             // a link, a button or an action does its own thing
  e.stopPropagation();insShow(n,true);},true);
 document.addEventListener('focusin',e=>{const n=e.target.closest&&e.target.closest('[data-ins]');if(n&&!INS.el.contains(e.target))insShow(n,false);});}
 return INS.el;}
function insShow(node,pin){const d=insEl(),fn=INS.fns.get(node);if(!fn)return;const key=node.getAttribute('data-ins');
 if(INS.pinned&&!pin&&INS.key!==key)return;
 d.innerHTML=fn()+(pin?'<div class="ins-foot">pinned · Esc to close</div>':'');
 d.classList.toggle('pinned',!!pin);d.style.display='block';INS.key=key;INS.pinned=!!pin;
 const r=node.getBoundingClientRect(),dw=d.offsetWidth,dh=d.offsetHeight,vw=innerWidth,vh=innerHeight;
 let x=r.left+r.width/2-dw/2,y=r.bottom+6;
 if(y+dh>vh-8)y=r.top-dh-6; if(y<8)y=Math.min(vh-dh-8,r.bottom+6);
 x=Math.max(8,Math.min(vw-dw-8,x));d.style.left=x+'px';d.style.top=y+'px';}
function insHide(force){if(!INS.el)return;if(INS.pinned&&!force)return;INS.el.style.display='none';INS.pinned=false;INS.key=null;INS.over=null;}
function inspectable(node,key,htmlFn){insEl();node.setAttribute('data-ins',key);INS.fns.set(node,htmlFn);
 if(!node.hasAttribute('tabindex')&&!/^(A|BUTTON)$/.test(node.tagName))node.setAttribute('tabindex','0');}
function reattach(root){if(!INS.key)return;const n=root.querySelector('[data-ins="'+INS.key+'"]');
 if(n){if(INS.el.style.display!=='none')insShow(n,INS.pinned);}else insHide(true);}

/* ---------------- pieces ---------------- */
const ELSEWHERE='live on the served page';
function short(n){return String(n||'').split(' (')[0];}   // a chip carries the name, the inspector the full title
function techChip(t){return '<a class="vw-tech" href="'+h(t.docs||t.homepage||'#')+'" target="_blank" rel="noopener" data-tech="'+h(t.code)+'">'+
 '<i>'+h((t.name||t.code).slice(0,1))+'</i>'+h(short(t.name||t.code))+' <span class="ext">↗</span></a>';}
function techCard(t){return '<b>'+h(t.name||t.code)+'</b><div class="ins-sub">'+h(t.category||'technology')+(t.vendor?' · '+h(t.vendor):'')+'</div>'+
 (t.docs?'<div><a href="'+h(t.docs)+'" target="_blank" rel="noopener">official documentation ↗</a></div>':'')+
 (t.fields&&t.fields.length?'<div class="ins-row"><span>field of knowledge</span>'+t.fields.map(f=>h(f.code)+' '+h(f.label)).join('<br>')+'</div>':'')+
 (t.occupations&&t.occupations.length?'<div class="ins-row"><span>who runs it</span>'+t.occupations.map(o=>h(o.code)+' '+h(o.label)).join('<br>')+'</div>':'');}
function partCard(f){if(!f)return '';const a=(f.addresses||[]);return '<b>'+h(f.title)+'</b>'+(f.role?'<div class="ins-sub">'+h(f.role)+'</div>':'')+
 (a.length?'<div class="ins-row"><span>addresses</span>'+a.map(x=>'<code>'+h(x.address)+'</code> '+h((x.what||[]).join(' · '))).join('<br>')+'</div>':'')+
 (f.tech&&f.tech.length?'<div class="ins-row"><span>runs</span>'+f.tech.map(t=>'<a href="'+h(t.docs)+'" target="_blank" rel="noopener">'+h(t.name)+' ↗</a>').join(' · ')+'</div>':'');}
function head(view,lv){const q=(view.questions||{})[lv.id];   // the DRAWING's own question at this lens, else the lens's own
 return '<div class="vw-head"><div class="vw-lv"><span class="lvname">'+h(lv.name)+'</span><span class="lvq">'+h(q||lv.question)+'</span></div>'+
 '<h3>'+view.title+'</h3>'+(lv.form==='story'?'':'<p class="vw-claim">'+view.claim+'</p>')+'</div>';}

/* ---------------- orient · story ---------------- */
function story(root,view,lv){const s=view.story;
 if(!s){root.innerHTML=head(view,lv)+'<p class="vw-empty">No story is written for this drawing.</p>';return;}
 let o=head(view,lv)+'<p class="vw-purpose">'+h(s.purpose)+'</p><ol class="vw-story" style="--n:'+s.stages.length+'">';
 s.stages.forEach((st,i)=>{o+='<li class="vw-stage" data-st="'+i+'"><span class="num">'+(i+1)+'</span><div class="lbl">'+h(st.label)+'</div><div class="doer">'+h(st.doer)+'</div>'+
  (st.tech.length?'<div class="techs">'+st.tech.map(techChip).join('')+'</div>':'')+'</li>';});
 o+='</ol><div class="vw-outcome"><span class="num">✓</span><div><div class="lbl">When it works</div><div class="doer">'+h(s.outcome)+'</div></div></div>';
 if(s.fields&&s.fields.length)o+='<div class="vw-learn"><span>to learn it properly</span>'+s.fields.map(f=>'<span class="vw-field" data-field="'+h(f.code)+'">'+h(f.code)+' · '+h(f.label)+'</span>').join('')+'</div>';
 root.innerHTML=o;
 const T={};s.stages.forEach(st=>st.tech.forEach(t=>T[t.code]=t));
 root.querySelectorAll('.vw-tech').forEach(a=>inspectable(a,'tech:'+a.dataset.tech,()=>techCard(T[a.dataset.tech])));
 root.querySelectorAll('.vw-stage[data-st]').forEach(n=>{const st=s.stages[+n.dataset.st];
  inspectable(n,'stage:'+n.dataset.st,()=>'<b>'+h(st.label)+'</b><div class="ins-sub">'+h(st.doer)+'</div>'+
   (st.parts&&st.parts.length?'<div class="ins-row"><span>in the ledger</span>'+st.parts.map(p=>h(p.title)+(p.role?' — '+h(p.role):'')).join('<br>')+'</div>':''));});
 root.querySelectorAll('.vw-field').forEach(n=>{const f=s.fields.find(x=>x.code===n.dataset.field);
  inspectable(n,'field:'+f.code,()=>'<b>'+h(f.scheme)+' '+h(f.code)+'</b><div class="ins-sub">'+h(f.path.join(' › '))+'</div><div class="ins-row"><span>technologies here</span>'+h(f.techs.join(', '))+'</div>');});}

/* ---------------- understand · schematic ---------------- */
function schematic(root,view,lv,state){
 root.innerHTML=head(view,lv)+'<div class="vw-fig">'+view.svg+'</div>'+(view.caption?'<div class="vw-cap">'+view.caption+'</div>':'')+
  (view.legend?'<div class="vw-legend">'+view.legend.map(l=>'<span title="'+h(l[1])+'">'+l[2]+h(l[0])+'</span>').join('')+'</div>':'');
 const svg=root.querySelector('svg.schema');svg.classList.add('lv-schematic');
 const byId={};(view.elements||[]).forEach(e=>byId[e.id]=e);
 svg.querySelectorAll('.el').forEach(g=>{const e=byId[g.dataset.el];if(!e)return;
  if(e.pattern==='flow'||e.pattern==='signal'||e.pattern==='boundary'||e.pattern==='band')return;
  const f=(view.facts||{})[e.bean];
  inspectable(g,'el:'+e.id,()=>'<b>'+h(e.label)+'</b><div class="ins-sub">'+h((view.patternMeaning||{})[e.pattern]||e.pattern)+'</div>'+(f?'<div class="ins-row"><span>ledger</span>'+partCard(f)+'</div>':''));});
 (view.actions||[]).forEach(a=>{const g=svg.querySelector('.el[data-el="'+a.el+'"]');if(!g)return;
  g.setAttribute('data-click','action');if(state.onAction){g.style.cursor='pointer';g.addEventListener('click',()=>state.onAction(a));}});
 clouds(svg,view);
 // DETAILS: a boundary that opens as a detail is the region at a larger scale, as a drawing's detail view is. The whole
 // shows each such region closed, with how many parts it holds; opened, the drawing is cropped to it, the rest hidden.
 const det=(view.details||[]).find(d=>d.el===(root.dataset.detail||''));
 if(det){const [x,y,w,hh]=det.box,m=14,W0=((svg.getAttribute('viewBox')||'').split(/[ ,]+/).map(Number)[2])||(w+2*m);
  /* a detail is drawn at most 1.6 times the whole's scale: larger, and a reader scrolls to see what it was opened for */
  const vw=Math.max(w+2*m,W0/1.6);svg.setAttribute('viewBox',(x+w/2-vw/2)+' '+(y-m)+' '+vw+' '+(hh+2*m));
  const keep=new Set(det.inside.concat([det.el]));svg.querySelectorAll('.el').forEach(g=>{if(!keep.has(g.dataset.el))g.style.display='none';});
  closeDetails(root,svg,view,state,(view.details||[]).filter(d=>det.inside.includes(d.el)));
  root.insertAdjacentHTML('afterbegin','<div class="vw-detail-of">detail of <b>'+h(det.label)+'</b> · <a href="#" class="vw-back">back to the whole</a></div>');
  root.querySelector('.vw-back').addEventListener('click',ev=>{ev.preventDefault();delete root.dataset.detail;mount(root,view,state);});}
 else{const inner=new Set((view.details||[]).flatMap(d=>d.inside));closeDetails(root,svg,view,state,(view.details||[]).filter(d=>!inner.has(d.el)));
  links(svg,view);}
 // ZOOM: an element that opens a drawing of its own takes the reader there — a lens holds its limit by opening, not crowding
 (view.opens||[]).forEach(o=>{const g=svg.querySelector('.el[data-el="'+o.el+'"]');if(!g)return;
  g.classList.add('opens');g.setAttribute('data-opens',o.view);
  if(state.onOpen){g.style.cursor='zoom-in';g.addEventListener('click',()=>state.onOpen(o.view));}});}

/* ---------------- operate · the health chain, the fallback ---------------- */
function spark(pts,w,hh){if(!pts||pts.length<2)return '';const ys=pts.map(p=>+p[1]),mn=Math.min(...ys),mx=Math.max(...ys),r=(mx-mn)||1;
 return '<svg class="spark" viewBox="0 0 '+w+' '+hh+'" preserveAspectRatio="none"><polyline points="'+
  pts.map((p,i)=>(i/(pts.length-1)*w).toFixed(1)+','+(hh-2-((+p[1]-mn)/r)*(hh-4)).toFixed(1)).join(' ')+'"/></svg>';}
function histLink(view,state){return state.historyUrl?'<div><a href="'+h(state.historyUrl)+'/d/'+h(view.uid)+'" target="_blank" rel="noopener">history ↗</a></div>':'';}
function chain(root,view,lv,state){const vals=state.values||{},hist=state.history||{};
 const bind={};(view.binds||[]).forEach(b=>bind[b.id]=b);
 let o=head(view,lv)+'<div class="vw-chain">';
 (view.tiles||[]).forEach((t,i)=>{
  if(t.blind){o+='<div class="vw-tile blind" data-tile="'+i+'"><div class="bar"></div><div class="tname">'+h(t.label)+'</div><div class="tstate">no signal</div><div class="tsub">'+h(t.why)+'</div></div>';return;}
  const bs=t.binds.map(id=>bind[id]).filter(Boolean);let worst='up',o2='';
  bs.forEach(b=>{const v=vals[b.id],st=stateOf(b,v,state.live);
   if(st==='down')worst='down';else if(st==='warn'&&worst!=='down')worst='warn';else if(st==='nd'&&worst==='up')worst='nd';
   if(b.live==='live-value')o2+='<div class="meas"><span class="v">'+(state.live?fmt(v,b):'—')+'</span><span class="mn">'+h(b.short||b.name)+
    (b.warn!=null?' · warn '+fmt(b.warn,b):'')+'</span>'+spark(hist[b.id],120,22)+'</div>';});
  const word={up:'up',down:'DOWN',warn:'attention',nd:(state.live?'no data':ELSEWHERE)}[worst];
  const act=(view.actions||[]).filter(a=>a.el===t.el);
  o+='<div class="vw-tile '+worst+'" data-tile="'+i+'"><div class="bar"></div><div class="tname">'+h(t.label)+'</div><div class="tstate">'+word+'</div>'+o2+
   act.map(a=>'<button class="vw-act" data-act="'+h(a.el)+'">▶ '+h(a.label||a.tool)+'</button>').join('')+'</div>';
  if(i<(view.tiles.length-1))o+='<div class="vw-link"></div>';});
 o+='</div>';
 if(view.alerts&&view.alerts.length)o+='<div class="vw-alerts"><span>armed alerts</span>'+view.alerts.map(a=>'<span class="al">'+h(a)+'</span>').join('')+'</div>';
 root.innerHTML=o;
 root.querySelectorAll('.vw-tile').forEach(n=>{const t=view.tiles[+n.dataset.tile];
  inspectable(n,'tile:'+t.el,()=>{if(t.blind)return '<b>'+h(t.label)+'</b><div class="ins-sub">'+h(t.why)+'</div>'+partCard((view.facts||{})[t.bean]);
   return '<b>'+h(t.label)+'</b>'+t.binds.map(id=>{const b=bind[id];if(!b)return '';const v=vals[id];
    return '<div class="ins-row"><span>'+h(b.name)+'</span>'+(state.live?'<b>'+fmt(v,b)+'</b>':'offline')+(b.warn!=null?' · warn at '+fmt(b.warn,b):'')+(b.crit!=null?', critical at '+fmt(b.crit,b):'')+
     '<div class="ins-q">'+h(b.source||'')+'</div></div>';}).join('')+histLink(view,state);});});
 root.querySelectorAll('.vw-act').forEach(bn=>bn.addEventListener('click',e=>{e.stopPropagation();const a=(view.actions||[]).find(x=>x.el===bn.dataset.act);
  if(state.onAction)state.onAction(a);else alert('Actions run on the served page.');}));}

/* ---------------- inspect · anatomy ---------------- */
function wiringHtml(w){if(!w||!(w.pipes.length||w.processes.length))return '';
 const rails=[];[...w.pipes,...w.processes].forEach(r=>{const k=r.rail||'';if(!rails.includes(k))rails.push(k);});
 let o='<div class="vw-sub">the wiring — every pipe, where it listens, and the line of configuration that makes it · from [['+h(w.bean)+']]</div><div class="wr">';
 rails.forEach(rl=>{const ps=w.pipes.map((p,i)=>[p,i]).filter(([p])=>(p.rail||'')===rl),pr=w.processes.map((p,i)=>[p,i]).filter(([p])=>(p.rail||'')===rl);
  o+='<section class="wr-rail"><h4>'+h(rl||'—')+'</h4>'+
   (ps.length?'<table class="wr-t"><tbody>'+ps.map(([p,i])=>'<tr class="'+h(p.state||'')+'" data-wp="'+i+'"><td class="wr-ft"><b>'+h(p.from)+'</b> <span class="wr-k">'+h(p.channel)+'</span> <b>'+h(p.to)+'</b></td><td><code>'+h(p.at)+'</code></td><td class="wr-c">'+h(p.config)+'</td></tr>').join('')+'</tbody></table>':'')+
   (pr.length?'<div class="wr-procs">'+pr.map(([p,i])=>'<span class="wr-p '+h(p.state||'')+'" data-wq="'+i+'"><b>'+h(p.proc)+'</b> <i>'+h(p.user)+'</i></span>').join('')+'</div>':'')+'</section>';});
 return o+'</div>';}
function wireWiring(root,w){if(!w)return;
 root.querySelectorAll('[data-wp]').forEach(n=>{const p=w.pipes[+n.dataset.wp];inspectable(n,'wp:'+n.dataset.wp,()=>'<b>'+h(p.from)+' → '+h(p.to)+'</b><div class="ins-sub">'+h(p.channel)+' · '+h(p.at)+'</div><div class="ins-row"><span>config</span>'+h(p.config)+'</div>'+(p.note?'<div class="ins-row">'+h(p.note)+'</div>':'')+(p.state?'<div class="ins-row"><span>state</span>'+h(p.state)+'</div>':''));});
 root.querySelectorAll('[data-wq]').forEach(n=>{const p=w.processes[+n.dataset.wq];inspectable(n,'wq:'+n.dataset.wq,()=>'<b>'+h(p.proc)+'</b><div class="ins-sub">runs as '+h(p.user)+'</div><div class="ins-row">'+h(p.role)+'</div><div class="ins-row"><span>config</span>'+h(p.config)+'</div>'+(p.note?'<div class="ins-row">'+h(p.note)+'</div>':'')+(p.state?'<div class="ins-row"><span>state</span>'+h(p.state)+'</div>':''));});}
function anatomy(root,view,lv){let o=head(view,lv)+wiringHtml(view.wiring)+'<div class="vw-cards">';
 (view.parts||[]).forEach((p,i)=>{o+='<article class="vw-card2" data-part="'+i+'"><header><b>'+h(p.bean)+'</b><span class="genos">'+h(p.genos)+'</span><span class="org">'+h(p.org||'no organisation')+'</span></header>'+
  (p.role?'<div class="role">'+h(p.role)+'</div>':'')+
  (p.anchors.length?'<section><span>identity</span>'+p.anchors.map(a=>'<code'+(a.establishing?' class="est"':'')+'>'+h(a.key)+' = '+h(a.value)+'</code>').join(' ')+'</section>':'')+
  (p.addresses.length?'<section><span>addresses</span>'+p.addresses.map(a=>'<code>'+h(a.address)+'</code> <i>'+h((a.what||[]).join(' · '))+'</i>').join('<br>')+'</section>':'')+
  (p.rows&&p.rows.length?'<section><span>facts</span>'+p.rows.map(r=>'<i>'+h(r[0])+'</i> '+h(r[1])).join('<br>')+'</section>':'')+
  (p.tech.length?'<section><span>runs</span>'+p.tech.map(techChip).join('')+'</section>':'')+
  '<section><span>provenance</span>'+h(p.provenance)+'</section>'+
  (p.open.length?'<section class="open"><span>open</span>'+p.open.map(x=>'⚠ '+h(x)).join('<br>')+'</section>':'')+'</article>';});
 o+='</div>';
 if(view.steps&&view.steps.length)o+='<div class="vw-sub">step by step — '+h(view.source||'')+'</div><ol class="vw-steps2">'+
  view.steps.map(s=>'<li><div>'+h(s.text)+'</div>'+(s.parts.length?'<div class="touch">'+s.parts.map(b=>'<span class="pchip">'+h(b)+'</span>').join('')+'</div>':'')+'</li>').join('')+'</ol>';
 root.innerHTML=o;wireWiring(root,view.wiring);
 const T={};(view.parts||[]).forEach(p=>p.tech.forEach(t=>T[t.code]=t));
 root.querySelectorAll('.vw-card2').forEach(card=>card.querySelectorAll('.vw-tech').forEach(a=>
  inspectable(a,'tech:'+a.dataset.tech+':'+card.dataset.part,()=>techCard(T[a.dataset.tech]))));
 root.querySelectorAll('.vw-card2 header b').forEach(n=>{const p=view.parts[+n.closest('.vw-card2').dataset.part];
  inspectable(n,'part:'+p.bean,()=>'<b>'+h(p.bean)+'</b><div class="ins-sub">ledger record beans/'+h(p.bean)+'.md</div><div class="ins-row"><span>provenance</span>'+h(p.provenance)+'</div>');});}


/* ---------------- operate · archetypes ----------------
   Each drawing answers ITS OWN operational question in the shape native to it; the health chain is the fallback.
   view.operate = {archetype, …what the shape reads, as binding ids, notes:[..], blind:[..]} */
function V(state,id){return (state.values||{})[id];}
function B(view,id){return (view.binds||[]).find(b=>b.id===id)||{};}
function stateWord(st,live){return {up:'up',down:'DOWN',warn:'attention',nd:(live?'no data':ELSEWHERE)}[st];}
function dot(st){return '<i class="dot '+st+'"></i>';}
function opFoot(view,op,state){let o=corrHtml(view,op,state);
 const acts=view.actions||[];
 if(acts.length)o+='<div class="op-acts">'+acts.map(a=>'<button class="vw-act" data-act="'+h(a.el)+'">▶ '+h(a.label||a.tool)+'</button>').join('')+'</div>';
 if((op.notes||[]).length)o+='<ul class="op-notes">'+op.notes.map(n=>'<li>'+h(n)+'</li>').join('')+'</ul>';
 if((op.blind||[]).length)o+='<div class="op-blind"><span>what this page cannot see</span><ul>'+op.blind.map(n=>'<li>'+h(n)+'</li>').join('')+'</ul></div>';
 if(view.alerts&&view.alerts.length)o+='<div class="vw-alerts"><span>alerts that watch this</span>'+view.alerts.map(a=>'<span class="al">'+h(a)+'</span>').join('')+'</div>';
 return o;}
function wireActs(root,view,state){wireCorr(root,view,state);root.querySelectorAll('.vw-act').forEach(bn=>bn.addEventListener('click',e=>{e.stopPropagation();
 const a=(view.actions||[]).find(x=>x.el===bn.dataset.act);if(state.onAction)state.onAction(a);else alert('Actions run on the served page.');}));}
function evidence(view,state,ids){return '<div class="op-ev">'+ids.map(id=>{const b=B(view,id),v=V(state,id),st=stateOf(b,v,state.live);
 return '<span class="ev '+st+'" data-ev="'+h(id)+'">'+dot(st)+h(b.short||b.name)+(b.live==='live-value'?' <b>'+(state.live?fmt(v,b):'—')+'</b>':'')+'</span>';}).join('')+'</div>';}
function evInspect(root,view,state){root.querySelectorAll('[data-ev]').forEach(n=>{const b=B(view,n.dataset.ev);
 inspectable(n,'ev:'+b.id,()=>'<b>'+h(b.name)+'</b><div class="ins-row"><span>now</span>'+(state.live?fmt(V(state,b.id),b):'offline')+'</div><div class="ins-q">'+h(b.source||'')+'</div>');});}
function winText(view){const w=view.window||{};return w.hours?('last '+(w.hours%1?w.hours:w.hours.toFixed(0))+' h'):'';}

/* reservoir: a store filling toward its thresholds. The fill is read as a share of the whole, by its unit. */
function reservoir(root,view,lv,state,op){const lb=B(view,op.fill),v=V(state,op.fill),live=state.live&&v!=null;
 const pct=live?Math.max(0,Math.min(100,pctOf(lb,+v))):null,H=220,Wd=150;
 let svg='<svg class="tank" viewBox="0 0 '+(Wd+90)+' '+(H+20)+'"><rect x="10" y="10" width="'+Wd+'" height="'+H+'" rx="18" class="tank-shell"/>';
 if(pct!=null){const fh=H*pct/100,st=stateOf(lb,v,true);svg+='<rect x="10" y="'+(10+H-fh)+'" width="'+Wd+'" height="'+fh+'" rx="18" class="tank-fill '+st+'"/>';}
 (op.thresholds||[]).forEach((g,i)=>{const y=10+H-H*g.at/100;svg+='<line x1="4" x2="'+(Wd+16)+'" y1="'+y+'" y2="'+y+'" class="gate-line"/><text x="'+(Wd+22+(i%2)*44)+'" y="'+(y+4)+'" class="gate-t">'+h(num(g.at))+'%</text>';});
 svg+='<text x="'+(10+Wd/2)+'" y="'+(10+H/2+10)+'" text-anchor="middle" class="tank-v">'+(pct!=null?fmt(pct,PCT):'—')+'</text></svg>';
 const fb=B(view,op.forecast),fv=op.forecast?V(state,op.forecast):null;let fc='';
 if(op.forecast){const s=fb.q==='duration'?coherent(fb,+fv):+fv;fc=!state.live||fv==null||isNaN(fv)?'—':(s<0||s>3650*86400?'not filling':fmt(fv,fb));}
 let o=head(view,lv)+'<div class="op-res"><div class="op-tank">'+svg+'</div><div class="op-side">'+
  ((op.thresholds||[]).length?'<div class="op-gates">'+op.thresholds.map(g=>'<div class="gt '+(pct!=null&&pct>=g.at?'past':'')+'"><b>'+h(num(g.at))+'%</b><span>'+h(g.label)+'</span><em>'+(pct==null?'':pct>=g.at?'passed':(g.at-pct).toFixed(1)+' points away')+'</em></div>').join('')+'</div>':'')+
  (op.forecast?'<div class="big"><span class="bv">'+fc+'</span><span class="bl">'+h(fb.name||'to the next threshold')+'</span></div>':'')+
  (state.history&&state.history[op.fill]?'<div class="big"><span class="bl">'+h(lb.name)+', '+h(winText(view))+'</span>'+spark(state.history[op.fill],260,46)+'</div>':'')+
  ((op.also||[]).length?'<div class="bl">also filling</div>'+evidence(view,state,op.also):'')+
  ((op.parts||[]).length?'<div class="bl">the parts</div>'+evidence(view,state,op.parts):'')+'</div></div>';
 root.innerHTML=o+opFoot(view,op,state);evInspect(root,view,state);wireActs(root,view,state);}

function lanes(root,view,lv,state,op){let o=head(view,lv)+'<div class="op-lanes">';
 (op.lanes||[]).forEach((ln,i)=>{let worst='up',at=null;
  const hops=ln.hops.map(hp=>{const b=B(view,hp.bind),st=hp.bind?stateOf(b,V(state,hp.bind),state.live):'nd';
   if(st==='down'&&worst!=='down'){worst='down';at=hp.label;}else if(st==='nd'&&worst==='up')worst='nd';return {hp,st};});
  const verdict=worst==='down'?'blocked at '+h(at):worst==='up'?'getting through':(state.live?'partly unknown':ELSEWHERE);
  o+='<div class="lane '+worst+'"><div class="ln-name">'+h(ln.name)+'</div><div class="ln-hops">'+hops.map((x,k)=>
   (k?'<span class="ln-link '+x.st+'"></span>':'')+'<span class="hop '+x.st+'" data-hop="'+i+'-'+k+'"><i></i><em>'+h(x.hp.label)+'</em></span>').join('')+
   '</div><div class="ln-verdict">'+verdict+'</div></div>';});
 o+='</div>';root.innerHTML=o+opFoot(view,op,state);
 root.querySelectorAll('[data-hop]').forEach(n=>{const [i,k]=n.dataset.hop.split('-').map(Number),hp=op.lanes[i].hops[k],b=B(view,hp.bind);
  inspectable(n,'hop:'+n.dataset.hop,()=>'<b>'+h(hp.label)+'</b><div class="ins-sub">'+h(op.lanes[i].name)+'</div>'+(hp.bind?'<div class="ins-row"><span>'+h(b.name)+'</span>'+stateWord(stateOf(b,V(state,hp.bind),state.live),state.live)+'</div><div class="ins-q">'+h(b.source||'')+'</div>':'<div class="ins-sub">no signal</div>'));});
 wireActs(root,view,state);}

function itemName(b,n){return ((b.item_names||{})[n])||n;}
function roster(root,view,lv,state,op){const sb=B(view,op.per_item),rows=(V(state,op.per_item)||[]).slice().sort((a,b)=>b.value-a.value);
 const over=op.active_over||0,top=op.top||12,act=rows.filter(r=>r.value>=over),idle=rows.length-act.length;
 let o=head(view,lv)+'<div class="op-roster"><div class="ro-head"><span class="bv">'+(state.live?act.length:'—')+'</span><span class="bl">active now'+(state.live?' of '+rows.length:'')+'</span></div>';
 if(!state.live)o+='<p class="bl">The roster is '+ELSEWHERE+'.</p>';
 const show=act.length>=top?act:rows.slice(0,Math.max(act.length,Math.min(top,rows.length))),mx2=Math.max(1,...show.map(r=>r.value));
 if(state.live&&!act.length&&rows.length)o+='<div class="bl">nothing above the threshold — the busiest:</div>';
 show.slice(0,top).forEach((r,i)=>{const idl=r.value<over;o+='<div class="ro-row'+(idl?' idle':'')+'" data-ro="'+i+'"><span class="ro-n">'+h(itemName(sb,r.name))+'</span><span class="ro-bar"><i style="width:'+(100*r.value/mx2).toFixed(1)+'%"></i></span><span class="ro-v">'+fmt(r.value,sb)+'</span></div>';});
 if(act.length>top)o+='<div class="bl">and '+(act.length-top)+' more active</div>';
 if(state.live&&idle)o+='<div class="bl">'+idle+' idle (below '+fmt(over,sb)+')</div>';
 o+='</div>'+((op.parts||[]).length?'<div class="bl">the parts</div>'+evidence(view,state,op.parts):'');
 root.innerHTML=o+opFoot(view,op,state);evInspect(root,view,state);wireActs(root,view,state);}

function arc(v,min,max,warn,crit,b,name){const a=(x)=>Math.PI*(1-(Math.max(min,Math.min(max,x))-min)/((max-min)||1));
 const P=(ang,r)=>[70+r*Math.cos(ang),72-r*Math.sin(ang)];const seg=(x0,x1,cls)=>{const [ax,ay]=P(a(x0),56),[bx,by]=P(a(x1),56);return '<path d="M'+ax+','+ay+' A56,56 0 0 1 '+bx+','+by+'" class="'+cls+'"/>';};
 const w=warn==null?max:warn,c=crit==null?max:crit;
 const st=v==null?'nd':v>=c&&crit!=null?'down':v>=w&&warn!=null?'warn':'up',[nx,ny]=P(a(v==null?min:v),48);
 return '<svg class="arc" viewBox="0 0 140 96">'+seg(min,w,'arc-ok')+seg(w,c,'arc-warn')+seg(c,max,'arc-crit')+
  (v!=null?'<line x1="70" y1="72" x2="'+nx+'" y2="'+ny+'" class="needle '+st+'"/>':'')+'<circle cx="70" cy="72" r="4" class="hub"/>'+
  '<text x="70" y="92" text-anchor="middle" class="arc-v '+st+'">'+fmt(v,b)+'</text></svg><div class="arc-n">'+h(name)+'</div>';}
function gauges(root,view,lv,state,op){const sb=B(view,op.per_item),rows=(V(state,op.per_item)||[]).slice().sort((a,b)=>a.name<b.name?-1:1);
 let o=head(view,lv)+'<div class="op-gauges">';
 if(!state.live||!rows.length)o+='<p class="bl">'+(state.live?'no readings':'The gauges are '+ELSEWHERE+'.')+'</p>';
 rows.forEach((r,i)=>{o+='<div class="gauge" data-g="'+i+'">'+arc(r.value,op.min||0,op.max==null?100:op.max,sb.warn,sb.crit,sb,itemName(sb,r.name))+'</div>';});
 o+='</div>';root.innerHTML=o+opFoot(view,op,state);
 root.querySelectorAll('[data-g]').forEach(n=>{const r=rows[+n.dataset.g];inspectable(n,'g:'+r.name,()=>'<b>'+h(itemName(sb,r.name))+'</b><div class="ins-row"><span>item</span><code>'+h(r.name)+'</code></div><div class="ins-row"><span>now</span>'+fmt(r.value,sb)+(sb.warn!=null?' · warn '+fmt(sb.warn,sb):'')+(sb.crit!=null?' · critical '+fmt(sb.crit,sb):'')+'</div>');});
 wireActs(root,view,state);}

function board(root,view,lv,state,op){let o=head(view,lv);
 if((op.facts||[]).length)o+='<div class="op-facts">'+op.facts.map(id=>{const b=B(view,id);return '<div class="big" data-ev="'+h(id)+'"><span class="bv">'+(state.live?fmt(V(state,id),b):'—')+'</span><span class="bl">'+h(b.name)+'</span></div>';}).join('')+'</div>';
 o+='<div class="op-board">'+(op.items||[]).map((it,i)=>{let worst='up';(it.binds||[]).forEach(id=>{const st=stateOf(B(view,id),V(state,id),state.live);if(st==='down')worst='down';else if(st==='nd'&&worst==='up')worst='nd';});
  if(!(it.binds||[]).length)worst='blind';
  const fact=it.fact?(state.live?fmt(V(state,it.fact),B(view,it.fact)):'—')+' '+h(B(view,it.fact).name||''):'';
  return '<div class="dev '+worst+'" data-dev="'+i+'">'+dot(worst==='blind'?'nd':worst)+'<span class="dv-n">'+h(it.label)+'</span><span class="dv-s">'+(worst==='blind'?'no signal':stateWord(worst,state.live))+'</span>'+((worst==='blind'?it.why:fact)?'<span class="dv-f">'+(worst==='blind'?h(it.why):fact)+'</span>':'')+'</div>';}).join('')+'</div>';
 root.innerHTML=o+opFoot(view,op,state);evInspect(root,view,state);
 root.querySelectorAll('[data-dev]').forEach(n=>{const it=op.items[+n.dataset.dev];inspectable(n,'dev:'+n.dataset.dev,()=>'<b>'+h(it.label)+'</b>'+(it.binds||[]).map(id=>{const b=B(view,id);return '<div class="ins-row"><span>'+h(b.name)+'</span>'+stateWord(stateOf(b,V(state,id),state.live),state.live)+'<div class="ins-q">'+h(b.source||'')+'</div></div>';}).join('')+((it.binds||[]).length?'':'<div class="ins-sub">'+h(it.why||'nothing measures it')+'</div>')+partCard((view.facts||{})[it.bean]));});
 wireActs(root,view,state);}

function scoreboard(root,view,lv,state,op){let o=head(view,lv)+'<div class="op-facts">'+(op.numbers||[]).map(id=>{const b=B(view,id),v=V(state,id),st=stateOf(b,v,state.live);
 return '<div class="big '+st+'" data-ev="'+h(id)+'"><span class="bv">'+(state.live?fmt(v,b):'—')+'</span><span class="bl">'+h(b.name)+'</span></div>';}).join('')+'</div>';
 if(op.list){const lb=B(view,op.list),rows=V(state,op.list)||[];o+='<div class="op-firing">'+(!state.live?'<p class="bl">What is firing is '+ELSEWHERE+'.</p>':
  rows.length?'<div class="bl">firing now</div>'+rows.map(r=>'<div class="fire">'+dot('down')+h(itemName(lb,r.name))+'</div>').join(''):'<div class="calm">'+dot('up')+'nothing is firing</div>')+'</div>';}
 if((op.parts||[]).length)o+='<div class="bl">the watcher\'s own parts</div>'+evidence(view,state,op.parts);
 root.innerHTML=o+opFoot(view,op,state);evInspect(root,view,state);wireActs(root,view,state);}


/* funnel: a stream narrowing through its stages. Each stage is a bar (square-root scaled, so a large first stage and a
   small last one share one page and the narrowing still shows), the count and what it counts; where the rest stopped
   branches off below it, with the reason; what was marked on the way sits beside it. Below: the headline numbers and a
   ROLL CALL of the parts, each up or down, and the items known to carry nothing. */
function funnel(root,view,lv,state,op){const live=state.live,val=id=>live?V(state,id):null;
 const cnt=s=>s.static!=null?s.static:val(s.count);   // a stage counts a live value, or the members of a reading (drawn with the page)
 const L=x=>Math.sqrt(Math.max(0,+x||0));
 let o=head(view,lv);
 if((op.numbers||[]).length)o+='<div class="op-facts">'+op.numbers.map(id=>{const b=B(view,id),v=val(id),st=stateOf(b,v,live);
  return '<div class="big '+st+'" data-ev="'+h(id)+'"><span class="bv">'+(live?fmt(v,b):'—')+'</span><span class="bl">'+h(b.name)+'</span></div>';}).join('')+'</div>';
 (op.funnels||[]).forEach((f,fi)=>{const mx=Math.max(1,...f.stages.map(s=>L(cnt(s))));
  o+='<div class="fun"><div class="fun-h"><b>'+h(f.name)+'</b>'+(op.window?'<span>'+h(op.window)+'</span>':'')+'</div><div class="fun-row">';
  f.stages.forEach((s,si)=>{const v=cnt(s),b=s.static!=null?{}:B(view,s.count),w=v!=null?Math.max(4,100*L(v)/mx):0;
   o+=(si?'<div class="fun-arrow">→</div>':'')+'<div class="fun-st" data-fs="'+fi+'-'+si+'"><div class="fun-bar"><i style="height:'+w.toFixed(1)+'%"></i></div>'+
    '<div class="fun-n">'+(v!=null?fmt(v,b):'—')+'</div><div class="fun-l">'+h(s.label)+'</div>'+(s.counts?'<div class="fun-u">'+h(s.counts)+'</div>':'')+
    (s.marks||[]).map((mk,mi)=>{const mv=val(mk.bind);return '<div class="fun-mark" data-fm="'+fi+'-'+si+'-'+mi+'">'+(live?fmt(mv,B(view,mk.bind)):'—')+' '+h(mk.label)+'</div>';}).join('')+
    (s.stops||[]).map((sp,pi)=>{const sv=val(sp.bind),hit=live&&sv>0;return '<div class="fun-stop'+(hit?' hit':'')+'" data-fp="'+fi+'-'+si+'-'+pi+'">↓ '+(live?fmt(sv,B(view,sp.bind)):'—')+' '+h(sp.label)+'</div>';}).join('')+'</div>';});
  o+='</div></div>';});
 (op.rollcall||[]).forEach((rc,ri)=>{const rb=B(view,rc.per_item),rows=(val(rc.per_item)||[]).slice().sort((a,b)=>a.name<b.name?-1:1),idle=new Set(rc.idle||[]);
  o+='<div class="rc"><div class="bl">'+h(rc.label)+(live?' — '+rows.filter(r=>r.value>=1).length+' of '+rows.length+' up':'')+'</div><div class="rc-row">'+
   (live?rows.map((r,i)=>{const st=idle.has(r.name)?'idle':(r.value>=1?'up':'down');return '<span class="rc-c '+st+'" data-rc="'+ri+'-'+i+'">'+dot(st==='idle'?'nd':st)+h(itemName(rb,r.name))+(r.value>1?' <b>×'+r.value+'</b>':'')+'</span>';}).join(''):'<span class="bl">'+ELSEWHERE+'</span>')+'</div></div>';
  rc._rows=rows;});
 root.innerHTML=o+opFoot(view,op,state);evInspect(root,view,state);wireActs(root,view,state);
 const src=id=>'<div class="ins-q">'+h(B(view,id).source||'')+'</div>';
 root.querySelectorAll('[data-fs]').forEach(n=>{const [fi,si]=n.dataset.fs.split('-').map(Number),s=op.funnels[fi].stages[si];
  inspectable(n,'fs:'+n.dataset.fs,()=>'<b>'+h(s.label)+'</b><div class="ins-sub">'+h(op.funnels[fi].name)+(s.counts?' · counted in '+h(s.counts):'')+'</div>'+(s.what?'<div class="ins-row">'+h(s.what)+'</div>':'')+src(s.count));});
 root.querySelectorAll('[data-fp]').forEach(n=>{const [fi,si,pi]=n.dataset.fp.split('-').map(Number),sp=op.funnels[fi].stages[si].stops[pi];
  inspectable(n,'fp:'+n.dataset.fp,()=>'<b>stopped: '+h(sp.label)+'</b>'+(sp.what?'<div class="ins-row">'+h(sp.what)+'</div>':'')+src(sp.bind));});
 root.querySelectorAll('[data-fm]').forEach(n=>{const [fi,si,mi]=n.dataset.fm.split('-').map(Number),mk=op.funnels[fi].stages[si].marks[mi];
  inspectable(n,'fm:'+n.dataset.fm,()=>'<b>'+h(mk.label)+'</b>'+(mk.what?'<div class="ins-row">'+h(mk.what)+'</div>':'')+src(mk.bind));});
 root.querySelectorAll('[data-rc]').forEach(n=>{const [ri,i]=n.dataset.rc.split('-').map(Number),rc=op.rollcall[ri],r=rc._rows[i],nt=(rc.notes||{})[r.name];
  inspectable(n,'rc:'+n.dataset.rc,()=>'<b>'+h(itemName(B(view,rc.per_item),r.name))+'</b><div class="ins-row"><span>now</span>'+(r.value>=1?(r.value>1?r.value+' running':'up'):'not found')+'</div>'+(nt?'<div class="ins-row">'+h(nt)+'</div>':'')+src(rc.per_item));});}

/* race: a run of a procedure against its deadline — the step it is at (a step of the procedure the view draws: 0
   before the first, n at the n-th), how long it has run, how long it still needs, and the verdict. The bar is time:
   what has run (solid), what it still needs (hatched), the deadline and the checkpoints (ticks). Before the first step,
   or past the last, nothing is in progress, and the verdict says so, calmly. */
function secs(b,v){return v==null?null:(b&&b.q==='duration'?coherent(b,+v):+v);}
function race(root,view,lv,state,op){const live=state.live,val=id=>live&&id?V(state,id):null;
 const steps=op.steps||[],sv=val(op.step_at),stepN=sv==null?null:Math.round(+sv);
 const el=secs(B(view,op.elapsed),val(op.elapsed)),eta=secs(B(view,op.eta),val(op.eta));
 const dl=op.deadline!=null?+op.deadline:secs(B(view,op.deadline_from),val(op.deadline_from));
 const pb=B(view,op.progress),pv=val(op.progress),pr=pv==null?null:(pb.q==='ratio'?coherent(pb,+pv):+pv);
 const busy=live&&stepN!=null&&stepN>=1&&stepN<=steps.length;
 let verdict,vst;
 if(!live){verdict=ELSEWHERE;vst='nd';}
 else if(stepN==null){verdict='no data';vst='nd';}
 else if(!busy){verdict='nothing in progress';vst='up';}
 else if(eta!=null&&eta>=0&&el!=null&&dl){const fin=el+eta;
  if(fin<=dl){verdict='done in about '+dur(eta)+' — '+dur(dl-fin)+' before the deadline';vst='up';}
  else{verdict='cut in '+dur(Math.max(dl-el,0))+' unless it ends — it needs about '+dur(eta)+' more';vst='down';}}
 else if(el!=null&&dl){verdict=dur(el)+' of '+dur(dl)+' used; how long it still needs is not known';vst=el>=0.8*dl?'warn':'up';}
 else{verdict='running';vst='up';}
 const stLabel=stepN==null?'—':busy?(stepN+' of '+steps.length+' · '+steps[stepN-1]):(stepN<1?'not started':'past the last step');
 const ph=busy?' busy ph'+(1+((stepN-1)%3)):' idle';
 let o=head(view,lv)+'<div class="op-race"><div class="rc-ph'+ph+'">'+h(stLabel)+'</div>'+
  '<div class="rc-verdict '+vst+'">'+dot(vst)+h(verdict)+'</div>';
 if(busy&&el!=null&&dl){const fin=el+(eta!=null&&eta>0?eta:0),top=Math.max(dl,fin,...(op.checkpoints||[]).map(g=>+g.at))*1.03,X=t=>(100*t/top).toFixed(2);
  o+='<div class="rc-bar"><i class="rc-el ph'+(1+((stepN-1)%3))+'" style="width:'+X(el)+'%"></i>'+(eta!=null&&eta>0?'<i class="rc-eta" style="left:'+X(el)+'%;width:'+X(eta)+'%"></i>':'')+
   '<i class="rc-dl" style="left:'+X(dl)+'%"></i>'+(op.checkpoints||[]).map(g=>'<i class="rc-gate" style="left:'+X(+g.at)+'%" title="'+h(g.label)+'"></i>').join('')+'</div>'+
   '<div class="rc-scale"><span>0</span><span>'+dur(el)+' so far'+(pr!=null&&pr>=0&&pr<=1?' · '+Math.round(pr*100)+'% done':'')+'</span><span>deadline '+dur(dl)+'</span></div>';
  if((op.checkpoints||[]).length)o+='<div class="rc-gates">'+op.checkpoints.map(g=>'<span class="'+(el>=+g.at?'past':'')+'"><b>'+dur(+g.at)+'</b> '+h(g.label)+(el>=+g.at?' — passed':'')+'</span>').join('')+'</div>';}
 if((op.numbers||[]).length)o+='<div class="op-facts">'+op.numbers.map(id=>{const b=B(view,id),v=val(id),st=stateOf(b,v,live);
  const shown=Array.isArray(v)?v.map(r=>h(itemName(b,r.name))+' '+fmt(r.value,b)).join(' · '):(live?fmt(v,b):'—');
  return '<div class="big '+st+'" data-ev="'+h(id)+'"><span class="bv">'+shown+'</span><span class="bl">'+h(b.name)+'</span></div>';}).join('')+'</div>';
 if((op.parts||[]).length)o+='<div class="bl">the parts</div>'+evidence(view,state,op.parts);
 o+='</div>';root.innerHTML=o+opFoot(view,op,state);evInspect(root,view,state);wireActs(root,view,state);}

/* correlate: any shape may add it. Several values on ONE time axis, stacked, so what moves together is seen together; a
   step value (`band`) shades every row by the step the run was at; a cursor reads every row at one moment. AGGREGATED
   beneath: each row's mean while the band held each step, and each step's share of the time; and `relate`: one value
   binned against another, over the time drawn — only while the band is at `at_step` where it names one, and only the
   moments it is above zero where it keeps `positive`. */
const PHC=['var(--nd)','var(--host)','var(--accent)','var(--svc)','var(--ext)','var(--store)'];
function atT(pts,t){let lo=0,hi=pts.length-1,k=-1;while(lo<=hi){const m=(lo+hi)>>1;if(pts[m][0]<=t){k=m;lo=m+1;}else hi=m-1;}return k<0?null:+pts[k][1];}
function hhmm(t){const d=new Date(t*1000);return String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');}
function corrHtml(view,op,state){return ((op&&op.correlate)||[]).map((c,ci)=>corrOne(view,c,ci,state)).join('');}
function corrOne(view,c,ci,state){if(!c||!(c.rows||[]).length)return '';
 const w=view.window||{};
 let o='<div class="op-corr" data-corr="'+ci+'"><div class="corr-h"><b>'+h(c.title||'Together, over time')+'</b>'+(w.hours?'<span>'+h(winText(view))+', every '+h(dur(w.step))+'</span>':'')+'</div>';
 if(!state.live)return o+'<p class="bl">drawn '+ELSEWHERE+', from its history</p></div>';
 const H=state.history||{},rows=c.rows.map(id=>({b:B(view,id),pts:(H[id]||[]).filter(p=>!isNaN(+p[1]))})).filter(r=>r.b.id),band=c.band?(H[c.band]||[]):[];
 const all=[].concat(...rows.map(r=>r.pts),band);if(all.length<2)return o+'<p class="bl">no history yet — it gathers as the page is open</p></div>';
 const t0=Math.min(...all.map(p=>+p[0])),t1=Math.max(...all.map(p=>+p[0])),Wd=960,L=150,R=84,RH=54,G=12,top=6,Hb=rows.length*(RH+G)-G,Ht=top+Hb+24;
 const x=t=>L+(t-t0)/((t1-t0)||1)*(Wd-L-R);let g='';
 for(let i=0;i<band.length;i++){const v=+band[i][1];if(isNaN(v))continue;const ta=+band[i][0],tb=i+1<band.length?+band[i+1][0]:t1;
  g+='<rect x="'+x(ta).toFixed(1)+'" y="'+top+'" width="'+Math.max(x(tb)-x(ta),0.6).toFixed(1)+'" height="'+Hb+'" class="corr-band" style="fill:'+PHC[Math.abs(v)%PHC.length]+'"/>';}
 rows.forEach((r,i)=>{const y0=top+i*(RH+G),vs=r.pts.map(p=>+p[1]),mn=Math.min(0,...vs),mx=Math.max(...vs,0),y=v=>y0+RH-(v-mn)/((mx-mn)||1)*RH;
  g+='<text x="'+(L-10)+'" y="'+(y0+RH/2+4)+'" class="corr-l" text-anchor="end">'+h(r.b.short||r.b.name)+'</text><line x1="'+L+'" x2="'+(Wd-R)+'" y1="'+(y0+RH)+'" y2="'+(y0+RH)+'" class="corr-ax"/>';
  if(r.pts.length>1){let d='';r.pts.forEach((p,k)=>{const X=x(+p[0]).toFixed(1),Y=y(+p[1]).toFixed(1);d+=k?'H'+X+'V'+Y:'M'+X+','+Y;});g+='<path d="'+d+'" class="corr-line"/>';}
  g+='<text x="'+(Wd-R+8)+'" y="'+(y0+10)+'" class="corr-max">max '+fmt(mx,r.b)+'</text><text x="'+(Wd-R+8)+'" y="'+(y0+RH/2+6)+'" class="corr-now">'+fmt(vs.length?vs[vs.length-1]:null,r.b)+'</text>';});
 const span=t1-t0,st=[60,300,600,900,1800,3600,7200,14400].find(s=>span/s<=8)||14400;
 for(let t=Math.ceil(t0/st)*st;t<=t1;t+=st)g+='<text x="'+x(t).toFixed(1)+'" y="'+(Ht-6)+'" class="corr-t" text-anchor="middle">'+hhmm(t)+'</text>';
 g+='<line class="corr-cur" x1="-9" x2="-9" y1="'+top+'" y2="'+(top+Hb)+'"/>';
 o+='<div class="corr-wrap"><svg class="corr" viewBox="0 0 '+Wd+' '+Ht+'" data-l="'+L+'" data-r="'+R+'" data-w="'+Wd+'" data-t0="'+t0+'" data-t1="'+t1+'">'+g+'</svg></div><div class="corr-read"></div>';
 const bands=c.bands||[];
 if(c.band&&bands.length)o+='<div class="corr-key">'+bands.map((lb,v)=>'<span><i style="background:'+PHC[v%PHC.length]+'"></i>'+h(lb)+'</span>').join('')+'</div>';
 if(band.length){const vals=[...new Set(band.map(p=>+p[1]).filter(v=>!isNaN(v)))].sort((a,b)=>a-b);
  o+='<div class="corr-sub">each value, averaged over the time each step held</div><div class="corr-aggw"><table class="corr-agg"><thead><tr><th></th>'+vals.map(v=>{const n=band.filter(p=>+p[1]===v).length;
   return '<th><i style="background:'+PHC[Math.abs(v)%PHC.length]+'"></i>'+h(bands[v]!=null?bands[v]:'= '+v)+'<em>'+Math.round(100*n/band.length)+'% of the time</em></th>';}).join('')+'</tr></thead><tbody>'+
   rows.map(r=>'<tr><td>'+h(r.b.short||r.b.name)+'</td>'+vals.map(v=>{const xs=band.filter(p=>+p[1]===v).map(p=>atT(r.pts,+p[0])).filter(z=>z!=null&&!isNaN(z));
    return '<td>'+(xs.length?fmt(xs.reduce((a,z)=>a+z,0)/xs.length,r.b):'—')+'</td>';}).join('')+'</tr>').join('')+'</tbody></table></div>';}
 const rl=c.relate;if(rl&&rl.across&&rl.measure&&H[rl.across]&&H[rl.measure]){const bx=B(view,rl.across),by=B(view,rl.measure),n=rl.bins||8;
  const pr=H[rl.measure].map(p=>[atT(H[rl.across],+p[0]),+p[1],+p[0]]).filter(p=>p[0]!=null&&!isNaN(p[1])&&(rl.at_step==null||atT(band,p[2])===+rl.at_step)&&(rl.keep!=='positive'||p[1]>0));
  o+='<div class="corr-sub">'+h(by.short||by.name)+' by '+h(bx.short||bx.name)+(rl.at_step!=null&&bands[rl.at_step]?', while '+h(bands[rl.at_step]):'')+' — binned, time-weighted</div>';
  if(pr.length<3)o+='<p class="bl">not enough history yet</p>';
  else{const a=Math.min(...pr.map(p=>p[0])),z=Math.max(...pr.map(p=>p[0])),wd=(z-a)/n||1,bins=Array.from({length:n},(_,k)=>({lo:a+k*wd,ys:[]}));
   pr.forEach(p=>bins[Math.min(n-1,Math.floor((p[0]-a)/wd))].ys.push(p[1]));
   const ms=bins.map(b=>b.ys.length?b.ys.reduce((s,v)=>s+v,0)/b.ys.length:null),top2=Math.max(...ms.filter(v=>v!=null),1e-9),BW=560,BH=120,bw=BW/n;
   let q='';bins.forEach((b,k)=>{const m=ms[k];if(m==null)return;const hh=BH*m/top2;
    q+='<rect x="'+(k*bw+3).toFixed(1)+'" y="'+(BH-hh+14).toFixed(1)+'" width="'+(bw-6).toFixed(1)+'" height="'+hh.toFixed(1)+'" class="rel-bar"><title>'+h(fmt(b.lo,bx)+' – '+fmt(b.lo+wd,bx)+': '+fmt(m,by)+' ('+b.ys.length+' samples)')+'</title></rect>'+
     '<text x="'+(k*bw+bw/2).toFixed(1)+'" y="'+(BH-hh+10).toFixed(1)+'" class="rel-v" text-anchor="middle">'+fmt(m,by)+'</text>';});
   q+='<text x="0" y="'+(BH+30)+'" class="corr-t">'+fmt(a,bx)+'</text><text x="'+BW+'" y="'+(BH+30)+'" class="corr-t" text-anchor="end">'+fmt(z,bx)+'</text>';
   o+='<svg class="rel" viewBox="-4 0 '+(BW+8)+' '+(BH+36)+'">'+q+'</svg>';}}
 return o+'</div>';}
function wireCorr(root,view,state){const op=view.operate;((op&&op.correlate)||[]).forEach((c,ci)=>{
 const box=root.querySelector('[data-corr="'+ci+'"]');if(!box)return;const sv=box.querySelector('svg.corr'),rd=box.querySelector('.corr-read');if(!sv||!rd)return;
 const H=state.history||{},L=+sv.dataset.l,R=+sv.dataset.r,Wd=+sv.dataset.w,t0=+sv.dataset.t0,t1=+sv.dataset.t1,cur=sv.querySelector('.corr-cur'),bands=c.bands||[];
 const show=ev=>{const bx=sv.getBoundingClientRect(),vx=(ev.clientX-bx.left)/bx.width*Wd;if(vx<L||vx>Wd-R){cur.setAttribute('x1',-9);cur.setAttribute('x2',-9);rd.innerHTML='';return;}
  const t=t0+(vx-L)/(Wd-L-R)*(t1-t0);cur.setAttribute('x1',vx);cur.setAttribute('x2',vx);
  const bv=c.band?atT(H[c.band]||[],t):null;
  rd.innerHTML='<b>'+hhmm(t)+'</b>'+(bv!=null?' · '+h(bands[bv]!=null?bands[bv]:'= '+bv):'')+' · '+c.rows.map(id=>{const b=B(view,id);return h(b.short||b.name)+' <b>'+fmt(atT(H[id]||[],t),b)+'</b>';}).join(' · ');};
 sv.addEventListener('mousemove',show);sv.addEventListener('mouseleave',()=>{cur.setAttribute('x1',-9);cur.setAttribute('x2',-9);rd.innerHTML='';});});}

/* table: the members of a reading, or the rows of a series, one line each with a column per path — the report, and the
   offline file of it (`dmview table` writes the same lines as CSV). Drawn with the page: nothing in it is live. */
function table(root,view,lv,state,op){const t=op.table||{columns:[],rows:[]};
 let o=head(view,lv)+'<div class="op-table"><table><thead><tr>'+t.columns.map(c=>'<th>'+h(c)+'</th>').join('')+'</tr></thead><tbody>'+
  (t.rows.length?t.rows.map(r=>'<tr>'+r.cells.map(c=>'<td>'+h(c)+'</td>').join('')+'</tr>').join(''):'<tr><td colspan="'+Math.max(1,t.columns.length)+'" class="bl">nothing to list</td></tr>')+
  '</tbody></table></div>';
 root.innerHTML=o+opFoot(view,op,state);wireActs(root,view,state);}

const ARCH={table:table,race:race,funnel:funnel,reservoir:reservoir,lanes:lanes,roster:roster,gauges:gauges,board:board,scoreboard:scoreboard};
function operate(root,view,lv,state){const op=view.operate;if(op&&ARCH[op.archetype])return ARCH[op.archetype](root,view,lv,state,op);chain(root,view,lv,state);
 if(op&&(op.correlate||[]).length){const d=document.createElement('div');d.innerHTML=opFoot(view,{correlate:op.correlate,notes:op.notes,blind:op.blind},state);root.appendChild(d);wireCorr(root,view,state);}}
const FORMS={story:story,schematic:schematic,'health-chain':operate,anatomy:anatomy};
/* THE SHEET: every drawing is a sheet, and its title block is made of facts the ledger holds — the page, the drawing,
   the lens it is read at (its scale), the garden and its release, the commit it is drawn from and its day, who stated
   it, where it is shown, and which sheet of how many. Nothing in it is typed for the page. */
function titleBlock(view,lv){const s=view.sheet;if(!s)return '';
 const c=(k,v)=>'<div class="tb-c"><span class="tb-k">'+h(k)+'</span><span class="tb-v">'+h(v||'—')+'</span></div>';
 return '<div class="vw-tblock" role="contentinfo">'+c('page',s.page)+c('drawing',view.title&&view.title.replace(/<[^>]+>/g,'')||view.key)+
  c('lens',lv.name||lv.id)+c('sheet',s.n+' of '+s.of)+c('garden',s.garden+(s.release?' · '+s.release:''))+
  c('drawn from',(s.commit||'')+(s.day?' · '+s.day:''))+c('stated by',s.by)+c('shown at',s.shown)+'</div>';}
/* A DETAIL CLOSED: its region shows how many parts it holds, and opens on a click; the parts inside are hidden */
function closeDetails(root,svg,view,state,ds){ds.forEach(d=>{const g=svg.querySelector('.el[data-el="'+d.el+'"]');if(!g)return;
  const inside=new Set(d.inside);svg.querySelectorAll('.el').forEach(x=>{if(inside.has(x.dataset.el))x.style.display='none';});
  const [x,y,w,hh]=d.box,NS='http://www.w3.org/2000/svg',t=document.createElementNS(NS,'text');
  t.setAttribute('x',x+w/2);t.setAttribute('y',y+hh/2+4);t.setAttribute('text-anchor','middle');t.setAttribute('class','vw-closed');
  const kinds=new Map((view.elements||[]).map(e=>[e.id,e.pattern])),n=d.inside.filter(i=>!['flow','signal','band','boundary','label'].includes(kinds.get(i))).length;
  t.textContent=n+(n===1?' part':' parts');const u=t.cloneNode();u.setAttribute('y',y+hh/2+18);u.setAttribute('class','vw-closed vw-open-hint');
  u.textContent='open the detail';g.appendChild(t);g.appendChild(u);g.classList.add('opens');g.style.cursor='zoom-in';
  g.addEventListener('click',ev=>{ev.stopPropagation();root.dataset.detail=d.el;mount(root,view,state);});});}
/* THE LINKS OF CLOSED REGIONS: the flows between two closed regions are one line a pair, saying how many it carries */
function links(svg,view){const L=view.links||[];if(!L.length)return;const box={};(view.elements||[]).forEach(e=>{if(e.box)box[e.id]=e.box;});
 (view.details||[]).forEach(d=>box[d.el]=d.box);
 const NS='http://www.w3.org/2000/svg',gone=new Set(L.flatMap(l=>l.flows)),used={};
 svg.querySelectorAll('.el').forEach(g=>{if(gone.has(g.dataset.el))g.style.display='none';});
 const inner=new Set((view.details||[]).flatMap(d=>d.inside)),closed=(view.details||[]).filter(d=>!inner.has(d.el)).map(d=>d.box),FR=[0.5,0.3,0.7,0.2,0.8,0.4,0.6];
 /* a place along the shared side: clear of a crossed region's own words, and of a line already there */
 const slot=(k,lo,hi,v,a,b)=>{const taken=used[k]=used[k]||[];const at=f=>lo+(hi-lo)*f;
  const f=FR.find(f=>!taken.includes(f)&&!closed.some(c=>c!==a&&c!==b&&(v?Math.abs(at(f)-(c[0]+c[2]/2))<64&&Math.min(a[1],b[1])<c[1]+c[3]/2&&c[1]+c[3]/2<Math.max(a[1]+a[3],b[1]+b[3])
   :Math.abs(at(f)-(c[1]+c[3]/2))<22&&Math.min(a[0],b[0])<c[0]+c[2]/2&&c[0]+c[2]/2<Math.max(a[0]+a[2],b[0]+b[2]))))??FR.find(f=>!taken.includes(f))??0.5;
  taken.push(f);return at(f);};
 /* edge to edge, square to the sheet: across the gap two boxes share a side over, else one bend */
 const route=(a,b)=>{const [ax,ay,aw,ah]=a,[bx,by,bw,bh]=b,lo=Math.max(ax,bx),hi=Math.min(ax+aw,bx+bw),vlo=Math.max(ay,by),vhi=Math.min(ay+ah,by+bh);
  if(hi-lo>8){const x=slot('x'+lo+'.'+hi,lo,hi,1,a,b);return by>=ay+ah?[[x,ay+ah],[x,by]]:[[x,ay],[x,by+bh]];}
  if(vhi-vlo>8){const y=slot('y'+vlo+'.'+vhi,vlo,vhi,0,a,b);return bx>=ax+aw?[[ax+aw,y],[bx,y]]:[[ax,y],[bx+bw,y]];}
  const sx=bx>=ax+aw?ax+aw:ax,cy=ay+ah/2,cx=bx+bw/2;return [[sx,cy],[cx,cy],[cx,by>ay?by:by+bh]];};
 L.forEach(l=>{const a=box[l.from],b=box[l.to];if(!a||!b)return;const pts=route(a,b),ln=document.createElementNS(NS,'polyline');
  ln.setAttribute('points',pts.map(p=>p.join(',')).join(' '));ln.setAttribute('fill','none');
  ln.setAttribute('class','edge vw-link');ln.setAttribute('marker-end','url(#ah-d)');if(l.both)ln.setAttribute('marker-start','url(#ah-d)');svg.appendChild(ln);
  if(l.flows.length>1||l.label){const m=pts.length>2?pts[1]:[(pts[0][0]+pts[1][0])/2,(pts[0][1]+pts[1][1])/2],t=document.createElementNS(NS,'text');
   const flat=pts[0][1]===pts[pts.length-1][1];t.setAttribute('x',m[0]+(flat?0:5));t.setAttribute('y',m[1]+(flat?-5:4));
   t.setAttribute('text-anchor',flat?'middle':'start');t.setAttribute('class','flab');t.textContent=l.flows.length>1?l.flows.length+' flows':l.label;svg.appendChild(t);}});}
/* REVISION CLOUDS: a part whose record the last commit changed is drawn inside a cloud, as a revised drawing is */
function clouds(svg,view){const ids=view.changed||[];if(!ids.length)return;const by={};(view.elements||[]).forEach(e=>by[e.id]=e);
 const NS='http://www.w3.org/2000/svg';ids.forEach(id=>{const e=by[id];if(!e||!e.box)return;const [x,y,w,hh]=e.box,p=7;
  const r=document.createElementNS(NS,'rect');r.setAttribute('x',x-p);r.setAttribute('y',y-p);r.setAttribute('width',w+2*p);
  r.setAttribute('height',hh+2*p);r.setAttribute('rx',14);r.setAttribute('class','revcloud');
  const t=document.createElementNS(NS,'text');t.setAttribute('x',x+w+p-2);t.setAttribute('y',y-p+10);t.setAttribute('class','revmark');
  t.textContent='Δ';svg.appendChild(r);svg.appendChild(t);});}
function mount(root,view,state){state=state||{};const lvs=view.levels||[];
 const lv=lvs.find(l=>l.id===state.level)||lvs.find(l=>+l.depth===+state.level)||lvs[0]||{form:'schematic',name:'',question:''};
 root.classList.add('vw');root.dataset.form=lv.form;
 (FORMS[lv.form]||schematic)(root,view,lv,state);root.insertAdjacentHTML('beforeend',titleBlock(view,lv));reattach(root);}
W.viewMount=mount;W.viewInspector={show:insShow,hide:insHide};
})();
