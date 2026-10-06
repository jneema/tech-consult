"""Builds the Corbel site's HTML pages.

Run from anywhere:  python3 build/build.py

- build/pages/<name>.html holds the main content of each page. Edit those, not the
  generated .html files in the project root, which are overwritten on every build.
- The header, footer, "Up next" links and <head> are defined once below.
- The four service pages (software-development.html and so on) have no file in
  build/pages; their content lives in SERVICE_PAGES and shares one template.
- {{icon:name}} in a page is replaced with the matching icon from ICONS.
"""
import re, pathlib

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
SERVICE_PAGES = [
    dict(id="software", noun="software", file="software-development.html", name="Software development",
         title="Software development | Corbel",
         desc="Custom platforms, internal tools and iOS and Android apps, built around how your business actually runs.",
         h1="Software built around how your business actually runs.",
         lede="Custom platforms and mobile apps for the work off-the-shelf tools can't handle: your approvals, your pricing rules, your operations. You own every line of code from the first commit.",
         facts=[("Typical length", "3 to 9 months"), ("Starts at", "$18,000"), ("Usual model", "Dedicated team")],
         deliver=[("Internal platforms", "Operations, finance, logistics and approval workflows with role-based access and full audit trails."),
                  ("Mobile apps", "iOS and Android from one codebase, with offline sync, push notifications and in-app payments."),
                  ("SaaS products", "Multi-tenant products with billing, onboarding and admin tooling, built to grow with your customer base."),
                  ("Legacy modernisation", "Rebuild ageing systems piece by piece while the old one keeps running. No big-bang cut-over.")],
         fit=["Your team works around your tools instead of with them",
              "Key processes live in spreadsheets, email threads or one person's head",
              "You need software you own outright, with code in your own repository",
              "An off-the-shelf product covers 70% of what you need and the rest is costing you"],
         stack_label="Typical stack", stack=["TypeScript", "React", "React Native", "Node.js", "Python", ".NET", "PostgreSQL"],
         steps=[("Discovery", "2 weeks", "Workshops with the people who will use it, a map of your current process, and a prioritised backlog."),
                ("Prototype", "2 to 3 weeks", "Clickable screens for the riskiest workflows, tested with real users before we write production code."),
                ("Build in sprints", "2 to 6 months", "Two-week sprints with a demo each time. A staging site you can use from week one."),
                ("Launch and hand-over", "2 weeks", "Data migration, staff training, documentation and 30 days of free fixes.")],
         faqs=[("Will we be locked in to Corbel?", "No. The code lives in your repository, uses mainstream technology, and comes with documentation and tests. Several clients have taken our work in-house."),
               ("Can you build for iOS and Android at the same time?", "Yes. We use React Native or Flutter so one team ships both apps from a single codebase, with native modules where performance needs it."),
               ("Do you work with our in-house developers?", "Often. We can lead the project and pair with your team, or slot in as extra capacity under your tech lead.")]),
    dict(id="web", noun="web", file="web-development.html", name="Web development",
         title="Web development | Corbel",
         desc="Fast, accessible websites, customer portals and e-commerce that your own team can update.",
         h1="Websites and portals that load fast and stay easy to change.",
         lede="Company sites, customer portals and online stores that load in about a second, meet accessibility standards, and can be edited by your own team without calling a developer.",
         facts=[("Typical length", "6 to 14 weeks"), ("Starts at", "$9,000"), ("Usual model", "Fixed scope")],
         deliver=[("Company websites", "Content-managed marketing sites with clean structure, strong SEO foundations and analytics set up properly."),
                  ("Customer portals", "Self-service accounts, order tracking, statements and support, connected to your back-office systems."),
                  ("E-commerce", "Headless storefronts with local and international payments, inventory sync and fast product pages."),
                  ("Performance and accessibility audits", "A prioritised report on speed, SEO and WCAG issues, with fixes we make or hand to your team.")],
         fit=["Your current site is slow on mobile or hard to update",
              "Customers call or email for information they could look up themselves",
              "You sell online and need payments, stock and delivery to stay in sync",
              "You are rebranding and want the site rebuilt properly, not reskinned"],
         stack_label="Typical stack", stack=["Next.js", "Astro", "Sanity", "WordPress (headless)", "Shopify", "Vercel"],
         steps=[("Content and structure", "1 to 2 weeks", "Sitemap, page templates and a content plan agreed with your marketing team."),
                ("Design", "2 to 3 weeks", "Design system and key page designs, reviewed on real devices before build."),
                ("Build and CMS setup", "3 to 8 weeks", "Pages built against a performance budget, with your team editing content in the CMS as we go."),
                ("Launch", "1 week", "Redirects, analytics, search console and a launch checklist, then training for your editors.")],
         faqs=[("Can our marketing team edit the site themselves?", "Yes. Every site comes with a CMS set up around your content, and a training session. Most changes never need a developer."),
               ("Will we lose our search rankings when we move?", "Not if the move is planned. We map every old URL to a new one, keep metadata, and monitor search console for the first months."),
               ("Do you design the site as well?", "Yes. Our designers handle the visual design and content structure, or we can work from your agency's designs.")]),
    dict(id="integrations", noun="integration", file="integrations.html", name="Integrations",
         title="Integrations | Corbel",
         desc="Connect payments, mobile money, CRM, ERP and logistics systems so data is entered once and trusted everywhere.",
         h1="Make the systems you already pay for work as one.",
         lede="Payments, mobile money, CRM, accounting and logistics tools connected properly. Data is entered once, moves automatically, and failures are caught before your customers notice.",
         facts=[("Typical length", "4 to 10 weeks"), ("Starts at", "$7,000"), ("Usual model", "Fixed scope")],
         deliver=[("Payments and mobile money", "M-Pesa, Airtel Money, card and bank integrations with automatic reconciliation and refunds."),
                  ("CRM and ERP sync", "Two-way sync between Salesforce, HubSpot, SAP Business One, Odoo, QuickBooks and Xero."),
                  ("APIs and middleware", "Well-documented APIs and integration layers with queues, retries and idempotency built in."),
                  ("Monitoring and alerting", "Dashboards and alerts for every integration, so a failed sync is fixed in minutes rather than found at month end.")],
         fit=["Staff copy data between systems by hand every day",
              "Finance and operations disagree on the numbers",
              "You are adding a new tool and need it to work with the rest",
              "An existing integration fails silently and nobody notices until month end"],
         stack_label="Systems we connect often", stack=["M-Pesa Daraja", "Airtel Money", "Stripe", "Flutterwave", "Salesforce", "HubSpot", "SAP B1", "Odoo", "Xero", "QuickBooks"],
         steps=[("Systems audit", "1 week", "We document every system, the data that moves between them, and where it breaks today."),
                ("Integration design", "1 week", "Data mapping, error handling and a test plan, agreed with finance and operations."),
                ("Build and test", "2 to 6 weeks", "Built against sandbox accounts, then tested with real data in a controlled rollout."),
                ("Monitor", "Ongoing", "Dashboards and alerts go live with the integration, plus a runbook for your team.")],
         faqs=[("What if the other system doesn't have an API?", "We have integrated with file exports, email parsing and database replication when there was no API. We will tell you the trade-offs up front."),
               ("Who maintains the integration after launch?", "Your choice. We hand over documentation and runbooks, or keep it running under a support retainer with alerting."),
               ("Can you work with our existing vendors?", "Yes. We regularly coordinate with ERP partners and payment providers on your behalf.")]),
    dict(id="cloud", noun="cloud", file="cloud-solutions.html", name="Cloud solutions",
         title="Cloud solutions | Corbel",
         desc="Cloud migration, infrastructure as code, CI/CD and cost reviews on AWS, Azure and Google Cloud.",
         h1="Infrastructure that is cheaper to run and easier to change.",
         lede="Move off ageing servers, cut your hosting bill, and ship new releases without holding your breath. Every environment is written down as code, so nothing depends on one person's memory.",
         facts=[("Typical length", "4 to 12 weeks"), ("Starts at", "$8,000"), ("Usual model", "Fixed scope or retainer")],
         deliver=[("Cloud migration", "Planned moves from on-site servers or other providers, with rehearsed cut-overs and rollback plans."),
                  ("Infrastructure as code", "Every environment defined in Terraform, reviewed like application code, and reproducible in an afternoon."),
                  ("CI/CD and DevOps", "Automated tests and deployments so releasing is routine, not a weekend event."),
                  ("Cost and security reviews", "Right-sizing, reserved capacity and access audits. Most reviews pay for themselves within three months.")],
         fit=["Critical systems run on a server in your office",
              "Your cloud bill keeps growing and nobody is sure why",
              "Deployments are manual, risky or only one person can do them",
              "You need to meet a security or data-residency requirement"],
         stack_label="Platforms and tools", stack=["AWS", "Microsoft Azure", "Google Cloud", "Terraform", "Docker", "Kubernetes", "GitHub Actions"],
         steps=[("Assessment", "1 to 2 weeks", "An inventory of what you run, what it costs, and a migration or improvement plan with a fixed price."),
                ("Foundations", "1 to 2 weeks", "Accounts, networking, access control and Terraform set up the right way from the start."),
                ("Migrate or rebuild", "2 to 6 weeks", "Workloads moved in planned waves, each with a rehearsed cut-over and rollback."),
                ("Optimise", "Ongoing", "Monthly cost and security reviews, patching and backup restore tests.")],
         faqs=[("Which cloud provider should we use?", "It depends on your team, existing licences and where your customers are. We work across AWS, Azure and Google Cloud and will recommend one with reasons."),
               ("Will there be downtime during migration?", "We plan for minimal or zero downtime, with cut-overs rehearsed in advance and scheduled outside your busy hours."),
               ("Can you reduce our current cloud bill?", "Usually. Clients typically save 20 to 40% through right-sizing, reserved capacity and removing forgotten resources.")]),
]

def service_page(s):
    facts = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in s["facts"])
    deliver = "".join(f'<div class="reveal"><h3>{h}</h3><p>{p}</p></div>' for h, p in s["deliver"])
    fit = "".join(f"<li>{x}</li>" for x in s["fit"])
    stack = "".join(f'<li class="tag">{x}</li>' for x in s["stack"])
    steps = "".join(f'<li class="reveal"><h3>{t}</h3><p>{p}</p><span class="dur">{d}</span></li>' for t, d, p in s["steps"])
    faqs = "".join(f'<details><summary>{q}<span class="pm" aria-hidden="true"></span></summary><div><p>{a}</p></div></details>' for q, a in s["faqs"])
    others = "".join(f'<li><a class="link-arrow" href="{f}">{n} {ICONS["arrow"]}</a></li>'
                     for i, f, n, _ in SERVICES_MENU if i != s["id"])
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

for name, title, desc, scripts in PAGES:
    body = (SRC / name).read_text()
    (OUT / name).write_text(page(name, title, desc, body, scripts))
    print("built", name)

for s in SERVICE_PAGES:
    (OUT / s["file"]).write_text(page(s["file"], s["title"], s["desc"], service_page(s), ["data.js", "main.js"]))
    print("built", s["file"])
