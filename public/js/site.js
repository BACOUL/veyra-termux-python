(()=>{ 
  const p=location.pathname||'/';
  document.querySelectorAll('nav a').forEach(a=>{
    const m=a.getAttribute('data-match')||a.getAttribute('href');
    if(m && p.startsWith(m)) a.classList.add('active');
  });
  const y=new Date().getFullYear();
  document.querySelectorAll('[data-year]').forEach(e=>e.textContent=y);
})();
