const C='veyra-v1'; const ASSETS=['/','/app','/benchmarks','/public/css/globals.css','/public/js/main.js','/public/favicon.svg'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(ASSETS)))});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(u.pathname.startsWith('/public/')){ e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(resp=>{const cp=resp.clone(); caches.open(C).then(c=>c.put(e.request,cp)); return resp;}))); }
});
