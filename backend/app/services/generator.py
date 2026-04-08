from __future__ import annotations

import pandas as pd
from app.services.synthesizer import synthesize_questions


def generate_paper(
    frame: pd.DataFrame, 
    subject: str, 
    total_marks: int, 
    questions_count: int, 
    target_years: list[int] | None = None,
    use_ai: bool = False
) -> dict:
    if use_ai:
        # Synthesis Mode: Create new questions based on historical topic importance
        # We find the most frequent topics in the frame for this subject
        subject_frame = frame[frame["subject"].str.lower() == subject.lower()].copy()
        if subject_frame.empty:
             return {"error": f"No historical data for subject: {subject}", "questions": []}
             
        topic_counts = subject_frame["topic"].value_counts().head(5) # Top 5 topics
        important_topics = topic_counts.index.tolist()
        
        # Determine how many questions per topic to generate
        per_topic = max(1, questions_count // len(important_topics))
        
        try:
            ai_questions = synthesize_questions(subject, important_topics, per_topic)
            
            # Trim if AI generated too many
            if len(ai_questions) > questions_count:
                ai_questions = ai_questions[:questions_count]
            
            # Formatting and ID generation
            formatted = []
            current_total = 0
            for i, q in enumerate(ai_questions, start=1):
                m = int(q.get("marks", 5))
                current_total += m
                formatted.append({
                    "question_no": i,
                    "topic": q.get("topic", "General"),
                    "question_text": q.get("question_text", "Explain the core concepts of this topic."),
                    "marks": m,
                    "difficulty": round(float(q.get("difficulty", 0.5)), 2)
                })
            
            # Final marks adjustment
            if current_total != total_marks and formatted:
                 adjustment = total_marks - current_total
                 formatted[-1]["marks"] += adjustment
                 if formatted[-1]["marks"] <= 0: formatted[-1]["marks"] = 1

            return {
                "subject": subject,
                "total_marks": total_marks,
                "questions": formatted,
                "mode": "AI Synthesized"
            }
        except Exception:
            # Fallback to sampling if synthesis totally fails
            pass

    # Default Sampling Mode (or Fallback)
    # Filter by subject and optionally by year
    subject_frame = frame[frame["subject"].str.lower() == subject.lower()].copy()
    if subject_frame.empty:
        return {"error": f"No questions found for subject: {subject}", "questions": []}

    if target_years:
        year_filtered = subject_frame[subject_frame["year"].isin(target_years)]
        if not year_filtered.empty:
            subject_frame = year_filtered

    # Group by topic to ensure variety
    topics = subject_frame["topic"].unique()
    questions_per_topic = max(1, questions_count // len(topics)) if len(topics) > 0 else questions_count
    
    selected_questions = []
    
    # Try to pick a balanced set from each topic
    for topic in topics:
        topic_pool = subject_frame[subject_frame["topic"] == topic]
        sample_size = min(len(topic_pool), questions_per_topic + 1)
        selected_questions.extend(topic_pool.sample(sample_size).to_dict(orient="records"))

    # Trimming/Padding
    if len(selected_questions) > questions_count:
        selected_questions = selected_questions[:questions_count]
    elif len(selected_questions) < questions_count:
        remaining_count = questions_count - len(selected_questions)
        already_selected_texts = [q["question_text"] for q in selected_questions]
        extra_pool = subject_frame[~subject_frame["question_text"].isin(already_selected_texts)]
        if not extra_pool.empty:
            extra_sample = extra_pool.sample(min(len(extra_pool), remaining_count))
            selected_questions.extend(extra_sample.to_dict(orient="records"))

    # Final pass
    current_total = 0
    formatted_questions = []
    for i, q in enumerate(selected_questions, start=1):
        m = int(q["marks"])
        current_total += m
        formatted_questions.append({
            "question_no": i,
            "topic": q["topic"],
            "question_text": q["question_text"],
            "marks": m,
            "difficulty": round(float(q["difficulty"]), 2)
        })

    if current_total != total_marks and formatted_questions:
        adjustment = total_marks - current_total
        formatted_questions[-1]["marks"] += adjustment
        if formatted_questions[-1]["marks"] <= 0:
             formatted_questions[-1]["marks"] = 1

    return {
        "subject": subject,
        "total_marks": total_marks,
        "questions": formatted_questions,
        "mode": "Historical Sampling"
    }