const CACHE_NAME='lol-analytics-study-atlas-v2-20260930';
const OFFLINE_URL='./index.html';

self.addEventListener('install',event=>{
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate',event=>{
  event.waitUntil(
    caches.keys()
      .then(keys=>Promise.all(keys.filter(k=>k.startsWith('lol-analytics-study-atlas')&&k!==CACHE_NAME).map(k=>caches.delete(k))))
      .then(()=>self.clients.claim())
  );
});

self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET') return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin) return;

  // Always prefer network for documents and V2 lesson parts.
  if(request.mode==='navigate'||request.destination==='document'||url.pathname.includes('/assets/study-atlas-v2/')){
    event.respondWith(
      fetch(request,{cache:'no-store'})
        .then(response=>{
          if(response&&response.ok){
            const clone=response.clone();
            caches.open(CACHE_NAME).then(cache=>cache.put(request,clone));
          }
          return response;
        })
        .catch(()=>caches.match(request).then(r=>r||caches.match(OFFLINE_URL)))
    );
    return;
  }

  event.respondWith(fetch(request).catch(()=>caches.match(request)));
});