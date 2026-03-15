const API = "";

function fmtPrice(p){if(p==null)return"—";if(p>=1000)return"$"+p.toLocaleString("en-US",{maximumFractionDigits:2});if(p>=1)return"$"+p.toFixed(4);return"$"+p.toFixed(8)}
function fmtChange(c){if(c==null)return"—";return(c>=0?"+":"")+c.toFixed(2)+"%"}
function badge(d){const m={bullish:"badge-bullish",bearish:"badge-bearish",neutral:"badge-neutral"};return`<span class="badge ${m[d]||'badge-neutral'}">${d}</span>`}
function scorePill(s){return`<span class="score-pill">${s}</span>`}
function ago(ts){const d=new Date(ts+"Z"),diff=Math.floor((Date.now()-d)/1000);if(diff<60)return diff+"s ago";if(diff<3600)return Math.floor(diff/60)+"m ago";if(diff<86400)return Math.floor(diff/3600)+"h ago";return Math.floor(diff/86400)+"d ago"}
async function api(path){const r=await fetch(API+path);if(!r.ok)throw new Error(r.status);return r.json()}

function signalTable(signals){
  if(!signals.length)return`<div class="empty">No signals found.</div>`;
  const rows=signals.map(s=>`<tr onclick="location.href='/coin/${s.coin}'">
    <td><strong>${s.coin}</strong></td><td>${s.signal_type}</td>
    <td>${badge(s.direction)}</td><td>${s.timeframe}</td>
    <td>${scorePill(s.score)}</td><td>${ago(s.timestamp)}</td>
  </tr>`).join("");
  return`<div style="overflow-x:auto"><table class="signal-table"><thead><tr>
    <th>Coin</th><th>Signal</th><th>Direction</th><th>TF</th><th>Score</th><th>Time</th>
  </tr></thead><tbody>${rows}</tbody></table></div>`;
}

async function loadDashboard(){
  try{
    const[overview,strong,signals,gainers,losers]=await Promise.all([
      api("/api/market_overview"),api("/api/strong_signals"),
      api("/api/signals?limit=30"),api("/api/top_gainers"),api("/api/top_losers")
    ]);
    const sc=overview.signal_counts;
    document.querySelector("#stat-total   .stat-number").textContent=sc.total;
    document.querySelector("#stat-bullish .stat-number").textContent=sc.bullish;
    document.querySelector("#stat-bearish .stat-number").textContent=sc.bearish;
    document.querySelector("#stat-strong  .stat-number").textContent=strong.length;

    document.getElementById("strong-signals").innerHTML=strong.length
      ?strong.map(s=>`<div class="signal-card ${s.direction}" onclick="location.href='/coin/${s.coin}'">
          <div class="coin-sym">${s.coin} ${scorePill(s.score)}</div>
          <div class="sig-type">${s.signal_type}</div>
          <div>${badge(s.direction)}</div>
          <div class="sig-meta">${s.timeframe} · ${ago(s.timestamp)}</div>
        </div>`).join("")
      :`<div class="empty">No strong signals in the last 24h.</div>`;

    document.getElementById("latest-signals").innerHTML=signalTable(signals);

    function moverHTML(coins){return coins.map(c=>{
      const cls=(c.change_24h||0)>=0?"up":"down";
      return`<div class="mover-row" onclick="location.href='/coin/${c.symbol}'">
        <span class="mover-sym">${c.symbol}</span>
        <span>${fmtPrice(c.price)}</span>
        <span class="mover-change ${cls}">${fmtChange(c.change_24h)}</span>
      </div>`;}).join("");}
    document.getElementById("top-gainers").innerHTML=moverHTML(gainers);
    document.getElementById("top-losers").innerHTML=moverHTML(losers);

    ["filter-timeframe","filter-direction"].forEach(id=>{
      document.getElementById(id)?.addEventListener("change",loadFilteredSignals);
    });
  }catch(e){console.error(e);}
}

async function loadFilteredSignals(){
  const tf=document.getElementById("filter-timeframe")?.value||"";
  const dir=document.getElementById("filter-direction")?.value||"";
  const p=new URLSearchParams({limit:50});
  if(tf)p.append("timeframe",tf);if(dir)p.append("direction",dir);
  try{const s=await api(`/api/signals?${p}`);
    document.getElementById("latest-signals").innerHTML=signalTable(s);}
  catch(e){console.error(e);}
}

async function loadScanner(){
  const tf=document.getElementById("filter-timeframe")?.value||"";
  const dir=document.getElementById("filter-direction")?.value||"";
  const score=document.getElementById("filter-score")?.value||"0";
  const p=new URLSearchParams({limit:100,min_score:score});
  if(tf)p.append("timeframe",tf);if(dir)p.append("direction",dir);
  try{const s=await api(`/api/signals?${p}`);
    document.getElementById("scanner-results").innerHTML=signalTable(s);}
  catch(e){console.error(e);}
}

async function loadCoinPage(symbol){
  try{
    const{coin,signals}=await api(`/api/coin/${symbol}`);
    document.querySelector("#coin-price  .stat-number").textContent=fmtPrice(coin.price);
    document.querySelector("#coin-change .stat-number").textContent=fmtChange(coin.change_24h);
    document.querySelector("#coin-volume .stat-number").textContent=
      coin.volume_24h?"$"+(coin.volume_24h/1e6).toFixed(1)+"M":"—";
    document.getElementById("coin-subtitle").textContent=coin.name;
    if((coin.change_24h||0)>=0)document.getElementById("coin-change").classList.add("bullish-card");
    else document.getElementById("coin-change").classList.add("bearish-card");
    document.getElementById("coin-signals").innerHTML=signalTable(signals);
  }catch(e){
    console.error(e);
    document.getElementById("coin-signals").innerHTML=`<div class="empty">Could not load data.</div>`;
  }
}
