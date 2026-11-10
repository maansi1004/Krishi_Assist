# KrishiAssist: document upload and storage (add-on for v4)

## What farmers get
1. **Profile page:** under the farm profile, "Upload your key documents now". It shows the 5 documents most schemes ask for (counted from your real scheme data, for example "Asked by 14 schemes") with an Upload button each.
2. **Documents page** (new "Documents" button in the top bar): upload any document, give it a type and a note, view it, download it, change its type, delete it. It also shows how much space is used.
3. **Plan application** (the existing planner window): the "Documents" part now checks what the farmer has already uploaded and asks only about the rest. For each missing document the farmer chooses:
   - **Upload now** (right there), or
   - **I have it** (nothing to upload), or
   - **I don't have it yet**: a numbered "Next steps: documents to arrange" card appears with how to get it (in English, Hindi or Hinglish), or
   - **Not applicable to me**: the item closes and no step is added.
4. **Scheme details** and each **application card** show one line such as "Documents: 3 of 5 ready".

## Where each file goes
Paths are relative to your project folder (the one that has `backend`, `frontend`, `tests` and `SETUP_WINDOWS.bat`).

| Add or update | Path | What to do |
|---|---|---|
| NEW | `backend/app/models/document.py` | add the file |
| NEW | `backend/app/services/upload_checks.py` | add the file |
| NEW | `backend/app/services/document_storage.py` | add the file |
| NEW | `backend/app/services/document_types.py` | add the file |
| NEW | `backend/app/services/how_to_get.py` | add the file |
| NEW | `backend/app/api/documents.py` | add the file |
| NEW | `frontend/src/documents.tsx` | add the file |
| NEW | `tests/test_phase12_documents.py` | add the file |
| NEW | `tests/test_phase13_document_plan.py` | add the file |
| UPDATED | `backend/app/models/__init__.py` | replace the file |
| UPDATED | `backend/app/core/config.py` | replace the file |
| UPDATED | `backend/app/services/rate_limit.py` | replace the file |
| UPDATED | `backend/app/main.py` | replace the file |
| UPDATED | `tests/conftest.py` | replace the file |
| UPDATED | `frontend/src/main.tsx` | replace the file (back up yours first; `main.tsx.changes.diff` lists the exact changes if you edited it yourself) |
| UPDATED | `frontend/src/styles.css` | replace the file |
| UPDATED | `.env.example` | replace the file (your own `.env` is not touched) |
| UPDATED | `SECURITY_NOTES.md` | replace the file |
| UPDATED | `check_files.py` | replace the file |
| MANUAL | `.gitignore` | add two lines at the end: `# Uploaded documents (personal data, never commit)` and `storage/` |

Not copied into the project: `main.tsx.changes.diff` (read-only list of changes) and this guide.

## How to add it
1. Stop the backend and frontend. Make a backup copy of your project folder.
2. Extract the zip to a temporary folder. Copy the folders `backend`, `frontend`, `tests` and the files `check_files.py`, `.env.example`, `SECURITY_NOTES.md` into your project folder, choosing **Replace the files in the destination**.
3. Open `.gitignore` and add the two lines from the table above.
4. In the project folder run `python check_files.py`. You need to see `All files are correct.`
5. Run the tests from the project folder:
   ```
   set PYTHONPATH=backend
   pytest -q
   ```
   You should see `204 passed`. The tests use their own temporary database and upload folder, so your real data is untouched.
6. Start the backend (`START_BACKEND.bat`). The two new database tables (`documents`, `document_choices`) are created automatically; there is nothing to migrate and existing data is kept.
7. Start the frontend (`START_FRONTEND.bat`), sign in, and open the **Profile** page. You should see "Upload your key documents now".
8. Check it end to end: upload a PDF from the profile page, open **Documents**, then open a scheme, press **Prepare documents**, and answer a missing document with "I don't have it yet". The next-steps card should appear.

## Where files are stored
- On disk: `storage/uploads/<user id>/<random name>.pdf|jpg|png` inside your project folder. It is created on the first upload and is ignored by Git.
- In the database (`krishiassist.db`): one row per file (type, size, checksum, display name, note) and one row per answer the farmer gave in the planner.
- **Back up the `storage` folder together with `krishiassist.db`.** Restoring only one of them leaves records without files or files without records (the app then says "The stored file is missing. Please upload it again.").
- To store files elsewhere, set `UPLOAD_DIR` in `.env` (a full path such as `D:/KrishiFiles`, or a relative one). Restart the backend after changing `.env`.

## Settings (all optional, in `.env`)
| Setting | Default | Meaning |
|---|---|---|
| `UPLOAD_DIR` | `storage/uploads` | where files are kept |
| `MAX_UPLOAD_MB` | 5 | largest single file |
| `MAX_DOCUMENTS_PER_USER` | 25 | files per farmer |
| `MAX_STORAGE_MB_PER_USER` | 50 | total size per farmer |
| `UPLOAD_MAX_PER_HOUR` | 30 | uploads per farmer per hour |

## What it accepts
PDF, JPEG and PNG only, judged by the real content of the file (a text file renamed `.pdf` is refused). Exact duplicate files are refused.

## Honest limits
- Files are **not encrypted** on the server's disk. Do not run this on a shared computer with real farmers' documents until encryption or cloud storage is added (only `document_storage.py` would change).
- No antivirus scan.
- Local storage on one server only.
- The "how to get this document" steps are general guidance. Offices and portals differ by state, and the screen says so. Only four well-known official websites are linked (UIDAI, DigiLocker, UDID/Swavlamban, Soil Health Card).

## Troubleshooting
- "Schemes" page opens but the Documents button is missing: you are not signed in, or `main.tsx` was not replaced. Run `python check_files.py`.
- Upload says "Upload failed": check the backend window for a message, and that `UPLOAD_DIR` points to a folder the program may write to.
- Old accounts and data are unchanged; documents are per farmer, so existing farmers start with none.
