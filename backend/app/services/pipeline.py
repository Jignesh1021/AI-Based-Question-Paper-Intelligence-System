from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_papers.csv"
MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "question_model.joblib"


@dataclass
class ModelBundle:
    topic_model: Pipeline
    difficulty_model: Pipeline
    frame: pd.DataFrame


def load_frame() -> pd.DataFrame:
    frame = pd.read_csv(DATA_PATH)
    frame["difficulty"] = frame["difficulty"].astype(float)
    return frame


def train_models(frame: pd.DataFrame) -> ModelBundle:
    if frame.empty:
        # Fallback if frame is empty
        frame = pd.DataFrame(columns=["year", "subject", "topic", "question_text", "marks", "difficulty"])
        
    topic_model = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    
    # Ensure labels are strings for topic prediction
    frame["topic"] = frame["topic"].astype(str)
    topic_model.fit(frame["question_text"], frame["topic"])

    difficulty_features = ColumnTransformer(
        [
            ("text", TfidfVectorizer(stop_words="english", max_features=500), "question_text"),
        ],
        remainder="passthrough",
    )
    difficulty_model = Pipeline(
        [
            ("features", difficulty_features),
            ("regressor", RandomForestRegressor(n_estimators=200, random_state=42)),
        ]
    )
    difficulty_model.fit(frame[["question_text", "marks"]], frame["difficulty"])

    bundle = ModelBundle(topic_model=topic_model, difficulty_model=difficulty_model, frame=frame)
    joblib.dump(bundle, MODEL_PATH)
    return bundle


def load_models() -> ModelBundle:
    if MODEL_PATH.exists():
        try:
            bundle = joblib.load(MODEL_PATH)
            if isinstance(bundle, ModelBundle):
                return bundle
        except Exception:
            pass
    
    frame = load_frame()
    return train_models(frame)


def retrain_models(db_records: pd.DataFrame) -> ModelBundle:
    """Retrain models using a combination of base CSV data and new DB records."""
    base_frame = load_frame()
    if db_records.empty:
        combined = base_frame
    else:
        combined = pd.concat([base_frame, db_records], ignore_index=True)
    
    return train_models(combined)


def predict_topic(bundle: ModelBundle, question_text: str) -> dict:
    probabilities = bundle.topic_model.predict_proba([question_text])[0]
    classes = bundle.topic_model.classes_
    ranking = sorted(
        (
            {"topic": topic, "score": round(float(score), 3)}
            for topic, score in zip(classes, probabilities)
        ),
        key=lambda item: item["score"],
        reverse=True,
    )
    return {"predicted_topic": ranking[0]["topic"], "ranking": ranking[:5]}


def predict_difficulty(bundle: ModelBundle, question_text: str, marks: int) -> dict:
    df_input = pd.DataFrame([{"question_text": question_text, "marks": marks}])
    score = float(bundle.difficulty_model.predict(df_input)[0])
    return {"difficulty_score": round(max(0.0, min(score, 1.0)), 2)}


def expected_questions(bundle: ModelBundle, subject: str, limit: int = 8) -> list[dict]:
    filtered = bundle.frame[bundle.frame["subject"].str.lower() == subject.lower()]
    ranked = (
        filtered.groupby(["topic", "question_text", "marks"])
        .agg(avg_difficulty=("difficulty", "mean"), count=("question_text", "size"))
        .reset_index()
        .sort_values(["count", "avg_difficulty"], ascending=[False, False])
        .head(limit)
    )
    return [
        {
            "topic": row.topic,
            "question_text": row.question_text,
            "marks": int(row.marks),
            "expected_score": round(float(row.count + row.avg_difficulty), 2),
        }
        for row in ranked.itertuples(index=False)
    ]