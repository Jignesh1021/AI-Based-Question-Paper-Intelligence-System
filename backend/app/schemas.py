from pydantic import BaseModel, Field


class QuestionPaperCreate(BaseModel):
    year: int
    subject: str
    topic: str
    question_text: str
    marks: int = Field(ge=1, le=100)
    difficulty: float = Field(ge=0.0, le=1.0)


class TopicPredictionRequest(BaseModel):
    question_text: str


class DifficultyPredictionRequest(BaseModel):
    question_text: str
    marks: int = Field(ge=1, le=100)


class GeneratePaperRequest(BaseModel):
    subject: str
    total_marks: int = 100
    questions: int = 10
    target_years: list[int] | None = None
    use_ai: bool = False