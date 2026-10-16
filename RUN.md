# KrishiAssist — final local run guide

## Easiest Windows method

1. Extract this ZIP to a normal folder (do not open/edit files inside the ZIP).
2. Double-click `SETUP_WINDOWS.bat` once.
3. Double-click `START_BACKEND.bat`. Keep that window open.
4. Double-click `START_FRONTEND.bat`. Keep that window open.
5. Open `http://localhost:5173`.

The API should respond at:
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/api/schemes

## Manual backend

From the project root:

```powershell
cd backend
.venv\Scripts\activate
$env:PYTHONPATH="."
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Manual frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

## Test the app

1. Register a test farmer.
2. Save a profile such as farmer + Gujarat + 5 hectares.
3. Search `tractor subsidy`.
4. Open AGR-50.
5. Check eligibility.
6. Use Application Plan to see documents, steps, official portal and create a tracking record.
7. Save a scheme and open Saved Schemes.
8. Open Applications and update status.
9. Ask the Assistant:
   - `What documents do I need for crop insurance?`
   - `Give me information about schemes related to machinery`
   - `Am I eligible for tractor subsidy?`
   - `What is PM-KISAN?`
   - `How can I improve soil health?`
10. Switch to Hindi and verify scheme names/descriptions and assistant replies are localized.

## Backend tests

From the project root:

```powershell
$env:PYTHONPATH="backend"
pytest -q
```

## Important

- The assistant can run without an external LLM using the verified scheme dataset and agriculture knowledge base.
- OpenRouter is optional. If configured, it is only a fallback for general agriculture questions; it must not decide scheme eligibility.
- Government applications are not submitted automatically. The Application Plan creates a KrishiAssist tracking record and links to the verified official portal.


## API connection troubleshooting

This build calls the FastAPI backend directly at `http://127.0.0.1:8000` in local development.
Keep `START_BACKEND.bat` running before using the frontend.

Verify:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/api/diagnostics`

If these do not open, the backend is not running or port 8000 is occupied by another process.
