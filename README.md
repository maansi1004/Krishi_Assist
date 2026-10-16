# KrishiAssist

**Explainable AI-Powered Agricultural Support & Decision System**

Core principle: **AI understands. Rules decide. Evidence explains. Workflow guides.**

## Phase 2 completed

The scheme intelligence foundation is now implemented:

- `data/scheme.schema.json` — machine-readable scheme contract
- `data/schemes.json` — 11 reviewed schemes from the project specification
- Generic recursive eligibility engine
- `AND`, `OR`, `NOT`
- `equals`, `not_equals`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `exists`
- `PASS`, `FAIL`, `UNKNOWN` criterion semantics
- `ELIGIBLE`, `ALMOST_ELIGIBLE`, `NOT_ELIGIBLE`, `VERIFICATION_REQUIRED`
- Blocking exclusion logic with safe handling of unknown exclusions
- Criterion-level explanations, missing requirements and remediation
- Separate verification conditions for workflow gates such as pre-approval
- Machine-readable benefit calculation for fixed and percentage/cap benefits
- Structured documents, action steps, portals and sources
- JSON Schema validation + duplicate scheme-code validation
- 16 automated tests passing

### Reviewed scheme set

1. PM-KISAN
2. PMFBY
3. NFSM
4. Uttarakhand PMKSY – Har Khet Ko Pani
5. Aromatic Plants Cultivation – CAP, Uttarakhand
6. Tamil Nadu Farmers Interest Group
7. Assam Mukhya Mantri Krishi Sa Sajuli Yojana
8. Gujarat AGR-2 Farm Mechanization
9. Uttarakhand Agricultural Investment Grant – Crop Damage 33%+
10. Gujarat AGR-50 Assistance to Purchase Tractors
11. Gujarat Agricultural Skill Development Training Programme

Where the project specification says current external verification is required, the dataset preserves that uncertainty instead of inventing a rule or URL.

## Run backend

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

## Validate scheme data

From the repository root:

```bash
PYTHONPATH=backend python backend/app/services/scheme_validator.py
```

Expected:

```text
SCHEME VALIDATION PASSED
```

## Test

From the repository root:

```bash
PYTHONPATH=backend pytest -q
```

## Example AGR-50 flow

A Gujarat farmer requesting tractor support can be evaluated as:

```text
Gujarat farmer
      +
empanelled tractor model = known
      +
authorized dealer = known
      +
pre-approval = unknown
      ↓
ALMOST_ELIGIBLE
```

A Punjab farmer fails the Gujarat state criterion and is `NOT_ELIGIBLE`.

Eligibility is never determined by an LLM or by a relevance score.

## Next phase

Phase 3: PostgreSQL + SQLAlchemy + JWT authentication + persistent farmer profiles/evaluation history.

## Phase 4 frontend

A professional agriculture-themed React/Vite frontend has been added under `frontend/`. It includes an image-led homepage with automatic hero slideshow, farmer-first natural-language search, service photography, featured scheme data from the API, and English/Hindi/Hinglish UI copy. The visual system deliberately avoids an icon-heavy AI-dashboard look.


## API troubleshooting (fixed build)

If the browser shows `404 Not Found` for saved schemes, applications, or assistant chat, make sure the FastAPI process was started from this exact project's `backend` directory. Check:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/diagnostics` (should report the loaded scheme count)
- `http://127.0.0.1:8000/docs`

The frontend uses the Vite `/api` proxy. If Vite moves from port 5173 to 5174 because 5173 is busy, the fixed backend also allows 5174 for direct development access.

The fixed assistant supports scheme discovery, documents, benefits, application steps, eligibility through the deterministic rule engine, general agriculture knowledge, and follow-up scheme context.
