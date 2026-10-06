#!/usr/bin/env python3
"""Corbel website and admin server.

    python3 server.py              # http://localhost:8000, admin at /admin/
    python3 server.py --port 9000
    python3 server.py --host 0.0.0.0   # listen on all interfaces (put HTTPS in front)

Admin login: the default is username "admin", password "admin". Change it before the
site is public:
    python3 server.py --set-login      # prompts for a new username and password
or set CORBEL_ADMIN_USER and CORBEL_ADMIN_PASSWORD in the environment. The saved login
is kept (password hashed) in data/admin.json; delete that file to go back to the default.

Everything the server writes lives in data/ (form submissions, content backups).
The admin posts case studies and job openings (build/content/cases.json and roles.json),
then rebuilds the site. Page wording, layout and service pages are changed in code.
Only the Python standard library is used.
"""
import argparse
import getpass
import hashlib
import hmac
import http.server
import json
import mimetypes
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CONTENT = ROOT / "build" / "content"
BACKUPS = DATA / "backups"
SUBMISSIONS = DATA / "submissions.json"

CONTENT_FILES = {"cases": "cases.json", "roles": "roles.json", "services": "services.json"}
EDITABLE = {"cases", "roles"}      # services is read-only here: the case study form lists them
STATUSES = ["new", "contacted", "proposal", "won", "lost", "archived"]
SESSION_HOURS = 12
MAX_BODY = 512 * 1024

lock = threading.Lock()          # guards submissions and content writes
build_lock = threading.Lock()
sessions = {}                    # token -> expiry timestamp
hits = {}                        # (bucket, ip) -> [timestamps]
last_build = {"ok": None, "at": None, "log": ""}


# ---------------------------------------------------------------- helpers
def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path, value):
    """Write atomically so a crash never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def backup(path):
    if not path.exists():
        return
    BACKUPS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(path, BACKUPS / f"{path.stem}-{stamp}{path.suffix}")
    # keep the 30 most recent backups of each file
    olds = sorted(BACKUPS.glob(f"{path.stem}-*{path.suffix}"))
    for old in olds[:-30]:
        old.unlink()


def rate_limited(bucket, ip, limit, window):
    t = time.time()
    key = (bucket, ip)
    recent = [x for x in hits.get(key, []) if t - x < window]
    recent.append(t)
    hits[key] = recent
    return len(recent) > limit


def run_build():
    with build_lock:
        proc = subprocess.run([sys.executable, str(ROOT / "build" / "build.py")],
                              capture_output=True, text=True, timeout=60)
        last_build.update(ok=proc.returncode == 0, at=now_iso(),
                          log=(proc.stdout + proc.stderr).strip())
        return dict(last_build)


# ---------------------------------------------------------------- password
def password_hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()


DEFAULT_USER = DEFAULT_PASSWORD = "admin"


def make_login(user, pw):
    salt = secrets.token_hex(16)
    return {"user": user, "salt": salt, "hash": password_hash(pw, salt)}


def setup_login():
    """Return (login, is_default). Environment variables win over data/admin.json."""
    env_user, env_pw = os.environ.get("CORBEL_ADMIN_USER"), os.environ.get("CORBEL_ADMIN_PASSWORD")
    if env_pw:
        user = env_user or DEFAULT_USER
        return make_login(user, env_pw), (user, env_pw) == (DEFAULT_USER, DEFAULT_PASSWORD)
    cfg = read_json(DATA / "admin.json", None)
    if not cfg or "user" not in cfg:        # first run, or a file from before usernames existed
        cfg = make_login(DEFAULT_USER, DEFAULT_PASSWORD)
        save_login(cfg)
    is_default = cfg["user"] == DEFAULT_USER and hmac.compare_digest(password_hash(DEFAULT_PASSWORD, cfg["salt"]), cfg["hash"])
    return cfg, is_default


def save_login(cfg):
    write_json(DATA / "admin.json", cfg)
    os.chmod(DATA / "admin.json", 0o600)


def set_login_interactively():
    user = input("New admin username: ").strip()
    pw = getpass.getpass("New admin password: ")
    if not user or len(pw) < 8:
        sys.exit("Username is required and the password must be at least 8 characters. Nothing changed.")
    if getpass.getpass("Repeat password: ") != pw:
        sys.exit("Passwords did not match. Nothing changed.")
    DATA.mkdir(exist_ok=True)
    save_login(make_login(user, pw))
    print("Admin login saved. Restart the server for it to take effect.")


# ---------------------------------------------------------------- validation
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def clean(value, limit=4000):
    return str(value or "").strip()[:limit]


def validate_submission(kind, body):
    """Return (record, error). Only whitelisted fields are kept."""
    if kind == "newsletter":
        email = clean(body.get("email"), 200)
        if not EMAIL.match(email):
            return None, "Enter a valid email address."
        return {"email": email}, None
    if kind == "brief":
        rec = {k: clean(body.get(k)) for k in ("name", "email", "company", "phone", "message",
                                                "stage", "budget", "timing", "source")}
        rec["services"] = [clean(s, 80) for s in (body.get("services") or [])][:10]
        rec["nda"] = bool(body.get("nda"))
        if len(rec["name"]) < 2 or not EMAIL.match(rec["email"]) or len(rec["message"]) < 20:
            return None, "Name, a valid email and a short message are required."
        return rec, None
    if kind == "call":
        rec = {k: clean(body.get(k), 300) for k in ("name", "email", "topic", "when", "startUTC")}
        if len(rec["name"]) < 2 or not EMAIL.match(rec["email"]) or not rec["startUTC"]:
            return None, "Name, a valid email and a time slot are required."
        try:
            start = datetime.fromisoformat(rec["startUTC"].replace("Z", "+00:00"))
        except ValueError:
            return None, "Invalid time slot."
        if start < datetime.now(timezone.utc):
            return None, "That time is in the past."
        rec["startUTC"] = start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        return rec, None
    return None, "Unknown form."


REQUIRED = {
    "cases": ["id", "client", "svc", "ind", "title", "metric", "mlabel"],
    "roles": ["title", "team", "location"],
}


def validate_content(name, value):
    if not isinstance(value, list):
        return "Expected a list."
    for i, item in enumerate(value, 1):
        if not isinstance(item, dict):
            return f"Item {i} is not an object."
        for key in REQUIRED[name]:
            if not str(item.get(key, "")).strip():
                return f"Item {i}: '{key}' is required."
    if name == "cases":
        ids = [c["id"] for c in value]
        if len(ids) != len(set(ids)):
            return "Two case studies have the same ID."
        if any(not re.fullmatch(r"[a-z0-9-]+", i) for i in ids):
            return "Case study IDs may only use lowercase letters, numbers and dashes."
    if name == "cases":
        services = {s["id"] for s in read_json(CONTENT / "services.json", [])}
        bad = next((c["client"] for c in value if c["svc"] not in services), None)
        if bad:
            return f"{bad}: unknown service."
    return None


# ---------------------------------------------------------------- handler
class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "Corbel"

    # -- plumbing
    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    @property
    def ip(self):
        return self.client_address[0]

    def send_json(self, status, value, headers=None):
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("Request too large.")
        raw = self.rfile.read(length) if length else b""
        if "json" in (self.headers.get("Content-Type") or ""):
            return json.loads(raw or b"null")
        return raw.decode()

    def token(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "corbel_admin":
                return v
        return None

    def is_admin(self):
        tok = self.token()
        exp = sessions.get(tok) if tok else None
        if exp and exp > time.time():
            return True
        sessions.pop(tok, None)
        return False

    def require_admin(self, mutating):
        if not self.is_admin():
            self.send_json(401, {"error": "Please sign in."})
            return False
        # Cross-site requests can't set this header without a CORS preflight we never allow
        if mutating and self.headers.get("X-Corbel-Admin") != "1":
            self.send_json(403, {"error": "Missing admin header."})
            return False
        return True

    # -- routing
    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            return self.api("GET", path)
        return self.static(path)

    def do_HEAD(self):
        return self.static(urlparse(self.path).path, head=True)

    def do_POST(self):
        return self.api("POST", urlparse(self.path).path)

    def do_PUT(self):
        return self.api("PUT", urlparse(self.path).path)

    def do_PATCH(self):
        return self.api("PATCH", urlparse(self.path).path)

    def do_DELETE(self):
        return self.api("DELETE", urlparse(self.path).path)

    # -- static files: the generated site, its assets and the admin UI only
    def static(self, path, head=False):
        path = unquote(path)
        if path in ("/", ""):
            path = "/index.html"
        if path in ("/admin", "/admin/"):
            path = "/admin/index.html"
        rel = path.lstrip("/")
        allowed = (re.fullmatch(r"[a-z0-9-]+\.html", rel)
                   or rel.startswith("assets/") or rel.startswith("admin/"))
        target = (ROOT / rel).resolve()
        if not allowed or ROOT not in target.parents or not target.is_file():
            body = b"Not found"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if not head:
                self.wfile.write(body)
            return
        data = target.read_bytes()
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        if rel.startswith("admin/"):
            self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        if not head:
            self.wfile.write(data)

    # -- API
    def api(self, method, path):
        try:
            return self.route(method, path)
        except (ValueError, json.JSONDecodeError) as e:
            return self.send_json(400, {"error": str(e) or "Bad request."})
        except Exception as e:  # keep the server up, report the problem
            self.log_message("error: %r", e)
            return self.send_json(500, {"error": "Server error. Check the server log."})

    def route(self, method, path):
        parts = [p for p in path.split("/") if p][1:]   # drop "api"

        # Public: website forms and booked slots
        if method == "POST" and len(parts) == 2 and parts[0] == "submit":
            return self.submit(parts[1])
        if method == "GET" and parts == ["slots"]:
            with lock:
                subs = read_json(SUBMISSIONS, [])
            taken = sorted({s["startUTC"] for s in subs
                            if s["type"] == "call" and s["status"] not in ("lost", "archived")})
            return self.send_json(200, {"taken": taken})

        # Session
        if parts == ["login"] and method == "POST":
            return self.login()
        if parts == ["logout"] and method == "POST":
            sessions.pop(self.token(), None)
            return self.send_json(200, {"ok": True}, {"Set-Cookie": "corbel_admin=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"})
        if parts == ["session"] and method == "GET":
            return self.send_json(200, {"admin": self.is_admin(), "build": last_build})

        # Everything below is admin-only
        if not self.require_admin(method != "GET"):
            return

        if parts == ["submissions"] and method == "GET":
            with lock:
                return self.send_json(200, read_json(SUBMISSIONS, []))
        if len(parts) == 2 and parts[0] == "submissions":
            return self.update_submission(method, parts[1])

        if len(parts) == 2 and parts[0] == "content" and parts[1] in CONTENT_FILES:
            file = CONTENT / CONTENT_FILES[parts[1]]
            if method == "GET":
                return self.send_json(200, read_json(file, []))
            if method == "PUT" and parts[1] in EDITABLE:
                value = self.read_body()
                err = validate_content(parts[1], value)
                if err:
                    return self.send_json(422, {"error": err})
                with lock:
                    backup(file)
                    write_json(file, value)
                return self.send_json(200, {"saved": True, "build": run_build()})

        if parts == ["build"] and method == "POST":
            return self.send_json(200, {"build": run_build()})

        return self.send_json(404, {"error": "Not found."})

    def login(self):
        if rate_limited("login", self.ip, 5, 60):
            return self.send_json(429, {"error": "Too many attempts. Wait a minute and try again."})
        body = self.read_body() or {}
        user, pw = str(body.get("username", "")).strip(), str(body.get("password", ""))
        cfg = self.server.login
        # Check both, always hashing, so the response doesn't reveal which one was wrong
        user_ok = hmac.compare_digest(user.encode(), cfg["user"].encode())
        pw_ok = hmac.compare_digest(password_hash(pw, cfg["salt"]), cfg["hash"])
        if not (user_ok and pw_ok):
            time.sleep(0.5)
            return self.send_json(401, {"error": "Wrong username or password."})
        tok = secrets.token_urlsafe(32)
        sessions[tok] = time.time() + SESSION_HOURS * 3600
        cookie = f"corbel_admin={tok}; Path=/; Max-Age={SESSION_HOURS * 3600}; HttpOnly; SameSite=Strict"
        return self.send_json(200, {"ok": True}, {"Set-Cookie": cookie})

    def submit(self, kind):
        if kind not in ("brief", "call", "newsletter"):
            return self.send_json(404, {"error": "Unknown form."})
        if rate_limited("submit", self.ip, 20, 3600):
            return self.send_json(429, {"error": "Too many submissions. Please email us instead."})
        body = self.read_body()
        if not isinstance(body, dict):
            raise ValueError("Expected a JSON object.")
        if body.get("website"):                     # honeypot field, filled only by bots
            return self.send_json(200, {"ok": True})
        rec, err = validate_submission(kind, body)
        if err:
            return self.send_json(422, {"error": err})
        with lock:
            subs = read_json(SUBMISSIONS, [])
            if kind == "newsletter" and any(s["type"] == "newsletter" and s["email"].lower() == rec["email"].lower() for s in subs):
                return self.send_json(200, {"ok": True, "duplicate": True})
            if kind == "call" and any(s["type"] == "call" and s["startUTC"] == rec["startUTC"]
                                      and s["status"] not in ("lost", "archived") for s in subs):
                return self.send_json(409, {"error": "That slot was just booked. Please choose another time."})
            ref = clean(body.get("ref"), 20)
            if not re.fullmatch(r"CRB-\d{4}", ref):
                ref = f"CRB-{secrets.randbelow(9000) + 1000}"
            rec.update(id=secrets.token_hex(6), type=kind, ref=ref, status="new", note="", created=now_iso())
            subs.append(rec)
            write_json(SUBMISSIONS, subs)
        return self.send_json(201, {"ok": True, "ref": ref})

    def update_submission(self, method, sid):
        with lock:
            subs = read_json(SUBMISSIONS, [])
            match = next((s for s in subs if s["id"] == sid), None)
            if not match:
                return self.send_json(404, {"error": "Not found."})
            if method == "DELETE":
                subs.remove(match)
            elif method == "PATCH":
                body = self.read_body() or {}
                if "status" in body:
                    if body["status"] not in STATUSES:
                        return self.send_json(422, {"error": "Unknown status."})
                    match["status"] = body["status"]
                if "note" in body:
                    match["note"] = clean(body["note"], 4000)
                match["updated"] = now_iso()
            else:
                return self.send_json(405, {"error": "Method not allowed."})
            write_json(SUBMISSIONS, subs)
        return self.send_json(200, match if method == "PATCH" else {"deleted": True})


def main():
    ap = argparse.ArgumentParser(description="Serve the Corbel site and admin.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--set-login", action="store_true", help="change the admin username and password, then exit")
    args = ap.parse_args()

    if args.set_login:
        return set_login_interactively()
    DATA.mkdir(exist_ok=True)
    login, is_default = setup_login()
    srv = http.server.ThreadingHTTPServer((args.host, args.port), Handler)
    srv.login = login
    run_build()
    print(f"Corbel running at http://{args.host}:{args.port}/  (admin: /admin/)", flush=True)
    if is_default:
        print('Warning: the admin login is still the default (admin / admin). '
              'Change it with "python3 server.py --set-login" before sharing the site.', flush=True)
    if not last_build["ok"]:
        print("Warning: the initial build failed:\n" + last_build["log"], flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
