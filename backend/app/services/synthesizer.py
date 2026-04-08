from __future__ import annotations

import json
import logging
import random
from typing import List

import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini if key is provided
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

def synthesize_questions(subject: str, topics: List[str], count_per_topic: int = 2) -> List[dict]:
    """
    Synthesize new questions using Generative AI.
    Falls back to a pattern-based generator if API key is missing.
    """
    if settings.gemini_api_key:
        try:
            return _call_gemini_synthesis(subject, topics, count_per_topic)
        except Exception as e:
            logger.error(f"Gemini Synthesis failed: {e}")
            return _fallback_synthesis(subject, topics, count_per_topic)
    else:
        return _fallback_synthesis(subject, topics, count_per_topic)

def _call_gemini_synthesis(subject: str, topics: List[str], count_per_topic: int) -> List[dict]:
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert examiner in {subject}.
    Generate {count_per_topic} high-quality, unique exam questions for each of the following topics:
    {", ".join(topics)}

    Requirements:
    - Questions must be professional and realistic.
    - Vary the difficulty between 0.2 (easy) and 0.9 (hard).
    - Vary the marks between 2 and 15.
    - Output format: JSON list of objects with keys: topic, question_text, marks, difficulty.

    Return ONLY the valid JSON list.
    """
    
    response = model.generate_content(prompt)
    try:
        # Extract JSON from potential markdown blocks
        clean_text = response.text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
             clean_text = clean_text.split("```")[1].split("```")[0].strip()
             
        data = json.loads(clean_text)
        return data
    except Exception as e:
        logger.error(f"Failed to parse Gemini response: {e}")
        raise e

def _fallback_synthesis(subject: str, topics: List[str], count_per_topic: int) -> List[dict]:
    """
    A smart template-based generator to avoid "dump" content when AI is offline.
    """
    prefixes = [
        "Explain the concept of {topic} in the context of {subject}.",
        "Compare and contrast different approaches to {topic}.",
        "Describe the practical applications of {topic} in real-world scenarios.",
        "Solve a complex problem involving {topic} principles.",
        "Analyze the impact of {topic} on the evolution of {subject}."
    ]
    
    synthesized = []
    for topic in topics:
        for _ in range(count_per_topic):
            template = random.choice(prefixes)
            synthesized.append({
                "topic": topic,
                "question_text": template.format(topic=topic, subject=subject),
                "marks": random.choice([5, 8, 10, 15]),
                "difficulty": round(random.uniform(0.3, 0.8), 2)
            })
    return synthesized
