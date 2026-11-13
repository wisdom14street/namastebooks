/* Namaste physical book finder. No Shopify credentials or staff access tokens on this static site. */
(function () {
  'use strict';
  const root = document.querySelector('[data-locator-mode]');
  if (!root) return;
  const mode = root.getAttribute('data-locator-mode');
  const $ = id => document.getElementById(id);
  const elt = (tag, cls, txt) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt != null) n.textContent = String(txt);
    return n;
  };
  const normalized = value => String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const codeKey = value => String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const money = amount => '$' + Number(amount).toFixed(2);
  const itemUrl = book => '/products/' + encodeURIComponent(book.handle) + '/';
  let catalog = [], locations = {}, builtAt = '', shown = 0, results = [];
  const PAGE = 24;

  function salesFloor(book) {
    const entries = locations[String(book.id)] || [];
    return entries.filter(row => row.kind === 'sales-floor' && row.code && row.verified_at);
  }
  function locationLabel(book) {
    const rows = salesFloor(book);
    return rows.length ? rows.map(row => row.code).join(', ') : '';
  }
  function searchable(book) {
    return normalized([book.title, book.author, book.subject, book.isbn, ...(book.sku || []), book.id].join(' '));
  }
  function searchScore(book, q) {
    if (!q) return 1;
    const title = normalized(book.title), author = normalized(book.author);
    const cq = codeKey(q);
    const skus = (book.sku || []).map(codeKey);
    if (String(book.id) === q || (cq.length >= 8 && (skus.includes(cq) || codeKey(book.isbn) === cq))) return 1000;
    if (title === q) return 950;
    if (title.startsWith(q)) return 800;
    if (author === q) return 750;
    if (author.startsWith(q)) return 650;
    const terms = q.split(' ').filter(Boolean);
    const hay = searchable(book);
    if (terms.every(term => hay.includes(term))) return 200 + terms.filter(term => title.includes(term)).length * 30;
    // A forgiving fallback for simple spelling errors without returning unrelated products.
    if (q.length > 5) {
      const set = new Set();
      for (let i = 0; i < q.length - 2; i++) set.add(q.slice(i, i + 3));
      let overlap = 0;
      set.forEach(t => { if (title.includes(t) || author.includes(t)) overlap++; });
      if (overlap >= Math.max(3, Math.floor(set.size * 0.72))) return 20 + overlap;
    }
    return 0;
  }
  function sectionField(book) {
    const formats = {video: 'Video', audio: 'Audio course', journal: 'Journal or workbook', set: 'Book and deck set'};
    const p = elt('p', 'loc-subject', (book.subject || 'Book') + (formats[book.format] ? ' · ' + formats[book.format] : ''));
    return p;
  }
  function photo(book, cls) {
    const img = elt('img', cls || 'loc-cover');
    img.loading = 'lazy';
    img.alt = 'Cover of ' + book.title;
    img.width = 90;
    img.height = 128;
    img.src = book.cover || '/assets/no-photo.svg';
    img.onerror = () => { img.onerror = null; img.src = '/assets/no-photo.svg'; };
    return img;
  }
  function card(book) {
    const article = elt('article', 'loc-book');
    article.appendChild(photo(book));
    const info = elt('div', 'loc-book-info');
    info.appendChild(elt('h2', '', book.title));
    if (book.author) info.appendChild(elt('p', 'loc-author', book.author));
    info.appendChild(sectionField(book));
    const place = locationLabel(book);
    info.appendChild(elt('p', place ? 'loc-placed' : 'loc-unmapped',
      place ? 'Shelf verified: ' + place : 'Exact shelf not yet verified — ask staff'));
    const actions = elt('div', 'loc-actions');
    const details = elt('button', 'loc-primary', place ? 'Show shelf location' : 'Show to an employee');
    details.type = 'button';
    details.addEventListener('click', () => openDetails(book));
    actions.appendChild(details);
    if (mode !== 'kiosk') {
      const link = elt('a', 'loc-secondary', 'Book details');
      link.href = itemUrl(book);
      actions.appendChild(link);
    }
    info.appendChild(actions);
    article.appendChild(info);
    return article;
  }
  function openDetails(book) {
    const dialog = $('loc-dialog'), content = $('loc-details');
    content.replaceChildren();
    const view = elt('div', 'loc-detail');
    view.appendChild(photo(book, 'loc-large-cover'));
    const panel = elt('div');
    panel.appendChild(elt('p', 'loc-eyebrow', 'Show this to a Namaste bookseller'));
    panel.appendChild(elt('h2', '', book.title));
    if (book.author) panel.appendChild(elt('p', 'loc-author', book.author));
    panel.appendChild(sectionField(book));
    const place = salesFloor(book);
    if (place.length) {
      panel.appendChild(elt('strong', 'loc-placed', 'Verified location: ' + place.map(x => x.code).join(', ')));
      panel.appendChild(elt('p', 'loc-small', 'Last physically verified: ' + place.map(x => x.verified_at).sort().reverse()[0]));
      panel.appendChild(elt('p', 'loc-small', 'Ask staff if the shelf is empty; stock may have changed.'));
    } else {
      panel.appendChild(elt('strong', 'loc-unmapped', 'Shelf location not yet mapped'));
      panel.appendChild(elt('p', 'loc-small', 'This title appears in the online book catalog. Ask staff to help locate a copy.'));
    }
    if (book.isbn) panel.appendChild(elt('p', 'loc-code', 'Verified ISBN: ' + book.isbn));
    if (book.sku && book.sku.length) panel.appendChild(elt('p', 'loc-code', 'SKU: ' + book.sku.join(', ')));
    panel.appendChild(elt('p', 'loc-code', 'Product reference: ' + book.id));
    if (mode !== 'kiosk') {
      const a = elt('a', 'loc-secondary', 'View online book listing');
      a.href = itemUrl(book);
      panel.appendChild(a);
    }
    view.appendChild(panel);
    content.appendChild(view);
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
  }
  function renderPage(reset) {
    const target = $('loc-results');
    if (reset) {
      target.replaceChildren();
      shown = 0;
    }
    const frag = document.createDocumentFragment();
    results.slice(shown, shown + PAGE).forEach(x => frag.appendChild(card(x.book)));
    target.appendChild(frag);
    shown += PAGE;
    $('loc-more').hidden = shown >= results.length;
  }
  function customerInit() {
    const input = $('loc-query'), status = $('loc-status');
    const subjects = [...new Set(catalog.map(x => x.subject).filter(Boolean))].sort();
    const filter = elt('select', 'loc-filter');
    filter.id = 'loc-subject-filter';
    filter.setAttribute('aria-label', 'Filter by subject');
    const all = elt('option', '', 'All subjects');
    all.value = '';
    filter.appendChild(all);
    subjects.forEach(s => {
      const opt = elt('option', '', s);
      opt.value = s;
      filter.appendChild(opt);
    });
    input.insertAdjacentElement('afterend', filter);
    let debounce;
    const update = () => {
      const q = normalized(input.value);
      const subj = filter.value;
      results = catalog
        .filter(x => !subj || x.subject === subj)
        .map(book => ({book, score: searchScore(book, q)}))
        .filter(x => x.score)
        .sort((a,b) => b.score - a.score || Number(!!locationLabel(b.book)) - Number(!!locationLabel(a.book)) || a.book.title.localeCompare(b.book.title));
      status.textContent = results.length.toLocaleString() + ' matching books · Catalog refreshed ' + (builtAt ? new Date(builtAt).toLocaleDateString() : 'recently');
      renderPage(true);
    };
    input.addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(update, 150); });
    filter.addEventListener('change', update);
    $('loc-clear').addEventListener('click', () => { input.value = ''; filter.value = ''; update(); input.focus(); });
    $('loc-more').addEventListener('click', () => renderPage(false));
    $('loc-dialog').querySelector('.loc-close').addEventListener('click', () => $('loc-dialog').close());
    $('loc-dialog').addEventListener('click', e => { if (e.target === $('loc-dialog')) $('loc-dialog').close(); });
    const params = new URLSearchParams(location.search);
    input.value = params.get('q') || '';
    update();
    if (mode === 'kiosk') {
      let idle;
      const resetIdle = () => {
        clearTimeout(idle);
        idle = setTimeout(() => {
          input.value = ''; filter.value = '';
          if ($('loc-dialog').open) $('loc-dialog').close();
          update();
          window.scrollTo(0, 0);
        }, 120000);
      };
      ['pointerdown', 'keydown', 'touchstart'].forEach(ev => document.addEventListener(ev, resetIdle, {passive: true}));
      resetIdle();
    }
  }

  function csvEscape(s) {
    const value = String(s == null ? '' : s);
    return /[\r\n,"]/.test(value) ? '"' + value.replace(/"/g, '""') + '"' : value;
  }
  function staffInit() {
    const storageKey = 'namaste-shelf-mapping-pilot-v1';
    let drafts = {};
    try { drafts = JSON.parse(localStorage.getItem(storageKey) || '{}'); } catch (_) { drafts = {}; }
    const shelf = $('loc-shelf'), sku = $('loc-sku'), status = $('loc-staff-status');
    const persist = () => {
      try { localStorage.setItem(storageKey, JSON.stringify(drafts)); }
      catch (_) { status.textContent = 'Local storage failed. Export your CSV before leaving.'; }
    };
    const renderDrafts = () => {
      const box = $('loc-staff-assignments');
      const entries = Object.values(drafts).sort((a,b) => b.verified_at.localeCompare(a.verified_at)).slice(0, 60);
      box.replaceChildren();
      box.appendChild(elt('p', 'loc-small', Object.keys(drafts).length + ' unique book assignments saved locally'));
      entries.forEach(row => {
        const line = elt('div', 'loc-draft-row');
        line.appendChild(elt('p', 'loc-draft', row.code + ' · ' + row.title + ' · ' + row.product_id));
        const remove = elt('button', 'loc-remove', 'Remove');
        remove.type = 'button';
        remove.setAttribute('aria-label', 'Remove local draft placement for ' + row.title + ' at ' + row.code);
        remove.addEventListener('click', () => {
          if (!confirm('Remove this local draft placement?')) return;
          delete drafts[row.product_id + '|' + row.code + '|' + row.kind];
          persist();
          renderDrafts();
        });
        line.appendChild(remove);
        box.appendChild(line);
      });
    };
    const set = (book, code) => {
      const key = book.id + '|' + code + '|sales-floor';
      drafts[key] = {
        product_id: String(book.id), isbn_sku: [book.isbn, ...(book.sku || [])].filter(Boolean).join('|'),
        title: book.title, code, kind: 'sales-floor',
        verified_at: new Date().toISOString().slice(0,10)
      };
      persist();
      renderDrafts();
      status.textContent = 'Saved on this device: ' + book.title + ' → ' + code + '. Export your CSV after this shift.';
      sku.value = ''; sku.focus();
      $('loc-staff-matches').replaceChildren();
    };
    const process = () => {
      const code = shelf.value.trim().toUpperCase();
      if (!/^[A-Z][A-Z0-9]{0,11}(?:-[A-Z0-9]{1,12}){1,3}$/.test(code)) {
        status.textContent = 'Enter a section-bay-level code such as A-04-02 (do not invent a location).';
        shelf.focus(); return;
      }
      const search = sku.value.trim().toLowerCase();
      if (!search) { status.textContent = 'Scan a book barcode or enter its Shopify ID.'; return; }
      const qcode = codeKey(search);
      const exact = catalog.filter(book =>
        String(book.id) === search ||
        (qcode.length >= 8 && (codeKey(book.isbn) === qcode || (book.sku || []).some(s => codeKey(s) === qcode)))
      );
      const box = $('loc-staff-matches'); box.replaceChildren();
      const titleQuery = normalized(search);
      const titleMatches = !exact.length && titleQuery.length >= 3 && /[a-z]/.test(titleQuery)
        ? catalog.filter(book => normalized(book.title + ' ' + book.author).includes(titleQuery)).slice(0, 15)
        : [];
      const hits = exact.length ? exact : titleMatches;
      if (!hits.length) {
        status.textContent = 'No exact ISBN/SKU or title match among currently listed books. Check Shopify or hold the item for manual catalog review; no assignment saved.';
        return;
      }
      if (exact.length === 1) { set(exact[0], code); return; }
      status.textContent = exact.length
        ? 'Multiple editions share this barcode. Select the exact edition before assigning a shelf.'
        : 'Title search only: verify the physical book edition before selecting. No automatic barcode match was found.';
      hits.forEach(book => {
        const b = elt('button', 'loc-match', book.title + ' (' + book.id + ') → ' + code);
        b.type = 'button'; b.addEventListener('click', () => set(book, code)); box.appendChild(b);
      });
    };
    sku.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); process(); } });
    $('loc-export').addEventListener('click', () => {
      const records = Object.values(drafts);
      if (!records.length) { status.textContent = 'Nothing to export yet.'; return; }
      const fields = ['product_id','isbn_sku','title','code','kind','verified_at'];
      const csv = [fields.join(','), ...records.map(row => fields.map(key => csvEscape(row[key])).join(','))].join('\r\n') + '\r\n';
      const url = URL.createObjectURL(new Blob([csv], {type:'text/csv;charset=utf-8'}));
      const a = elt('a'); a.href = url; a.download = 'namaste-shelf-assignments-' + new Date().toISOString().slice(0,10) + '.csv';
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      status.textContent = 'CSV exported. The public finder will NOT update until these assignments are reviewed and imported.';
    });
    $('loc-reset-drafts').addEventListener('click', () => {
      if (!confirm('Permanently clear shelf-mapping drafts saved on this device? Export first.')) return;
      drafts = {}; persist(); renderDrafts(); status.textContent = 'Local drafts cleared.';
    });
    renderDrafts(); sku.focus();
  }

  Promise.all([
    fetch('/data/locator-catalog.json', {cache: 'no-store'}).then(r => { if (!r.ok) throw Error('catalog HTTP ' + r.status); return r.json(); }),
    fetch('/data/physical-locations.json', {cache: 'no-store'}).then(r => { if (!r.ok) throw Error('locations HTTP ' + r.status); return r.json(); })
  ]).then(([feed, mapped]) => {
    catalog = feed.books || [];
    locations = mapped.items || {};
    builtAt = feed.built_at || '';
    if (mode === 'staff') staffInit();
    else customerInit();
  }).catch(() => {
    const target = mode === 'staff' ? $('loc-staff-status') : $('loc-status');
    if (target) target.textContent = 'Book data could not load. Please use the main book search or ask a bookseller.';
  });
})();
