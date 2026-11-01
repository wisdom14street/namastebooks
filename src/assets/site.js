(function(){
  const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
  const money=v=>'$'+Number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  let _cat=null;const catalog=()=>_cat||(_cat=Promise.all([fetch('/data/catalog.json').then(r=>r.json()),fetch('/data/meta.json').then(r=>r.json())]));
  // menu
  const mb=$('.menu');if(mb)mb.onclick=()=>{const o=document.body.classList.toggle('open');mb.setAttribute('aria-expanded',String(o))};
  // filter helpers shared by shop + quiz
  function match(x,f){if(!f)return true;
    if(f.aisle&&!f.aisle.includes(x.c))return false;if(f.base&&!f.base.includes(x.k))return false;if(f.fam&&!f.fam.includes(x.f))return false;
    if(f.brand&&!f.brand.includes(x.b))return false;if(f.style&&!f.style.includes(x.s))return false;
    if(f.maxp!=null&&x.p>=f.maxp)return false;if(f.minp!=null&&x.p<f.minp)return false;if(f.multi&&!x.m)return false;if(f.gift&&!x.g)return false;
    if(f.q&&!new RegExp(f.q,'i').test(x.t))return false;return true}
  const card0=(x,m)=>`<a class="card" href="/products/${x.h}/"><div class="ph"><img loading="lazy" decoding="async" src="${esc(x.i)}" alt="${esc(x.t)}" width="400" height="400"></div><div class="meta"><span class="tag" style="--c:${m.aisles[x.c].color}">${esc(x.f?m.fams[x.f]:m.aisles[x.c].name)}</span><h3>${esc(x.t)}</h3><p class="price">${x.n>1?'<small>'+x.n+' options from</small> ':''}${x.o?'<s>'+money(x.o)+'</s> ':''}${money(x.p)}</p></div></a>`;
  const atc=x=>x.v?`<button type="button" class="atc" data-atc data-v="${x.v}" data-h="${esc(x.h)}" data-t="${esc(x.t)}" data-p="${x.p}" data-i="${esc(x.i)}" data-c="${esc(x.c)}" data-k="${esc(x.k)}" aria-label="Add ${esc(x.t)} to cart">Add to cart</button>`:`<a class="atc" href="/products/${esc(x.h)}/" aria-label="Choose options for ${esc(x.t)}">Choose options</a>`;
  const card=(x,m)=>card0(x,m).replace('<a class="card" ','<div class="card"><a class="clink" ')+atc(x)+'</div>';
  const words=q=>q.toLowerCase().split(/\s+/).filter(Boolean);
  const hit=(x,m,ws)=>{const s=(x.t+' '+(m.brands[x.b]||'')).toLowerCase();return ws.every(w=>s.includes(w))};
  // header search suggestions
  const hq=$('#hq'),sg=$('#sugg');
  if(hq&&sg){let t,items=[],sel=-1;
    const close=()=>{sg.hidden=true;hq.setAttribute('aria-expanded','false');sel=-1};
    const render=()=>{sg.innerHTML=items.map((it,i)=>`<li role="option" id="sg${i}" aria-selected="${i===sel}"><a href="${it.u}">${it.img?`<img src="${esc(it.img)}" alt="" width="40" height="40">`:''}<span>${esc(it.t)}</span>${it.p?`<b>${money(it.p)}</b>`:''}</a></li>`).join('');sg.hidden=!items.length;hq.setAttribute('aria-expanded',String(!!items.length));if(sel>=0)hq.setAttribute('aria-activedescendant','sg'+sel)};
    hq.addEventListener('focus',()=>catalog(),{once:true});
    hq.oninput=()=>{clearTimeout(t);t=setTimeout(async()=>{const q=hq.value.trim();if(q.length<2){items=[];render();return}
      const [d,m]=await catalog();const ws=words(q);
      const br=Object.entries(m.brands).filter(([k,n])=>ws.every(w=>n.toLowerCase().includes(w))).slice(0,2).map(([k,n])=>({t:'Author: '+n,u:'/authors/'+k+'/'}));
      const ps=d.filter(x=>hit(x,m,ws)).sort((a,b)=>a.r-b.r).slice(0,6).map(x=>({t:x.t,u:'/products/'+x.h+'/',img:x.i.replace(/width=\d+/,'width=80'),p:x.p}));
      items=[...br,...ps,{t:`See all results for “${q}”`,u:'/shop/?q='+encodeURIComponent(q)}];sel=-1;render()},150)};
    hq.onkeydown=e=>{if(sg.hidden)return;if(e.key==='ArrowDown'){sel=Math.min(items.length-1,sel+1);render();e.preventDefault()}else if(e.key==='ArrowUp'){sel=Math.max(-1,sel-1);render();e.preventDefault()}else if(e.key==='Enter'&&sel>=0){location.href=items[sel].u;e.preventDefault()}else if(e.key==='Escape')close()};
    document.addEventListener('click',e=>{if(!e.target.closest('.search'))close()});
  }
  // shop grid
  const shop=$('.shop');
  if(shop){
    const grid=$('#grid'),more=$('#more'),count=$('#count'),pre=JSON.parse(shop.dataset.preset||'{}'),P=new URLSearchParams(location.search),locked=Object.keys(pre).length>0;
    const st={cat:P.get('cat')||'',fam:P.get('fam')||'',brand:P.get('brand')||'',sty:P.get('sty')||'',q:P.get('q')||'',price:P.get('price')||'',sort:P.get('sort')||(shop.dataset.sort||($('#sort option[value=best]')?'best':'new'))};
    ['q','fam','brand','sty','price','sort'].forEach(k=>{const el=$('#'+k);if(el)el.value=st[k]});
    let data=[],meta={},shown=0,list=[];const PAGE=48;
    function apply(){
      const [lo,hi]=st.price?st.price.split('-').map(Number):[0,1e9],ws=words(st.q);
      list=data.filter(x=>match(x,pre)&&(!st.cat||x.c===st.cat)&&(!st.fam||x.f===st.fam)&&(!st.brand||x.b===st.brand)&&(!st.sty||x.s===st.sty)&&x.p>=lo&&x.p<hi&&(!ws.length||hit(x,meta,ws)));
      const by={best:(a,b)=>a.r-b.r||a.p-b.p,new:(a,b)=>b.d.localeCompare(a.d),lo:(a,b)=>a.p-b.p,hi:(a,b)=>b.p-a.p,az:(a,b)=>a.t.localeCompare(b.t)}[st.sort];list.sort((a,b)=>(a.x||0)-(b.x||0)||by(a,b));
      shown=0;grid.innerHTML='';page();count.textContent=list.length.toLocaleString()+' item'+(list.length===1?'':'s');
      $$('.f').forEach(b=>{const on=pre.aisle?pre.aisle.length===1&&b.dataset.cat===pre.aisle[0]:b.dataset.cat===st.cat;b.classList.toggle('on',on);b.setAttribute('aria-pressed',String(on))});
      if(!locked){const u=new URLSearchParams();Object.entries(st).forEach(([k,v])=>{if(v&&!(k==='sort'&&v===(shop.dataset.sort||(($('#sort option[value=best]'))?'best':'new'))))u.set(k,v)});history.replaceState(null,'',location.pathname+(u.toString()?'?'+u:''))}
      if(!list.length)grid.innerHTML='<p>Nothing matches those filters yet. Try fewer filters or another search.</p>';
    }
    function page(){grid.insertAdjacentHTML('beforeend',list.slice(shown,shown+PAGE).map(x=>card(x,meta)).join(''));shown+=PAGE;more.hidden=shown>=list.length}
    more.onclick=page;
    $$('.f').forEach(b=>b.onclick=()=>{if(locked){location.href=b.dataset.cat?'/shop/'+meta.aisles[b.dataset.cat].slug+'/':'/shop/';return}st.cat=b.dataset.cat;apply()});
    let t;$('#q').oninput=e=>{clearTimeout(t);t=setTimeout(()=>{st.q=e.target.value;apply()},180)};
    ['fam','brand','sty','price','sort'].forEach(k=>{const el=$('#'+k);if(el)el.onchange=e=>{st[k]=e.target.value;apply()}});
    catalog().then(([d,m])=>{data=d;meta=m;apply()});
  }
  // product page: live price + stock from the Shopify store
  const P=window.NI_PRODUCT;
  if(P){
    const buy=$('#buy'),price=$('#price'),stock=$('#stock'),sel=$('#variant'),cmp=$('#cmp');let variants=null;
    function setV(id){const v=variants&&variants.find(v=>String(v.id)===String(id));buy.dataset.v=id;if(sel){const o=sel.options[sel.selectedIndex];buy.dataset.vt=o?o.textContent.replace(/ \(sold out\)$/,''):''}if(!v)return;buy.dataset.p=(v.price/100).toFixed(2);buy.dataset.max=(v.quantity_rule&&v.quantity_rule.max)||'';
      price.textContent=money(v.price/100);if(v.compare_at_price&&v.compare_at_price>v.price){cmp.hidden=false;cmp.textContent=money(v.compare_at_price/100)}else cmp.hidden=true;
      stock.classList.toggle('out',!v.available);stock.querySelector('span').textContent=v.available?'In stock':'Sold out';buy.textContent=v.available?'Add to cart':'Sold out';buy.disabled=!v.available;buy.setAttribute('aria-disabled',String(!v.available))}
    if(sel)sel.onchange=e=>setV(e.target.value);
    fetch(`${P.shop}/products/${P.handle}.js`).then(r=>r.ok?r.json():Promise.reject(r.status)).then(p=>{variants=p.variants;
      if(sel)[...sel.options].forEach(o=>{const v=variants.find(v=>String(v.id)===o.value);if(v)o.disabled=!v.available});
      setV(sel?sel.value:(variants.find(v=>v.available)||variants[0]).id)}).catch(()=>{stock.querySelector('span').textContent='In stock (checked at checkout)'});
    $$('.th').forEach(b=>b.onclick=()=>{const m=$('#mainimg');m.removeAttribute('srcset');m.src=b.dataset.src;$$('.th').forEach(x=>x.classList.remove('on'));b.classList.add('on')});
  }
  // quiz: combine the chosen answers' filters and recommend real in-stock products
  const qz=$('#quiz');
  if(qz&&window.NI_QUIZ){qz.onsubmit=async e=>{e.preventDefault();const [d,m]=await catalog();
    const fs=window.NI_QUIZ.map((opts,i)=>{const c=qz.querySelector(`input[name=q${i}]:checked`);return c?opts[+c.value]:null}).filter(Boolean);
    let pool=d.filter(x=>fs.every(f=>match(x,f)));let relaxed=false;
    for(let drop=fs.length-1;pool.length<3&&drop>=0;drop--){relaxed=true;pool=d.filter(x=>fs.filter((_,i)=>i<drop).every(f=>match(x,f)))}
    pool.sort((a,b)=>a.r-b.r||a.p-b.p);const out=$('#quizout');
    out.innerHTML=`<h2>Your matches</h2>${relaxed?'<p class="small">We widened the search a little to find enough in stock.</p>':''}<div class="grid">${pool.slice(0,8).map(x=>card(x,m)).join('')}</div><p><a class="btn alt" href="/shop/">Browse everything</a></p>`;
    out.scrollIntoView({behavior:'smooth'})}}
})();
