# Running the Project

## Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> Copy `.env.example` to `.env` and fill in your API keys before starting.

Backend runs at **http://localhost:8000**

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**

---

> Make sure the backend is running before using the frontend. API requests are proxied automatically — no CORS configuration needed.
