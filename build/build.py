"""Builds the Corbel site's HTML pages.

Run from anywhere:  python3 build/build.py

- build/pages/<name>.html holds the main content of each page. Edit those, not the
  generated .html files in the project root, which are overwritten on every build.
- The header, footer, "Up next" links and <head> are defined once below.
- The four service pages (software-development.html and so on) have no file in
  build/pages; their content lives in SERVICE_PAGES and shares one template.
- {{icon:name}} in a page is replaced with the matching icon from ICONS.
"""
import html, json, re, pathlib, urllib.parse

SRC = pathlib.Path(__file__).parent / "pages"
OUT = pathlib.Path(__file__).parent.parent

def svg(paths, cls=""):
    c = f' class="{cls}"' if cls else ""
    return (f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths}</svg>')

ICONS = {
    "software": svg('<path d="M8 7l-5 5 5 5M16 7l5 5-5 5M13.5 4l-3 16"/>'),
    "web": svg('<rect x="3" y="4.5" width="18" height="15" rx="2"/><path d="M3 9h18M6.5 6.8h.01M9 6.8h.01"/>'),
    "integrations": svg('<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.5 6H14a4 4 0 0 1 4 4v5.5M15.5 18H10a4 4 0 0 1-4-4V8.5"/>'),
    "cloud": svg('<path d="M7 18.5h10.5a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.6 9.1 4.75 4.75 0 0 0 7 18.5z"/>'),
    "more": svg('<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><path d="M16.75 13.5v6.5M13.5 16.75H20"/>'),
    "design": svg('<path d="M4 20l4-1L19 8a2.1 2.1 0 0 0-3-3L5 16z"/><path d="M14 7l3 3"/>'),
    "data": svg('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'),
    "consult": svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>'),
    "support": svg('<path d="M12 3l7.5 3v5.5c0 4.5-3.2 8.2-7.5 9.5-4.3-1.3-7.5-5-7.5-9.5V6z"/><path d="M8.8 12l2.2 2.2 4.2-4.4"/>'),
    "arrow": svg('<path d="M4 12h15M13 6l6 6-6 6"/>', "arrow"),
    "arrow-left": svg('<path d="M20 12H5M11 6l-6 6 6 6"/>'),
    "chev": svg('<path d="M6 9l6 6 6-6"/>', "chev"),
    "theme": svg('<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 0 0 16z" fill="currentColor"/>'),
    "menu": svg('<path d="M4 8h16M4 16h16"/>', "open-ic"),
    "close": svg('<path d="M6 6l12 12M18 6L6 18"/>', "close-ic"),
    "x": svg('<path d="M6 6l12 12M18 6L6 18"/>'),
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.75h4V21H3zM9.5 9.75h3.8v1.6h.06c.53-.95 1.83-1.95 3.77-1.95 4.03 0 4.77 2.5 4.77 5.75V21h-4v-5.1c0-1.22-.02-2.8-1.8-2.8-1.8 0-2.07 1.33-2.07 2.7V21h-4z"/></svg>',
    "github": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.5a9.5 9.5 0 0 0-3 18.52c.47.09.65-.2.65-.46v-1.6c-2.64.57-3.2-1.27-3.2-1.27-.43-1.1-1.06-1.4-1.06-1.4-.86-.59.07-.58.07-.58.95.07 1.45.98 1.45.98.85 1.45 2.22 1.03 2.76.79.09-.62.33-1.03.6-1.27-2.1-.24-4.32-1.05-4.32-4.68 0-1.03.37-1.88.98-2.54-.1-.24-.43-1.2.09-2.5 0 0 .8-.26 2.6.97a9 9 0 0 1 4.74 0c1.8-1.23 2.6-.97 2.6-.97.52 1.3.19 2.26.1 2.5.6.66.97 1.5.97 2.54 0 3.64-2.22 4.44-4.33 4.67.34.3.64.88.64 1.77v2.63c0 .26.17.56.66.46A9.5 9.5 0 0 0 12 2.5z"/></svg>',
    "x-social": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.75 3h3.07l-6.7 7.66L22 21h-6.17l-4.83-6.32L5.47 21H2.4l7.17-8.2L2 3h6.33l4.37 5.77zm-1.08 16.17h1.7L7.4 4.73H5.58z"/></svg>',
}

BRAND_MARK = ('<svg class="brand-mark" viewBox="0 0 28 28" aria-hidden="true">'
              '<path d="M3 4h22v6H14v14H8V10H3z" fill="currentColor"/>'
              '<rect x="16" y="13" width="9" height="11" fill="var(--accent)"/></svg>')

SERVICES_MENU = [
    ("software", "Software development", "Custom platforms, internal tools and mobile apps"),
    ("web", "Web development", "Websites, portals and web applications"),
    ("integrations", "Integrations", "Connect payments, CRM, ERP and logistics"),
    ("cloud", "Cloud solutions", "Migration, DevOps and managed infrastructure"),
    ("more", "More services", "Design, data, IT consulting and support"),
]

# ---------------------------------------------------------------------------
# Site map
# ---------------------------------------------------------------------------
SERVICES_MENU = [
    ("software", "software-development.html", "Software development", "Custom platforms, internal tools and mobile apps"),
    ("web", "web-development.html", "Web development", "Websites, portals and web applications"),
    ("integrations", "integrations.html", "Integrations", "Connect payments, CRM, ERP and logistics"),
    ("cloud", "cloud-solutions.html", "Cloud solutions", "Migration, DevOps and managed infrastructure"),
    ("more", "services.html#more", "More services", "Design, data, IT consulting and support"),
]
SERVICE_FILES = {"services.html"} | {f for _, f, _, _ in SERVICES_MENU if f.endswith(".html")}

NAV = [("work.html", "Work"), ("process.html", "How we work"), ("pricing.html", "Pricing"),
       ("about.html", "About"), ("contact.html", "Contact")]

# "Up next" link shown at the foot of each page, so visitors move through the site
NEXT = {
    "index.html": ("services.html", "Services", "What we build and how we can help"),
    "services.html": ("software-development.html", "Software development", "Custom platforms, internal tools and mobile apps"),
    "software-development.html": ("web-development.html", "Web development", "Websites, portals and e-commerce"),
    "web-development.html": ("integrations.html", "Integrations", "Payments, CRM, ERP and logistics, connected"),
    "integrations.html": ("cloud-solutions.html", "Cloud solutions", "Migration, DevOps and cost control"),
    "cloud-solutions.html": ("work.html", "Case studies", "Projects we can talk about"),
    "work.html": ("process.html", "How we work", "Five stages from discovery to support"),
    "process.html": ("pricing.html", "Pricing", "Three ways to work with us"),
    "pricing.html": ("estimate.html", "Estimate your project", "A budget and timeline in a minute"),
    "estimate.html": ("contact.html", "Start a project", "Send a brief or book a call"),
    "faq.html": ("contact.html", "Still have a question?", "Ask a technical lead directly"),
    "about.html": ("careers.html", "Careers", "Open roles and how we hire"),
    "careers.html": ("contact.html", "Get in touch", "Send a brief or book a call"),
}

def header(page):
    here = ' aria-current="page"'
    menu = "".join(
        f'<a href="{f}"{here if f == page else ""}><span class="ic">{ICONS[i]}</span><b>{n}</b><span>{d}</span></a>'
        for i, f, n, d in SERVICES_MENU)
    def cur(href):
        return ' aria-current="page"' if href == page else ""
    links = "".join(f'<li><a class="nav-link" href="{h}"{cur(h)}>{t}</a></li>' for h, t in NAV)
    svc_cur = ' aria-current="page"' if page in SERVICE_FILES else ""
    mob_svc = "".join(f'<li><a href="{f}">{n}</a></li>' for _, f, n, _ in SERVICES_MENU)
    mob_links = "".join(f'<li><a href="{h}">{t}{ICONS["arrow"]}</a></li>' for h, t in NAV + [("careers.html", "Careers")])
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header" id="siteHeader">
  <div class="container header-inner">
    <a class="brand" href="index.html" aria-label="Corbel home">{BRAND_MARK}<span>Corbel</span></a>
    <nav class="primary-nav" aria-label="Main">
      <ul class="nav-list">
        <li class="has-menu">
          <button class="nav-link" type="button" aria-expanded="false" aria-controls="servicesMenu" data-menu{svc_cur}>Services {ICONS["chev"]}</button>
          <div class="nav-menu" id="servicesMenu">
            {menu}
            <div class="menu-foot"><a class="link-arrow" href="services.html">All services</a><a class="link-arrow" href="estimate.html">Estimate a project {ICONS["arrow"]}</a></div>
          </div>
        </li>
        {links}
      </ul>
    </nav>
    <div class="header-actions">
      <button class="icon-btn" type="button" data-theme-toggle aria-label="Switch between light and dark theme">{ICONS["theme"]}</button>
      <a class="btn btn-primary btn-sm header-cta" href="contact.html">Start a project</a>
      <button class="icon-btn nav-toggle" type="button" aria-expanded="false" aria-controls="mobileNav" aria-label="Menu">{ICONS["menu"]}{ICONS["close"]}</button>
    </div>
  </div>
  <nav class="mobile-nav" id="mobileNav" aria-label="Mobile" hidden>
    <ul>
      <li><a href="services.html">Services{ICONS["arrow"]}</a><ul class="sub">{mob_svc}</ul></li>
      {mob_links}
    </ul>
    <div class="mobile-cta">
      <a class="btn btn-accent btn-block" href="contact.html">Start a project</a>
      <a class="btn btn-outline btn-block" href="estimate.html">Estimate your project</a>
    </div>
    <p class="mobile-contact">hello@corbel.example<br>+254 20 765 4321</p>
  </nav>
</header>'''

def pager(page):
    if page not in NEXT:
        return ""
    href, title, sub = NEXT[page]
    return f'''<nav class="pager" aria-label="Next page">
  <div class="container">
    <a class="pager-link" href="{href}"><span class="pager-k">Up next</span><span class="pager-t">{title}</span><span class="pager-s">{sub}</span><span class="go">{ICONS["arrow"]}</span></a>
  </div>
</nav>'''

def footer():
    svc = "".join(f'<li><a href="{f}">{n}</a></li>' for _, f, n, _ in SERVICES_MENU)
    return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer-top">
      <div class="footer-news">
        <h2>Notes from the build</h2>
        <p>One email a month on integrations, cloud costs and shipping software that lasts. No sales pitches.</p>
        <form class="news-form" data-newsletter novalidate>
          <label class="sr-only" for="newsEmail">Email address</label>
          <input id="newsEmail" type="email" placeholder="you@company.com" autocomplete="email" required>
          <button class="btn" type="submit">Subscribe</button>
        </form>
        <p class="news-msg" role="status"></p>
      </div>
      <div class="footer-cols">
        <div><h3>Services</h3><ul>{svc}</ul></div>
        <div><h3>Company</h3><ul>
          <li><a href="work.html">Case studies</a></li>
          <li><a href="process.html">How we work</a></li>
          <li><a href="pricing.html">Pricing</a></li>
          <li><a href="estimate.html">Project estimator</a></li>
          <li><a href="faq.html">FAQ</a></li>
          <li><a href="about.html">About us</a></li>
          <li><a href="careers.html">Careers</a></li>
        </ul></div>
        <div><h3>Get in touch</h3><ul>
          <li><a href="mailto:hello@corbel.example">hello@corbel.example</a></li>
          <li><a href="tel:+254207654321">+254 20 765 4321</a></li>
          <li>Westlands, Nairobi</li>
          <li>Mon to Fri, 8am to 6pm EAT</li>
        </ul>
        <div class="social">
          <a href="#" aria-label="Corbel on LinkedIn">{ICONS["linkedin"]}</a>
          <a href="#" aria-label="Corbel on GitHub">{ICONS["github"]}</a>
          <a href="#" aria-label="Corbel on X">{ICONS["x-social"]}</a>
        </div></div>
      </div>
    </div>
    <div class="footer-base">
      <a class="brand" href="index.html" aria-label="Corbel home">{BRAND_MARK}<span>Corbel</span></a>
      <ul><li>&copy; <span data-year>2026</span> Corbel Consulting Ltd.</li><li><a href="#">Privacy</a></li><li><a href="#">Terms</a></li></ul>
    </div>
  </div>
</footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>'''

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:ital,wght@0,400..800;1,400..800&display=swap" rel="stylesheet">')

def page(name, title, desc, body, scripts):
    body = re.sub(r"\{\{icon:([\w-]+)\}\}", lambda m: ICONS[m.group(1)], body)
    js = "\n".join(f'<script src="assets/js/{s}" defer></script>' for s in scripts)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0A0D12" media="(prefers-color-scheme: dark)">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 28 28'%3E%3Cpath d='M3 4h22v6H14v14H8V10H3z' fill='%230B1220'/%3E%3Crect x='16' y='13' width='9' height='11' fill='%230E6B4E'/%3E%3C/svg%3E">
<script>try{{var t=(localStorage.getItem("corbel-theme")||"").replace(/"/g,"");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}}catch(e){{}}document.documentElement.classList.add("js")</script>
{FONTS}
<link rel="stylesheet" href="assets/css/styles.css">
</head>
<body>
{header(name)}
<main id="main">
{body}
</main>
{pager(name)}
{footer()}
{js}
</body>
</html>
'''

# ---------------------------------------------------------------------------
# Service pages share one template
# ---------------------------------------------------------------------------
CONTENT = pathlib.Path(__file__).parent / "content"

def load(name):
    return json.loads((CONTENT / name).read_text())

def esc(text):
    """Escape admin-entered text for HTML. Apostrophes are left readable."""
    return html.escape(str(text), quote=False)

def attr(text):
    return html.escape(str(text), quote=True)

SERVICE_PAGES = load("service-pages.json")

def service_page(s):
    facts = "".join(f"<div><dt>{esc(f['label'])}</dt><dd>{esc(f['value'])}</dd></div>" for f in s["facts"])
    deliver = "".join(f'<div class="reveal"><h3>{esc(d["title"])}</h3><p>{esc(d["text"])}</p></div>' for d in s["deliver"])
    fit = "".join(f"<li>{esc(x)}</li>" for x in s["fit"])
    stack = "".join(f'<li class="tag">{esc(x)}</li>' for x in s["stack"])
    steps = "".join(f'<li class="reveal"><h3>{esc(st["title"])}</h3><p>{esc(st["text"])}</p><span class="dur">{esc(st["duration"])}</span></li>' for st in s["steps"])
    faqs = "".join(f'<details><summary>{esc(f["q"])}<span class="pm" aria-hidden="true"></span></summary><div><p>{esc(f["a"])}</p></div></details>' for f in s["faqs"])
    others = "".join(f'<li><a class="link-arrow" href="{f}">{n} {ICONS["arrow"]}</a></li>'
                     for i, f, n, _ in SERVICES_MENU if i != s["id"])
    s = {**s, **{k: esc(s[k]) for k in ("name", "h1", "lede", "stack_label", "noun")}}
    return f'''<header class="page-head">
  <div class="container">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="services.html">Services</a><span aria-hidden="true">/</span><span aria-current="page">{s["name"]}</span></nav>
    <div class="page-head-grid">
      <div>
        <div class="ic-lg">{ICONS[s["id"]]}</div>
        <h1 class="h1">{s["h1"]}</h1>
      </div>
      <div>
        <p class="lede">{s["lede"]}</p>
        <dl class="facts">{facts}</dl>
        <div class="head-actions">
          <a class="btn btn-accent" href="contact.html?service={s["id"]}">Discuss your project {ICONS["arrow"]}</a>
          <a class="btn btn-outline" href="estimate.html?type={s["id"]}">Estimate the cost</a>
        </div>
      </div>
    </div>
  </div>
</header>

<section class="section">
  <div class="container">
    <div class="section-head">
      <h2 class="h2">What we deliver</h2>
      <p class="lede">Most {s["noun"]} projects include one or more of these. Each is scoped and priced separately so you only pay for what you need.</p>
    </div>
    <div class="deliver-grid wide">{deliver}</div>
  </div>
</section>

<section class="section">
  <div class="container split">
    <div class="reveal">
      <h2 class="h3">A good fit if</h2>
      <ul class="check-list" style="margin-top:24px">{fit}</ul>
    </div>
    <div class="reveal">
      <h2 class="h3">{s["stack_label"]}</h2>
      <p class="muted" style="margin:10px 0 20px">Chosen for what your team can maintain after launch.</p>
      <ul class="tags">{stack}</ul>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head">
      <h2 class="h2">How a typical project runs</h2>
      <p class="lede">Timings are typical for this kind of work. Your proposal will set out exact dates. <a href="process.html">See our full process</a>.</p>
    </div>
    <ol class="process four">{steps}</ol>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head">
      <h2 class="h2">Related work</h2>
      <a class="link-arrow" href="work.html?service={s["id"]}" style="justify-self:end">All {s["name"].lower()} projects {ICONS["arrow"]}</a>
    </div>
    <div class="case-grid" data-cases="svc:{s["id"]}"></div>
  </div>
</section>

<section class="section">
  <div class="container faq-layout">
    <div>
      <h2 class="h2">Questions about {s["name"].lower()}</h2>
      <a class="link-arrow" href="faq.html">All questions {ICONS["arrow"]}</a>
      <h3 class="small muted" style="margin:40px 0 14px;font-weight:500;letter-spacing:0">Other services</h3>
      <ul class="other-svc">{others}</ul>
    </div>
    <div class="faq">{faqs}</div>
  </div>
</section>
'''

PAGES = [
    ("index.html", "Corbel | Software, web, integrations and cloud consultancy",
     "Corbel designs, builds and integrates software for growing businesses: custom software, web development, systems integration and cloud solutions.",
     ["data.js", "main.js", "home.js"]),
    ("services.html", "Services | Corbel",
     "Software development, web development, integrations and cloud solutions, plus design, data, IT consulting and support.",
     ["data.js", "main.js"]),
    ("work.html", "Case studies | Corbel",
     "Selected projects from Corbel: logistics integrations, healthcare apps, retail platforms, cloud migrations and more.",
     ["data.js", "main.js", "work.js"]),
    ("process.html", "How we work | Corbel",
     "Our five-stage process, the industries we know well, and the technology we use.",
     ["data.js", "main.js"]),
    ("pricing.html", "Pricing | Corbel",
     "Fixed-scope projects, dedicated teams and support retainers. See what each costs and what is included.",
     ["data.js", "main.js"]),
    ("estimate.html", "Project estimator | Corbel",
     "Get a rough budget, timeline and team size for your software, web, integration or cloud project in under a minute.",
     ["data.js", "main.js", "estimate.js"]),
    ("faq.html", "FAQ | Corbel",
     "Answers to common questions about working with Corbel: ownership, pricing, contracts, data protection and support.",
     ["data.js", "main.js"]),
    ("about.html", "About us | Corbel",
     "Corbel is an independent software consultancy based in Nairobi. Our story, values, leadership team and offices.",
     ["data.js", "main.js", "about.js"]),
    ("careers.html", "Careers | Corbel",
     "Open roles at Corbel for engineers, designers and DevOps specialists. Hybrid in Nairobi or remote across East Africa.",
     ["data.js", "main.js"]),
    ("contact.html", "Contact | Corbel",
     "Tell us about your project or book a 30-minute discovery call with a Corbel technical lead.",
     ["data.js", "main.js", "contact.js"]),
]

def roles_html():
    rows = []
    for r in load("roles.json"):
        if not r.get("open", True):
            continue
        body = "".join(f"<p>{esc(p)}</p>" for p in r["description"])
        subject = urllib.parse.quote(r["title"])
        rows.append(f'''<details class="role-row">
        <summary><b>{esc(r["title"])}</b><span>{esc(r["team"])}</span><span>{esc(r["location"])}</span><span class="pm" aria-hidden="true"></span></summary>
        <div class="role-body">
          <div class="prose">{body}</div>
          <div class="actions"><a class="btn btn-primary" href="mailto:careers@corbel.example?subject={subject}">Apply by email</a><span class="small muted">{esc(r["type"])} · {esc(r["salary"])}</span></div>
        </div>
      </details>''')
    if not rows:
        return '<p class="muted">No open roles right now. We still read every speculative application.</p>'
    return '<div class="roles">\n      ' + "\n      ".join(rows) + '\n    </div>'

# Shared data for the site's scripts (stack map, case studies)
data = {"services": load("services.json"), "cases": load("cases.json")}
(OUT / "assets/js/data.js").write_text(
    "/* Corbel — shared content used by several pages.\n"
    "   Generated by build/build.py from build/content/*.json. Do not edit by hand. */\n"
    "window.CORBEL = " + json.dumps(data, indent=2, ensure_ascii=False) + ";\n")

for name, title, desc, scripts in PAGES:
    body = (SRC / name).read_text().replace("{{roles}}", roles_html())
    (OUT / name).write_text(page(name, title, desc, body, scripts))
    print("built", name)

for s in SERVICE_PAGES:
    (OUT / s["file"]).write_text(page(s["file"], attr(s["title"]), attr(s["desc"]), service_page(s), ["data.js", "main.js"]))
    print("built", s["file"])
