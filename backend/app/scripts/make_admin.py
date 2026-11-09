"""Give (or take away) administrator rights.   Run from the ka\\backend folder:

    python -m app.scripts.make_admin farmer@example.com
    python -m app.scripts.make_admin farmer@example.com --revoke

There is deliberately no web page for this: nobody can make themselves an administrator
from the browser. Register the account normally first, then run this on the server.
"""
from __future__ import annotations

import sys

from app.db.session import Base, SessionLocal, engine
import app.models  # noqa: F401  (makes sure every table is known)
from app.models.user import User
from app.services.audit import log_event


def set_role(db, email: str, role: str) -> bool:
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user:
        return False
    user.role = role
    db.commit()
    log_event(db, user.id, "role_changed", {"role": role, "by": "make_admin script"})
    return True


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print("Usage: python -m app.scripts.make_admin EMAIL [--revoke]")
        return 2
    role = "farmer" if "--revoke" in argv else "admin"
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if not set_role(db, args[0], role):
            print(f"No account with the e-mail {args[0]}. Register it first, then run this again.")
            return 1
    print(f"{args[0]} is now: {role}. They must sign out and sign in again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
