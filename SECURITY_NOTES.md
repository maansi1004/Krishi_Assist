# KrishiAssist: security notes

What the project protects today, and what it does not. Useful for the report and for interviews.

## In place
- **Passwords** are never stored. Each one is salted and hashed with PBKDF2-SHA256 (310,000 rounds).
- **Login tokens** (JWT) must carry an expiry time and a subject, are signed, and last 60 minutes.
- **Guessing protection:** 5 failed sign-ins per e-mail and address, and 20 per address, lock sign-in for 15 minutes (HTTP 429 with a Retry-After header). Sign-ups are limited to 10 per hour per address.
- **No user enumeration by timing:** an unknown e-mail costs the same time as a wrong password.
- **Production guard:** with `APP_ENV=production` the server refuses to start unless `JWT_SECRET` is a random value of 32+ characters. The API docs are switched off in production.
- **Allowed websites (CORS)** come from the `CORS_ORIGINS` setting, not from code.
- **One database location:** a relative SQLite path always means "inside the project folder".
- **Audit trail:** key actions are recorded without passwords, e-mail addresses or profile values.
- **Tests** run on their own temporary database and never touch development data.

## Known limits (be upfront about these)
- The rate limiter is **in memory**: it resets when the server restarts and is not shared between server processes. A production deployment would use Redis.
- Behind a reverse proxy the limiter sees the proxy's address unless the proxy passes the real client address on.
- The login token is kept in the browser's `localStorage`, so a cross-site-scripting bug would expose it. An HttpOnly cookie is safer.
- There is no refresh token: after 60 minutes the farmer signs in again.
- Registering an already-used e-mail says so (a usability choice that lets people discover which e-mails have accounts).
- Passwords only need 8 characters; there is no breached-password check and no e-mail verification.
- SQLite is for the prototype; PostgreSQL is the production target.

## Administrator access
- The `admin` role can only be given by running `python -m app.scripts.make_admin` on the server. There is no web page, API call or registration option that grants it.
- The role is read from the database on every request, so removing it works at once even for a token that was already issued.
- Admin pages are protected on the server (HTTP 403). Hiding the button in the browser is only a convenience.

## The AI need reader
- Its suggestions are shown to the farmer and nothing is saved or checked until they confirm.
- The AI can only suggest state, land size, age, farmer type, main crop and topics. It is never asked for, and is never allowed to supply, caste/social category or gender; those come only from the farmer's own words.
- Everything the AI returns is checked against fixed allowed values and number ranges. The sentence is treated as data, not instructions.
- The sentence itself is not stored in the audit trail, only which kinds of details were found.
- Each farmer may use it 30 times per hour.

## Document uploads
In place:
- Only the signed-in farmer can see, download, change or delete their own documents. Someone else's document answers "not found", exactly like a document that does not exist.
- A file is accepted only if its real content is a PDF, JPEG or PNG (checked from the first bytes). The file name and the type the browser claims are ignored, so a text or program file renamed to `.pdf` is refused.
- Size is limited while the file is being received (5 MB by default), so a huge upload cannot fill the server's memory. Each farmer also has limits on the number of files (25), total size (50 MB) and uploads per hour (30). Exact duplicate files are refused.
- Files are stored outside the website files, under random names the server makes (`storage/uploads/<user id>/<random>.pdf`). The name the farmer typed is never used in a path, and every path is checked to stay inside the upload folder. A file is written completely or not at all.
- Files are only served by the API, with `nosniff`, `no-store` and frame-blocking headers.
- The audit trail records what kind of document and how big, never the file name, note or contents.

Known limits (be upfront about these):
- Files are stored on the server's disk **without encryption**. Anyone with access to the server's disk can read them. Encryption at rest or cloud storage would be added in `services/document_storage.py`.
- There is no antivirus scan. A PDF can contain active content; browsers open PDFs in their own sandbox.
- Storage is local to one server. Back up the `storage` folder together with the database.
- There is no "delete my account" feature yet, so documents stay until the farmer deletes them.
