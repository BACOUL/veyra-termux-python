async function getJSON(url, opts={}) {
  const r = await fetch(url, { headers:{'Content-Type':'application/json', ...(opts.headers||{})}, ...opts });
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}
function el(html){ const t=document.createElement('template'); t.innerHTML=html.trim(); return t.content.firstChild; }
function copyTxt(t){ return navigator.clipboard?.writeText(t); }
function fmtDate(s){ try{ return new Date(s).toLocaleString(); }catch{ return s; } }
function idk(){ return Date.now().toString(36)+Math.random().toString(36).slice(2,10); }
