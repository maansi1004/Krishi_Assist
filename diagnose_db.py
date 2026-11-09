"""Finds out WHICH database file the running KrishiAssist server really writes to.

Put this file in your project folder (next to SETUP_WINDOWS.bat), start your backend
the normal way, then run:

    python diagnose_db.py

It only uses Python's standard library, so any Python works. It registers one throw-away
account on the running server, looks for that account in every .db file around your project,
reports which file got it, and then deletes the throw-away account again.
"""
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
import uuid

API = os.environ.get("KA_API", "http://127.0.0.1:8000").rstrip("/")
ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {"node_modules", ".venv", ".git", "__pycache__", "dist", ".pytest_cache"}


def say(text=""):
    print(text, flush=True)


def http(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "null")
        except Exception:
            return e.code, None
    except Exception as e:  # server not reachable
        return None, str(e)


def find_db_files():
    found = []
    for base in {ROOT, os.path.dirname(ROOT)}:
        base_depth = base.rstrip(os.sep).count(os.sep)
        for folder, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in SKIP]
            if folder.count(os.sep) - base_depth >= 4:
                dirs[:] = []
            for f in files:
                if f.endswith((".db", ".sqlite", ".sqlite3")):
                    path = os.path.join(folder, f)
                    if path not in found:
                        found.append(path)
    return found


def users_in(path):
    try:
        c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        rows = c.execute("select id, email, role from users order by id").fetchall()
        c.close()
        return rows
    except Exception:
        return None


say("=" * 64)
say("KrishiAssist database check")
say("=" * 64)

# 1. What THIS folder's files say
cfg = os.path.join(ROOT, "backend", "app", "core", "config.py")
cfg_text = open(cfg, encoding="utf-8").read() if os.path.exists(cfg) else ""
path_fixed = "_sqlite_path_does_not_depend_on_the_folder" in cfg_text
has_admin_code = os.path.exists(os.path.join(ROOT, "backend", "app", "scripts", "make_admin.py"))
env_file = os.path.join(ROOT, ".env")
env_url = ""
if os.path.exists(env_file):
    for line in open(env_file, encoding="utf-8", errors="ignore"):
        if line.strip().startswith("DATABASE_URL="):
            env_url = line.split("=", 1)[1].strip()


def sqlite_file(url):
    """The file a sqlite:/// address points to, or None when it cannot be worked out."""
    if not url.startswith("sqlite:///"):
        return None
    p = url[len("sqlite:///"):]
    if not p or p.startswith(":memory:"):
        return None
    if not os.path.isabs(p):
        if not path_fixed:
            return None          # old config: depends on the folder the server was started from
        p = os.path.join(ROOT, p)
    return os.path.normcase(os.path.normpath(p))


if env_url:
    expected = sqlite_file(env_url)
else:
    expected = os.path.normcase(os.path.normpath(os.path.join(ROOT, "krishiassist.db"))) if path_fixed else None

say(f"\n1) This project folder: {ROOT}")
say(f"   config.py has the database-path fix ........ {'yes' if path_fixed else 'NO  (old config: path depends on the folder you start from)'}")
say(f"   admin tool (make_admin.py) present ......... {'yes' if has_admin_code else 'NO'}")
say(f"   .env sets DATABASE_URL ..................... {env_url if env_url else 'no'}")
if expected:
    say(f"   so this folder's code uses this database ... {expected}")

# 2. The running server
say(f"\n2) The server answering at {API}")
status, health = http("GET", "/health")
if status != 200:
    say("   NOT REACHABLE: the backend is not running. Start it first, in ANOTHER window:")
    say("      START_BACKEND.bat      (or: cd backend, activate the environment, then")
    say("      python -m uvicorn app.main:app --host 127.0.0.1 --port 8000)")
    say("   Wait until it says 'Application startup complete', then run this check again.")
    say(f"   ({health})")
    sys.exit(1)
say(f"   reachable, reports: {health}")
s_admin, _ = http("GET", "/api/admin/coverage")
server_has_admin = s_admin in (401, 403)
say(f"   server has the admin code .................. {'yes' if server_has_admin else 'NO  (this is an OLD server)'}")

# 3. Register a throw-away account and see where it lands
email = f"diag-{uuid.uuid4().hex[:8]}@example.com"
status, reply = http("POST", "/api/auth/register", {"name": "Diagnostic User", "email": email, "password": "DiagPass12345"})
say(f"\n3) Registering a throw-away account on that server ... HTTP {status}")
if status != 200:
    say(f"   Could not register ({reply}). Wait a minute and try again if it says 'too many'.")
    sys.exit(1)

hits = []
for path in find_db_files():
    rows = users_in(path)
    if rows is None:
        continue
    if any(r[1] == email for r in rows):
        hits.append(path)

say("\n4) Database files around your project:")
for path in find_db_files():
    rows = users_in(path)
    mark = "  <-- the server wrote the new account HERE" if path in hits else ""
    say(f"   {path}")
    say(f"      {len(rows) if rows is not None else '?'} users{mark}")
    for r in (rows or []):
        if r[1] != email:
            say(f"        id={r[0]}  {r[1]}  role={r[2]}")

# 5. clean up the throw-away account
for path in hits:
    try:
        c = sqlite3.connect(path)
        uid = c.execute("select id from users where email=?", (email,)).fetchone()
        if uid:
            for table in ("audit_logs", "farm_profiles", "saved_schemes", "applications", "evaluations"):
                try:
                    c.execute(f"delete from {table} where user_id=?", (uid[0],))
                except Exception:
                    pass
            c.execute("delete from users where id=?", (uid[0],))
            c.commit()
        c.close()
    except Exception:
        pass

# 6. Verdict
say("\n" + "=" * 64)
say("RESULT")
say("=" * 64)
if not hits:
    say("The new account was not found in any .db file near your project.")
    say("The server probably uses a database somewhere else (check DATABASE_URL in .env,")
    say("or in the environment). Tell me the first lines of your START_BACKEND output.")
else:
    real = os.path.normcase(os.path.normpath(hits[0]))
    say(f"The running server saves accounts in:\n   {hits[0]}")
    problems = []
    if expected and real != expected:
        problems.append("This is NOT the database file this folder's settings point to:\n"
                        f"   settings say: {expected}\n"
                        "   A server from a different folder (or older version) is answering on port 8000,\n"
                        "   or the .env file was changed after the server started (restart the server).")
    if has_admin_code and not server_has_admin:
        problems.append("The server on port 8000 is an OLD version without the admin code,\n"
                        "   although this folder has it. Stop it and start the backend from THIS folder.")
    if not path_fixed:
        problems.append("config.py in this folder is missing the database-path fix. Copy backend\\app\\core\\config.py from v4.")
    if problems:
        say("\nPROBLEMS FOUND:")
        for p in problems:
            say(" - " + p)
        say("\nWHAT TO DO (Windows):")
        say("   1. Find what is using port 8000:   netstat -ano | findstr :8000")
        say("   2. Stop it (replace 1234 with the PID in the last column):   taskkill /PID 1234 /F")
        say("   3. Start the backend from THIS folder (START_BACKEND.bat) and run this check again.")
    else:
        say("\nGOOD: the running server uses this folder's database.")
        say("Open exactly that file in your database viewer, and refresh it after registering.")
        say("make_admin (run from this folder's backend folder) will find users in the same file.")
