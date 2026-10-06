/* Corbel — about page: team list and live office clocks. */
(function () {
  const { $, $$, esc } = window.Corbel;

  const TEAM = [
    ['Achieng Odhiambo', 'Managing Director'],
    ['Brian Mutua', 'Head of Engineering'],
    ['Faith Chebet', 'Design Director'],
    ['Kevin Omondi', 'Principal, Integrations'],
    ['Nadia Yusuf', 'Principal, Cloud'],
    ['Eric Habimana', 'Lead, Kigali hub'],
    ['Mercy Wanjiku', 'Head of Data'],
    ['Tom Hargreaves', 'Client Partner, Europe']
  ];
  // A few quiet line patterns so the placeholders don't all look identical
  const PATTERNS = [
    '<path d="M0 160h200M0 120h200M0 80h200" class="cv-line"/>',
    '<circle cx="100" cy="125" r="70" class="cv-line"/><circle cx="100" cy="125" r="40" class="cv-line"/>',
    '<path d="M40 0v250M100 0v250M160 0v250" class="cv-line"/>',
    '<path d="M0 250L200 0M-60 250L140 0M60 250L260 0" class="cv-line"/>'
  ];
  const initials = n => n.split(' ').map(p => p[0]).join('');
  const list = $('#teamList');
  if (list) {
    list.innerHTML = TEAM.map(([n, r], i) => `<li class="person">
        <div class="portrait"><svg viewBox="0 0 200 250" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${PATTERNS[i % PATTERNS.length]}</svg><span aria-hidden="true">${esc(initials(n))}</span></div>
        <b>${esc(n)}</b><span class="role">${esc(r)}</span></li>`).join('');
  }

  const clocks = $$('[data-tz]');
  const tick = () => clocks.forEach(el => {
    const tz = el.dataset.tz;
    const time = new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: '2-digit', minute: '2-digit' }).format(new Date());
    const hour = +new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: 'numeric', hourCycle: 'h23' }).format(new Date());
    const day = new Intl.DateTimeFormat('en-GB', { timeZone: tz, weekday: 'short' }).format(new Date());
    const open = hour >= 8 && hour < 18 && !['Sat', 'Sun'].includes(day);
    el.textContent = `${time} local time · ${open ? 'Open now' : 'Closed'}`;
  });
  tick();
  setInterval(tick, 30000);
})();
