/* Google Analytics 4 events for the storefronts. Every call is guarded: if gtag is blocked or missing, nothing breaks.
   view_item on product pages, generate_lead on call / email / booking / directions / claim-listing links.
   add_to_cart and begin_checkout are sent from cart.js. */
(function(){
  function ga(n,p){try{if(typeof window.gtag==='function')window.gtag('event',n,p||{})}catch(_){}}
  window.niGA=ga;
  try{
    if(/^\/products\//.test(location.pathname)){
      var b=document.getElementById('buy'),it=null;
      if(b&&b.dataset&&b.dataset.v){var d=b.dataset;it={item_id:String(d.v),item_name:d.t+(d.vt&&d.vt!=='Default Title'?' - '+d.vt:''),price:+d.p||0,quantity:1};if(d.c)it.item_category=d.c}
      else{[].forEach.call(document.querySelectorAll('script[type="application/ld+json"]'),function(s){if(it)return;try{var j=JSON.parse(s.textContent);(Array.isArray(j)?j:[j]).forEach(function(o){if(!it&&o&&o['@type']==='Product'){var of=Array.isArray(o.offers)?o.offers[0]:(o.offers||{});it={item_id:String(o.sku||location.pathname.split('/')[2]),item_name:o.name,price:+of.price||0,quantity:1}}})}catch(_){}})}
      if(it)ga('view_item',{currency:'USD',value:it.price,items:[it]});
    }
  }catch(_){}
  var BOOK=/(book\.squareup\.com|squareup\.com\/appointments|square\.site|setmore\.com|calendly\.com|acuityscheduling\.com|as\.me\/|vagaro\.com|booksy\.com|schedulicity\.com|simplybook|fresha\.com|\/book-a-reading|\/booking)/i,
      MAPS=/(google\.[a-z.]+\/maps|maps\.google\.|goo\.gl\/maps|maps\.app\.goo\.gl|maps\.apple\.com)/i;
  function kind(a){
    var h=a.getAttribute('href')||'';
    if(/^tel:/i.test(h))return'phone';
    if(/^mailto:/i.test(h))return/^mailto:claim@/i.test(h)?'claim':'email';
    var u;try{u=new URL(h,location.href)}catch(_){return''}
    if(u.origin===location.origin&&/^\/claim(\/|$)/.test(u.pathname))return'claim';
    if(MAPS.test(u.href))return'directions';
    if(BOOK.test(u.href)||(u.origin!==location.origin&&/^\s*book\b/i.test(a.textContent||'')))return'booking';
    return'';
  }
  document.addEventListener('click',function(e){try{
    var a=e.target&&e.target.closest&&e.target.closest('a[href]');if(!a)return;var k=kind(a);if(!k)return;
    ga('generate_lead',{link_type:k,link_url:(a.getAttribute('href')||'').slice(0,200),link_text:(a.textContent||'').trim().replace(/\s+/g,' ').slice(0,100),transport_type:'beacon'});
  }catch(_){}},true);
})();
