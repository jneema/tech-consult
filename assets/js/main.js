/* Corbel — behaviour shared by every page: header, menus, theme, newsletter, reveal, helpers. */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = document.documentElement;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const store = {
    get(k, f) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : f; } catch (e) { return f; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
    session: {
      get(k, f) { try { const v = sessionStorage.getItem(k); return v ? JSON.parse(v) : f; } catch (e) { return f; } },
      set(k, v) { try { sessionStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
      del(k) { try { sessionStorage.removeItem(k); } catch (e) {} }
    }
  };

  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const toast = msg => {
    const t = $('#toast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(t._h);
    t._h = setTimeout(() => t.classList.remove('show'), 3000);
  };

  const ARROW = '<svg class="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"/></svg>';

  /* ---------- Case study covers: a quiet line drawing per service ---------- */
  const MOTIFS = {
    software: `<rect class="cv-fill cv-line" x="214" y="30" width="156" height="100" rx="6"/>
      <path class="cv-line" d="M252 30v100M266 52h84M266 68h70M266 84h78"/>
      <rect class="cv-accent-fill" x="266" y="102" width="46" height="12" rx="3"/>
      <path class="cv-line" d="M226 50h14M226 64h14M226 78h14"/>`,
    web: `<rect class="cv-fill cv-line" x="196" y="28" width="176" height="110" rx="6"/>
      <path class="cv-line" d="M196 46h176"/><circle class="cv-line" cx="208" cy="37" r="2.5"/><circle class="cv-line" cx="218" cy="37" r="2.5"/>
      <rect class="cv-accent-fill" x="212" y="62" width="86" height="10" rx="3"/>
      <path class="cv-line" d="M212 84h132M212 96h112M212 108h124"/>
      <rect class="cv-line" x="312" y="58" width="44" height="18" rx="3"/>`,
    integrations: `<path class="cv-line" d="M236 58C290 58 292 112 344 112M236 58C286 58 300 40 344 40M244 128C296 128 300 112 344 112"/>
      <path class="cv-accent" d="M236 58C270 58 286 74 300 86C314 98 326 112 344 112"/>
      <circle class="cv-fill cv-line" cx="236" cy="58" r="14"/><circle class="cv-fill cv-accent" cx="344" cy="112" r="14"/>
      <circle class="cv-fill cv-line" cx="344" cy="40" r="9"/><circle class="cv-fill cv-line" cx="244" cy="128" r="9"/>`,
    cloud: `<path class="cv-line" d="M220 150a80 80 0 0 1 160 0M240 150a60 60 0 0 1 120 0M280 150a20 20 0 0 1 40 0"/>
      <path class="cv-accent" d="M260 150a40 40 0 0 1 80 0"/>
      <path class="cv-line" d="M200 150a100 100 0 0 1 200 0"/>`,
    more: `<path class="cv-line" d="M214 140h160"/>
      <rect class="cv-fill cv-line" x="222" y="100" width="18" height="40" rx="2"/><rect class="cv-fill cv-line" x="250" y="78" width="18" height="62" rx="2"/>
      <rect class="cv-fill cv-line" x="278" y="88" width="18" height="52" rx="2"/><rect class="cv-accent-fill" x="306" y="46" width="18" height="94" rx="2"/>
      <rect class="cv-fill cv-line" x="334" y="64" width="18" height="76" rx="2"/>`
  };
  const cover = c => `<svg viewBox="0 0 400 250" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs><pattern id="g-${c.id}" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" class="cv-dot"/></pattern></defs>
      <rect width="400" height="250" fill="url(#g-${c.id})"/>${MOTIFS[c.svc] || MOTIFS.software}</svg>`;

  const serviceName = id => (window.CORBEL.services.find(s => s.id === id) || {}).name || '';
  const caseCard = c => `<a class="case-card" href="work.html#${c.id}" data-case="${c.id}">
      <div class="case-cover">${cover(c)}<div class="metric"><b>${esc(c.metric)}</b><span>${esc(c.mlabel)}</span></div></div>
      <div class="case-body">
        <div class="case-meta"><span>${esc(c.client)}</span><span>${esc(serviceName(c.svc))}</span></div>
        <h3>${esc(c.title)}</h3>
        <span class="link-arrow">Read the case study ${ARROW}</span>
      </div></a>`;

  /* ---------- Form submissions ----------
     Served by server.py, forms post to /api/submit/<kind>. Opened straight from disk
     (file://) there is no server, so submissions are only kept in this browser. */
  const online = location.protocol.startsWith('http');
  async function submit(kind, payload) {
    if (!online) {
      const key = 'corbel-' + kind + 's';
      const all = store.get(key, []);
      all.push(payload);
      store.set(key, all);
      return { ok: true, ref: payload.ref, offline: true };
    }
    try {
      const res = await fetch('/api/submit/' + kind, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      return { ok: res.ok, status: res.status, ref: data.ref || payload.ref, error: data.error };
    } catch (e) {
      return { ok: false, status: 0, error: 'We could not reach the server. Check your connection, or email hello@corbel.example.' };
    }
  }

  window.Corbel = { $, $$, store, esc, toast, reduced, ARROW, caseCard, serviceName, submit, online };

  /* ---------- Theme ---------- */
  $$('[data-theme-toggle]').forEach(btn => btn.addEventListener('click', () => {
    const dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('corbel-theme', root.dataset.theme); } catch (e) {}
  }));

  /* ---------- Header ---------- */
  const header = $('#siteHeader');
  const onScroll = () => header && header.classList.toggle('scrolled', scrollY > 8);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Services dropdown
  const menuBtn = $('[data-menu]');
  const menu = menuBtn && $('#' + menuBtn.getAttribute('aria-controls'));
  if (menuBtn && menu) {
    const li = menuBtn.parentElement;
    let hoverTimer, hoverOpenedAt = 0;
    const set = open => { menuBtn.setAttribute('aria-expanded', open); menu.classList.toggle('open', open); };
    // A click right after hover opened the menu should not immediately close it again
    menuBtn.addEventListener('click', () => {
      if (Date.now() - hoverOpenedAt < 600) return;
      set(menuBtn.getAttribute('aria-expanded') !== 'true');
    });
    document.addEventListener('click', e => { if (!li.contains(e.target)) set(false); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && menu.classList.contains('open')) { set(false); menuBtn.focus(); } });
    li.addEventListener('focusout', e => { if (!li.contains(e.relatedTarget)) set(false); });
    if (matchMedia('(hover: hover) and (pointer: fine)').matches) {
      li.addEventListener('mouseenter', () => {
        clearTimeout(hoverTimer);
        if (!menu.classList.contains('open')) { hoverOpenedAt = Date.now(); set(true); }
      });
      li.addEventListener('mouseleave', () => { hoverTimer = setTimeout(() => set(false), 160); });
    }
  }

  // Mobile navigation
  const navToggle = $('.nav-toggle');
  const mobileNav = $('#mobileNav');
  if (navToggle && mobileNav) {
    const setNav = open => {
      navToggle.setAttribute('aria-expanded', open);
      navToggle.setAttribute('aria-label', open ? 'Close menu' : 'Menu');
      mobileNav.hidden = !open;
      document.body.classList.toggle('nav-open', open);
    };
    navToggle.addEventListener('click', () => setNav(mobileNav.hidden));
    mobileNav.addEventListener('click', e => { if (e.target.closest('a')) setNav(false); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !mobileNav.hidden) { setNav(false); navToggle.focus(); } });
    matchMedia('(min-width: 1001px)').addEventListener('change', e => { if (e.matches) setNav(false); });
  }

  /* ---------- Newsletter ---------- */
  $$('[data-newsletter]').forEach(form => {
    const msg = form.parentElement.querySelector('.news-msg');
    form.addEventListener('submit', e => {
      e.preventDefault();
      const input = form.querySelector('input');
      const v = input.value.trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
        msg.textContent = 'Enter an email address like name@company.com.';
        input.focus();
        return;
      }
      const btn = form.querySelector('button');
      btn.disabled = true;
      submit('newsletter', { email: v }).then(r => {
        btn.disabled = false;
        if (!r.ok) { msg.textContent = r.error || 'Something went wrong. Please try again.'; return; }
        form.reset();
        msg.textContent = `Thanks. The next issue goes to ${v}.`;
      });
    });
  });

  /* ---------- Case study grids: data-cases="ids:a,b" or "svc:integrations" ---------- */
  $$('[data-cases]').forEach(grid => {
    const [kind, val] = grid.dataset.cases.split(':');
    const all = window.CORBEL.cases;
    const list = kind === 'ids'
      ? val.split(',').map(id => all.find(c => c.id === id)).filter(Boolean)
      : all.filter(c => c.svc === val).slice(0, 3);
    grid.innerHTML = list.map(caseCard).join('');
  });

  /* ---------- Footer year ---------- */
  $$('[data-year]').forEach(el => { el.textContent = new Date().getFullYear(); });

  /* ---------- Reveal on scroll ---------- */
  const reveals = $$('.reveal');
  if (!('IntersectionObserver' in window) || reduced) {
    reveals.forEach(el => el.classList.add('in'));
  } else {
    const io = new IntersectionObserver(entries => entries.forEach(en => {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    }), { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveals.forEach(el => io.observe(el));
  }
})();
