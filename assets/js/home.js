/* Corbel — home page: stack map and testimonials. */
(function () {
  const { $, esc, reduced } = window.Corbel;
  const { services, cases } = window.CORBEL;

  /* ---------- Stack map ---------- */
  const svg = $('#map');
  if (svg) {
    const NS = 'http://www.w3.org/2000/svg';
    const el = (t, a) => { const n = document.createElementNS(NS, t); for (const k in a) n.setAttribute(k, a[k]); return n; };
    const NODES = {
      web: { l: 'Website', x: 260, y: 44 }, mobile: { l: 'Mobile app', x: 428, y: 104 },
      pay: { l: 'Payments', x: 458, y: 222 }, crm: { l: 'CRM', x: 420, y: 346 },
      erp: { l: 'Accounting / ERP', x: 260, y: 400 }, data: { l: 'Data warehouse', x: 100, y: 346 },
      cloud: { l: 'Cloud hosting', x: 74, y: 222 }, tools: { l: 'Internal tools', x: 100, y: 104 }
    };
    const C = { x: 260, y: 222 };
    const edges = {}, nodes = {};
    const drawNode = (x, y, label, cls, h = 40) => {
      const g = el('g', { class: 'map-node ' + (cls || '') });
      const rect = el('rect', { y: y - h / 2, height: h, rx: 7 });
      const t = el('text', { y: y + 5.5, 'text-anchor': 'middle' });
      t.textContent = label;
      g.append(rect, t);
      svg.appendChild(g);
      // Size each box to its rendered label, and keep it inside the canvas
      const w = (t.getComputedTextLength() || label.length * 8.5) + 30;
      const cx = Math.min(Math.max(x, w / 2 + 2), 520 - w / 2 - 2);
      rect.setAttribute('x', cx - w / 2);
      rect.setAttribute('width', w);
      t.setAttribute('x', cx);
      return g;
    };
    Object.entries(NODES).forEach(([k, n]) => { edges[k] = el('line', { x1: C.x, y1: C.y, x2: n.x, y2: n.y, class: 'map-edge' }); svg.appendChild(edges[k]); });
    Object.entries(NODES).forEach(([k, n]) => { nodes[k] = drawNode(n.x, n.y, n.l); });
    drawNode(C.x, C.y, 'Your business', 'map-core', 50);

    const chips = $('#mapChips');
    let idx = 0, timer = null;
    services.forEach((s, i) => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'chip'; b.textContent = s.short; b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', () => { stop(); show(i); });
      chips.appendChild(b);
    });
    function show(i) {
      idx = i;
      const s = services[i];
      Object.keys(NODES).forEach(k => {
        const on = s.nodes.includes(k);
        nodes[k].classList.toggle('on', on);
        edges[k].classList.toggle('on', on);
      });
      [...chips.children].forEach((b, j) => b.setAttribute('aria-pressed', j === i));
      $('#mapNote').textContent = s.note;
    }
    function stop() { clearInterval(timer); timer = null; }
    show(2);
    if (!reduced) {
      timer = setInterval(() => show((idx + 1) % services.length), 4000);
      const panel = svg.closest('.stack-map');
      panel.addEventListener('pointerenter', stop, { once: true });
      panel.addEventListener('focusin', stop, { once: true });
    }
  }

  /* ---------- Testimonials ---------- */
  const track = $('#quoteTrack');
  if (track) {
    const list = cases.filter(c => c.quote).slice(0, 5);
    const initials = n => n.replace(/^Dr\.\s*/, '').split(' ').map(p => p[0]).slice(0, 2).join('');
    track.innerHTML = list.map((c, i) => `<figure class="quote" role="group" aria-roledescription="slide" aria-label="${i + 1} of ${list.length}" style="margin:0">
        <div>
          <blockquote>${esc(c.quote.text)}</blockquote>
          <figcaption><span class="avatar" aria-hidden="true">${esc(initials(c.quote.who))}</span>
            <span><b>${esc(c.quote.who)}</b><small>${esc(c.quote.role)}</small></span></figcaption>
        </div>
        <p class="quote-result"><b>${esc(c.metric)}</b><span>${esc(c.mlabel)}</span><a href="work.html#${c.id}">Read the case study</a></p>
      </figure>`).join('');
    const count = $('#quoteCount');
    const current = () => Math.round(track.scrollLeft / track.clientWidth);
    const update = () => { count.textContent = `${current() + 1} / ${list.length}`; };
    const go = d => {
      const n = (current() + d + list.length) % list.length;
      track.scrollTo({ left: n * track.clientWidth, behavior: reduced ? 'auto' : 'smooth' });
    };
    $('#quotePrev').addEventListener('click', () => go(-1));
    $('#quoteNext').addEventListener('click', () => go(1));
    track.addEventListener('keydown', e => {
      if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
    });
    let raf;
    track.addEventListener('scroll', () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(update); }, { passive: true });
    update();
  }
})();
