/* header that shrinks / hides on scroll (mobile), recently viewed, sticky mobile add-to-cart, bundles */
(function(){
  const $=(s,r)=>(r||document).querySelector(s),$$=(s,r)=>[...(r||document).querySelectorAll(s)];
  const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money=v=>'$'+Number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  if($('.shop'))document.documentElement.classList.add('has-shop');
  const top=$('.top');
  if(top){let last=scrollY,tick=false;const mq=matchMedia('(max-width:999px)');
    const run=()=>{tick=false;const y=scrollY;
      if(!mq.matches){top.classList.remove('compact','hide');last=y;return}
      top.classList.toggle('compact',y>140);
      if(document.body.classList.contains('open')||document.documentElement.classList.contains('cart-open'))top.classList.remove('hide');
      else if(y>last+6&&y>220)top.classList.add('hide');else if(y<last-6||y<=220)top.classList.remove('hide');
      last=y};
    addEventListener('scroll',()=>{if(!tick){tick=true;requestAnimationFrame(run)}},{passive:true});
    top.addEventListener('focusin',()=>top.classList.remove('hide'))}
  const P=window.NI_PRODUCT,RV='ni_rv_v1';let rv=[];
  try{rv=JSON.parse(window.localStorage.getItem(RV)||'[]')}catch(e){rv=[]}
  if(P&&P.handle){rv=[P.handle,...rv.filter(h=>h!==P.handle)].slice(0,12);try{window.localStorage.setItem(RV,JSON.stringify(rv))}catch(e){}}
  const box=$('[data-recent]');
  if(box){const want=rv.filter(h=>!P||h!==P.handle).slice(0,8);
    if(want.length)fetch('/data/catalog.json').then(r=>r.json()).then(d=>{const by=new Map(d.map(x=>[x.h,x]));const xs=want.map(h=>by.get(h)).filter(Boolean);if(!xs.length)return;
      box.innerHTML='<div class="sechead"><h2>Recently viewed</h2></div><div class="rvrow">'+xs.map(x=>'<a class="rv" href="/products/'+esc(x.h)+'/"><img src="'+esc(x.i.replace(/width=\d+/,'width=200'))+'" alt="" width="120" height="120" loading="lazy"><span>'+esc(x.t)+'</span><b>'+money(x.p)+'</b></a>').join('')+'</div>';box.hidden=false}).catch(()=>{})}
  const buy=$('#buy'),bar=$('.stickybuy');
  if(buy&&bar&&'IntersectionObserver' in window){
    const sb=$('button',bar),pr=$('[data-sb-price]',bar),src=$('#price');
    const sync=()=>{sb.disabled=buy.disabled;sb.textContent=buy.disabled?'Sold out':'Add to cart';if(src&&pr)pr.textContent=src.textContent};
    sb.addEventListener('click',()=>{if(!buy.disabled)buy.click()});
    new MutationObserver(sync).observe(buy,{attributes:true,childList:true,characterData:true,subtree:true});sync();
    new IntersectionObserver(es=>{const off=!es[0].isIntersecting&&es[0].boundingClientRect.top<0;bar.classList.toggle('on',off);document.body.classList.toggle('sb-on',off)}).observe(buy)}
  const st=$('#stock'),ins=$('.instore');
  if(st&&ins)new MutationObserver(()=>{ins.hidden=st.classList.contains('out')}).observe(st,{attributes:true});
  $$('.bundle').forEach(bx=>{const btn=$('[data-bundle]',bx),tot=$('[data-bundle-total]',bx);if(!btn)return;const all=JSON.parse(btn.getAttribute('data-bundle'));
    const upd=()=>{const on=$$('input[type=checkbox]',bx).map((c,i)=>c.checked?all[i]:null).filter(Boolean);btn.setAttribute('data-atc-items',JSON.stringify(on));btn.disabled=!on.length;
      tot.textContent=money(on.reduce((s,x)=>s+Number(x.p),0));btn.textContent=on.length>1?'Add all '+on.length+' to cart':'Add to cart'};
    bx.addEventListener('change',upd);upd()});
})();
