from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import Base, engine, get_db
from app.db.models import QuestionPaperRecord
from app.schemas import DifficultyPredictionRequest, GeneratePaperRequest, QuestionPaperCreate, TopicPredictionRequest
from app.services.analytics import build_analytics
from app.services.exporter import export_powerbi_data
from app.services.generator import generate_paper
from app.services.pipeline import expected_questions, load_models, predict_difficulty, predict_topic, retrain_models
from app.services.uploader import process_csv_upload
from app.services.pdf_exporter import generate_paper_pdf
from fastapi.responses import Response


app = FastAPI(title="AI-Based Question Paper Intelligence System", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
# Global model bundle
bundle = load_models()


def frame_from_db(db: Session) -> pd.DataFrame:
    rows = db.query(QuestionPaperRecord).all()
    return pd.DataFrame(
        [
            {
                "year": row.year,
                "subject": row.subject,
                "topic": row.topic,
                "question_text": row.question_text,
                "marks": row.marks,
                "difficulty": row.difficulty,
            }
            for row in rows
        ]
    )


def combined_frame(db: Session) -> pd.DataFrame:
    global bundle
    db_frame = frame_from_db(db)
    if db_frame.empty:
        return bundle.frame.copy()
    return pd.concat([bundle.frame, db_frame], ignore_index=True)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "bundle_records": len(bundle.frame)}


@app.get("/metadata/subjects")
def get_subjects(db: Session = Depends(get_db)) -> dict:
    frame = combined_frame(db)
    subjects = sorted(frame["subject"].unique().tolist())
    return {"subjects": subjects}


@app.post("/analyze/papers")
def analyze_papers(records: list[QuestionPaperCreate], db: Session = Depends(get_db)) -> dict:
    global bundle
    stored = []
    for record in records:
        item = QuestionPaperRecord(**record.model_dump())
        db.add(item)
        stored.append(record.model_dump())
    db.commit()

    # Retrain after adding new records
    bundle = retrain_models(frame_from_db(db))
    
    analytics = build_analytics(combined_frame(db))
    return analytics.__dict__


@app.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    global bundle
    try:
        content = await file.read()
        records = process_csv_upload(content, db)
        
        # Trigger retraining
        bundle = retrain_models(frame_from_db(db))
        
        return {"status": "success", "inserted": len(records)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/analytics/topic-frequency")
def topic_frequency(db: Session = Depends(get_db)) -> dict:
    frame = combined_frame(db)
    analytics = build_analytics(frame)
    return {"topic_frequency": analytics.topic_frequency, "yearly_heatmap": analytics.yearly_heatmap}


@app.post("/predict/topic")
def predict_topic_endpoint(payload: TopicPredictionRequest) -> dict:
    return predict_topic(bundle, payload.question_text)


@app.post("/predict/difficulty")
def predict_difficulty_endpoint(payload: DifficultyPredictionRequest) -> dict:
    return predict_difficulty(bundle, payload.question_text, payload.marks)


@app.get("/questions/expected")
def questions_expected(subject: str, limit: int = 8, db: Session = Depends(get_db)) -> dict:
    frame = combined_frame(db)
    # We pass a temporary bundle or just the frame
    temp_bundle = bundle.__class__(topic_model=bundle.topic_model, difficulty_model=bundle.difficulty_model, frame=frame)
    return {"subject": subject, "expected_questions": expected_questions(temp_bundle, subject, limit)}


@app.post("/papers/generate")
def generate_paper_endpoint(payload: GeneratePaperRequest, db: Session = Depends(get_db)) -> dict:
    frame = combined_frame(db)
    return generate_paper(frame, payload.subject, payload.total_marks, payload.questions, use_ai=payload.use_ai)


@app.post("/papers/download")
def download_paper(payload: GeneratePaperRequest, db: Session = Depends(get_db)):
    frame = combined_frame(db)
    paper_data = generate_paper(frame, payload.subject, payload.total_marks, payload.questions, use_ai=payload.use_ai)
    
    if "error" in paper_data:
        raise HTTPException(status_code=404, detail=paper_data["error"])
        
    pdf_bytes = generate_paper_pdf(paper_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={payload.subject}_paper.pdf"
        }
    )


@app.get("/export/powerbi")
def export_powerbi(db: Session = Depends(get_db)) -> dict:
    frame = combined_frame(db)
    output_path = Path(__file__).resolve().parent / "data" / "powerbi_export.csv"
    path = export_powerbi_data(frame, output_path)
    return {"file_path": path}


@app.post("/seed")
def seed_records(records: list[QuestionPaperCreate], db: Session = Depends(get_db)) -> dict:
    global bundle
    for record in records:
        db.add(QuestionPaperRecord(**record.model_dump()))
    db.commit()
    
    bundle = retrain_models(frame_from_db(db))
    return {"inserted": len(records)}