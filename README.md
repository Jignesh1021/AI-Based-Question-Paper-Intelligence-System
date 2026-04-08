# AI-Based Question Paper Intelligence System

An end-to-end analytics and paper-generation platform for teachers. The project combines FastAPI, pandas, scikit-learn, SQLite, and a React dashboard to:

- analyze past question papers
- predict important topics
- score difficulty trends
- surface expected questions
- generate smart question papers
- export Power BI-ready trend data

## Project Structure

- `backend/` FastAPI app, ML pipeline, SQL persistence, and analytics endpoints
- `frontend/` React teacher dashboard
- `.github/copilot-instructions.md` workspace guidance

## Backend Features

- topic frequency analysis
- heatmap-ready analytics by topic and year
- topic prediction with TF-IDF + logistic regression
- question difficulty scoring
- expected question ranking
- paper generation with topic and difficulty balance

## Frontend Features

- analytics summary cards
- topic heatmap view
- most expected questions list
- generated paper preview
- trend export status

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /health`
- `POST /analyze/papers`
- `GET /analytics/topic-frequency`
- `POST /predict/topic`
- `POST /predict/difficulty`
- `GET /questions/expected`
- `POST /papers/generate`
- `GET /export/powerbi`

## Notes

- SQLite is used by default so the project runs locally without extra setup.
- Sample historical question paper data is included in `backend/app/data/sample_papers.csv`.
- The frontend expects the backend at `http://localhost:8000`.