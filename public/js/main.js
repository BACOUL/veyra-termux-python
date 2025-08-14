async function getJSON(url, opts={}) {
  const r = await fetch(url, { headers:{'Content-Type':'application/json', ...(opts.headers||{})}, ...opts });
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}
function el(html){ const t=document.createElement('template'); t.innerHTML=html.trim(); return t.content.firstChild; }
function copyTxt(t){ return navigator.clipboard?.writeText(t); }
function fmtDate(s){ try{ return new Date(s).toLocaleString(); }catch{ return s; } }
function idk(){ return Date.now().toString(36)+Math.random().toString(36).slice(2,10); }

/* toast minimal */
function toast(msg){
  let t=document.getElementById('toast');
  if(!t){
    t=document.createElement('div'); t.id='toast';
    Object.assign(t.style,{
      position:'fixed', right:'16px', bottom:'16px', zIndex:9999,
      background:'rgba(0,0,0,.82)', color:'#E5F3F0',
      padding:'10px 12px', borderRadius:'12px',
      border:'1px solid #2a3344', fontSize:'14px',
      boxShadow:'0 12px 28px rgba(0,194,168,.18)', transition:'opacity .25s'
    });
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.style.opacity = '1';
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(()=>{ t.style.opacity='0'; }, 1800);
}
