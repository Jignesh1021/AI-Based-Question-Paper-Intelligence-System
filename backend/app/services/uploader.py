from __future__ import annotations

import io
from typing import List

import pandas as pd
from sqlalchemy.orm import Session

from app.db.models import QuestionPaperRecord
from app.schemas import QuestionPaperCreate


def process_csv_upload(file_content: bytes, db: Session) -> List[dict]:
    """
    Process a CSV file content, validate schema, and store records in the DB.
    Expected columns: year, subject, topic, question_text, marks, difficulty
    """
    df = pd.read_csv(io.BytesIO(file_content))
    
    # Basic validation
    required_cols = {"year", "subject", "topic", "question_text", "marks", "difficulty"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"CSV missing required columns: {missing}")

    records = []
    for _, row in df.iterrows():
        record = QuestionPaperRecord(
            year=int(row["year"]),
            subject=str(row["subject"]),
            topic=str(row["topic"]),
            question_text=str(row["question_text"]),
            marks=int(row["marks"]),
            difficulty=float(row["difficulty"])
        )
        db.add(record)
        records.append({
            "year": record.year,
            "subject": record.subject,
            "topic": record.topic,
            "question_text": record.question_text,
            "marks": record.marks,
            "difficulty": record.difficulty
        })
    
    db.commit()
    return records
