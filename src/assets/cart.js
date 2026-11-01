/* Branded on-site cart. Items live in this browser's localStorage (one cart per site); checkout hands the whole
   basket to Shopify as a multi-item cart permalink: /cart/V1:Q1,V2:Q2?attributes[Storefront]=... */
(function(){
  const C=window.NI_CART;if(!C)return;
  const $=(s,r)=>(r||document).querySelector(s),$$=(s,r)=>[...(r||document).querySelectorAll(s)];
  const money=v=>'$'+Number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const ga=(n,p)=>{try{if(typeof window.gtag==='function')window.gtag('event',n,p)}catch(_){}};   // GA4, never blocks the cart
  const gaItem=x=>({item_id:String(x.v),item_name:String(x.t||'')+(x.vt&&x.vt!=='Default Title'?' - '+x.vt:''),price:+x.p||0,quantity:+x.q||1,...(x.c?{item_category:x.c}:{})});
  const KEY='ni_cart_v1:'+C.domain,HARD_MAX=99,FRESH=10*60*1000;
  let items=load();
  function load(){try{const a=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(a)?a.filter(x=>x&&x.v&&x.q>0):[]}catch(e){return[]}}
  function save(){try{localStorage.setItem(KEY,JSON.stringify(items))}catch(e){}paint()}
  window.addEventListener('storage',e=>{if(e.key===KEY){items=load();paint()}});
  const cap=x=>Math.max(1,Math.min(HARD_MAX,x.max>0?x.max:HARD_MAX));
  const live=()=>items.filter(x=>!x.out);
  const count=()=>items.reduce((n,x)=>n+x.q,0);
  const subtotal=()=>live().reduce((s,x)=>s+x.p*x.q,0);
  function checkoutUrl(){
    const parts=live().map(x=>x.v+':'+Math.min(x.q,cap(x)));if(!parts.length)return'';
    return C.shop+'/cart/'+parts.join(',')+C.attr+'&attributes%5BSite%5D='+encodeURIComponent(C.domain)+'&note='+encodeURIComponent('Ordered on '+C.brand+' ('+C.domain+')')+'&ref='+encodeURIComponent(C.ref);
  }
  window.NI_CART_URL=checkoutUrl;
  function add(d,q){
    q=q||1;let x=items.find(y=>String(y.v)===String(d.v));
    if(x){x.q=Math.min(cap(x),x.q+q);x.out=false}
    else{x={v:String(d.v),h:d.h,t:d.t,vt:d.vt||'',p:+d.p,i:d.i||'',q:1,max:+d.max||0,c:d.c||'',ts:0};x.q=Math.min(cap(x),q);items.push(x)}
    save();check([x],true);return x;
  }
  // live price / stock from the Shopify store (same public endpoint the product pages use)
  const pend={};
  function check(list,force){
    const now=Date.now();
    const hs=[...new Set(list.filter(x=>force||now-(x.ts||0)>FRESH).map(x=>x.h))];
    return Promise.all(hs.map(h=>pend[h]||(pend[h]=fetch(C.shop+'/products/'+encodeURIComponent(h)+'.js').then(r=>r.ok?r.json():Promise.reject(r.status)).then(p=>{
      items.filter(x=>x.h===h).forEach(x=>{const v=p.variants.find(v=>String(v.id)===String(x.v));x.ts=Date.now();
        if(!v){x.out=true;return}x.p=v.price/100;x.out=!v.available;const m=v.quantity_rule&&v.quantity_rule.max;x.max=m>0?m:(x.max||0);x.q=Math.min(x.q,cap(x))})
    }).catch(()=>{}).finally(()=>{delete pend[h]})))).then(()=>{if(hs.length)save()});
  }
  // cross-sells: best sellers from the same aisle that can be added in one tap
  let _cat=null;const catalog=()=>_cat||(_cat=fetch('/data/catalog.json').then(r=>r.json()).catch(()=>[]));
  function suggest(n){
    return catalog().then(d=>{
      const inCart=new Set(items.map(x=>x.h)),last=items[items.length-1],aisle=last&&last.c;
      const ok=d.filter(x=>x.v&&!x.x&&!/no-photo/.test(x.i)&&!inCart.has(x.h));
      let pool=aisle?ok.filter(x=>x.c!==aisle):ok;if(pool.length<n)pool=ok;   // pair with a different aisle (holder for sticks, etc.)
      const pref=C.pair&&last&&C.pair[last.k];if(pref){const p2=ok.filter(x=>pref.includes(x.k));if(p2.length>=n)pool=p2}
      return pool.slice().sort((a,b)=>a.r-b.r||a.p-b.p).slice(0,40).sort(()=>Math.random()-.5).slice(0,n);
    });
  }
  // ---------- rendering ----------
  const drawer=$('#cart'),dim=$('.cdim'),pageBox=$('[data-cart-page]');
  function rowHtml(x){
    const m=cap(x),title=x.t+(x.vt&&x.vt!=='Default Title'?' – '+x.vt:'');
    return `<li class="ci${x.out?' isout':''}" data-v="${esc(x.v)}"><a class="cimg" href="/products/${esc(x.h)}/" tabindex="-1" aria-hidden="true">${x.i?`<img src="${esc(x.i.replace(/width=\d+/,'width=160'))}" alt="" width="72" height="72" loading="lazy">`:''}</a>
<div class="cimeta"><a class="cit" href="/products/${esc(x.h)}/">${esc(title)}</a><span class="cip">${money(x.p)} each</span>${x.out?'<span class="ciout">Sold out online, so it is left out of checkout. Call us, it may be on the shelf.</span>':''}
<div class="cq"><button type="button" data-dec aria-label="Decrease quantity of ${esc(title)}"${x.q<=1?' disabled':''}>&minus;</button><input type="number" inputmode="numeric" min="1" max="${m}" value="${x.q}" aria-label="Quantity of ${esc(title)}" data-qty><button type="button" data-inc aria-label="Increase quantity of ${esc(title)}"${x.q>=m||x.out?' disabled':''}>+</button><button type="button" class="crm" data-rm aria-label="Remove ${esc(title)} from cart">Remove</button></div>
${x.max>0&&x.q>=x.max?`<span class="cimax">Limit ${x.max} per order</span>`:''}</div><b class="cil">${money(x.p*x.q)}</b></li>`;
  }
  function html(){
    const n=count(),url=checkoutUrl(),pick=C.pickup?`<div class="cpick"><b>Free pickup inside Namaste Bookshop, ${esc(C.street)}</b><span>Choose <b>Pickup</b> at checkout and collect it inside Namaste Bookshop, 2 W 14th St, near Union Square. No shipping fee.${C.ready?' '+esc(C.ready)+'.':''}</span></div>`:`<div class="cpick"><b>Collect it at ${esc(C.street)}</b><span>Choose pickup at checkout if it is offered for your items, or ship from New York City.</span></div>`;
    if(!items.length)return `<div class="cempty"><p>Your cart is empty.</p><a class="btn" href="/shop/">Start shopping</a></div>${pick}<div class="cups" data-ups></div>`;
    return `<ul class="clist">${items.map(rowHtml).join('')}</ul>
<div class="csum"><div class="crow"><span>Subtotal (${live().reduce((a,x)=>a+x.q,0)} item${n===1?'':'s'})</span><b>${money(subtotal())}</b></div><p class="small">Shipping and tax are shown at checkout.</p></div>
${pick}${url?`<a class="btn ccheck" href="${esc(url)}" rel="nofollow" data-checkout>Check out</a>`:'<span class="btn ccheck" aria-disabled="true">Check out</span>'}
<p class="csec">Secure Shopify checkout through ${esc(C.shopName)}, the store that ships and holds your pickup.</p>
<a class="clink" href="/shop/" data-cart-close>Keep shopping</a><div class="cups" data-ups></div>`;
  }
  let upsKey=null,upsHtml='',upsP=null;
  function upsells(box){
    const u=$('[data-ups]',box);if(!u)return;const k=items.map(x=>x.h).join('|');
    if(k===upsKey){if(upsP)upsP.then(()=>{const w=$('[data-ups]',box);if(w)w.innerHTML=upsHtml});else u.innerHTML=upsHtml;return}
    upsKey=k;upsHtml='';
    upsP=suggest(3).then(xs=>{upsP=null;if(!xs.length)return;upsHtml=`<h3>${esc(items.length?C.pairTitle:'Popular right now')}</h3><ul>${xs.map(x=>`<li><a href="/products/${esc(x.h)}/"><img src="${esc(x.i.replace(/width=\d+/,'width=160'))}" alt="" width="56" height="56" loading="lazy"><span>${esc(x.t)}</span></a><b>${money(x.p)}</b><button type="button" class="cadd" data-atc data-v="${x.v}" data-h="${esc(x.h)}" data-t="${esc(x.t)}" data-p="${x.p}" data-i="${esc(x.i)}" data-c="${esc(x.c)}" data-k="${esc(x.k)}" aria-label="Add ${esc(x.t)} to cart">Add</button></li>`).join('')}</ul>`;const w=$('[data-ups]',box);if(w)w.innerHTML=upsHtml});
  }
  function fill(box){const a=document.activeElement,sel=a&&box.contains(a)&&a.closest('[data-v]')&&[a.closest('[data-v]').dataset.v,[...a.attributes].find(t=>/^data-(inc|dec|qty)$/.test(t.name))];
    $('[data-cart-body]',box).innerHTML=html();upsells(box);
    if(sel&&sel[1]){const el=$(`[data-v="${CSS.escape(sel[0])}"] [${sel[1].name}]`,box);if(el&&!el.disabled)el.focus()}}
  function paint(){
    const n=count();$$('[data-cart-count]').forEach(b=>{b.textContent=n>99?'99+':n;b.hidden=!n});
    $$('[data-cart-open]').forEach(b=>b.setAttribute('aria-label',`Cart, ${n} item${n===1?'':'s'}`));
    if(drawer&&!drawer.hidden)fill(drawer);if(pageBox)fill(pageBox);
  }
  // ---------- drawer ----------
  let back=null;
  function open(msg){
    if(pageBox){pageBox.scrollIntoView({behavior:'smooth'});say(msg);return}
    if(!drawer)return;back=document.activeElement;drawer.hidden=false;dim.hidden=false;fill(drawer);
    requestAnimationFrame(()=>{drawer.classList.add('on');dim.classList.add('on')});document.documentElement.classList.add('cart-open');
    say(msg);$('.cx',drawer).focus();check(items);
  }
  function close(){if(!drawer||drawer.hidden)return;drawer.classList.remove('on');dim.classList.remove('on');document.documentElement.classList.remove('cart-open');
    setTimeout(()=>{drawer.hidden=true;dim.hidden=true},220);if(back&&back.focus)back.focus()}
  function say(m){const s=pageBox?$('.cmsg',pageBox):$('#cmsg');if(s){s.textContent='';if(m)setTimeout(()=>s.textContent=m,30)}}
  document.addEventListener('keydown',e=>{if(!drawer||drawer.hidden)return;if(e.key==='Escape'){close();return}
    if(e.key==='Tab'){const f=$$('a[href],button:not([disabled]),input,select',drawer).filter(el=>el.offsetParent);if(!f.length)return;
      if(e.shiftKey&&document.activeElement===f[0]){f[f.length-1].focus();e.preventDefault()}else if(!e.shiftKey&&document.activeElement===f[f.length-1]){f[0].focus();e.preventDefault()}}});
  document.addEventListener('click',e=>{
    const t=e.target.closest('[data-atc],[data-atc-items],[data-cart-open],[data-cart-close],[data-inc],[data-dec],[data-rm],[data-checkout]');if(!t)return;
    if(t.hasAttribute('data-checkout')){const u=checkoutUrl();if(u)t.href=u;try{const l=live();if(l.length)ga('begin_checkout',{currency:'USD',value:Math.round(subtotal()*100)/100,items:l.map(gaItem),transport_type:'beacon'})}catch(_){}return}
    if(t.hasAttribute('data-cart-open')){e.preventDefault();open();return}
    if(t.hasAttribute('data-cart-close')){if(drawer&&!drawer.hidden){e.preventDefault();close()}return}
    if(t.hasAttribute('data-atc')||t.hasAttribute('data-atc-items')){e.preventDefault();if(t.disabled||t.getAttribute('aria-disabled')==='true')return;
      let list;try{list=t.hasAttribute('data-atc-items')?JSON.parse(t.getAttribute('data-atc-items')):[t.dataset]}catch(_){return}
      list.forEach(d=>add(d,+(d.q||1)));
      try{const gi=list.map(d=>gaItem({v:d.v,t:d.t,vt:d.vt,p:d.p,q:+(d.q||1),c:d.c}));ga('add_to_cart',{currency:'USD',value:Math.round(gi.reduce((s,x)=>s+x.price*x.quantity,0)*100)/100,items:gi})}catch(_){}
      const lab=t.textContent;t.classList.add('added');t.textContent='Added ✓';setTimeout(()=>{t.textContent=lab;t.classList.remove('added')},1600);
      open(list.length>1?`Added ${list.length} items to your cart.`:`Added ${list[0].t} to your cart.`);return}
    const row=t.closest('[data-v]');const x=row&&items.find(y=>String(y.v)===row.dataset.v);if(!x)return;
    if(t.hasAttribute('data-rm')){items=items.filter(y=>y!==x);say(`Removed ${x.t}.`)}
    else if(t.hasAttribute('data-inc'))x.q=Math.min(cap(x),x.q+1);
    else if(t.hasAttribute('data-dec'))x.q=Math.max(1,x.q-1);
    save();
  });
  document.addEventListener('change',e=>{const t=e.target;if(!t.hasAttribute||!t.hasAttribute('data-qty'))return;const row=t.closest('[data-v]');const x=row&&items.find(y=>String(y.v)===row.dataset.v);if(!x)return;
    const v=parseInt(t.value,10);if(!v||v<1){items=items.filter(y=>y!==x)}else x.q=Math.min(cap(x),v);save()});
  paint();if(pageBox)check(items);
})();
