from sqlalchemy import Column, Float, Integer, String, Text

from app.db.database import Base


class QuestionPaperRecord(Base):
    __tablename__ = "question_papers"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    subject = Column(String(120), nullable=False)
    topic = Column(String(120), nullable=False)
    question_text = Column(Text, nullable=False)
    marks = Column(Integer, nullable=False)
    difficulty = Column(Float, nullable=False)