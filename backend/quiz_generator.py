import json
import re
from typing import Dict, List
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import os

logger = logging.getLogger(__name__)

# Initialize Gemini LLM
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7
)

# ============ PROMPT TEMPLATES ============

QUIZ_GENERATION_PROMPT = PromptTemplate(
    input_variables=["content", "num_questions"],
    template="""You are an expert educator. Based on the following Wikipedia article content, generate a JSON array of {num_questions} quiz questions.

ARTICLE CONTENT:
{content}

IMPORTANT REQUIREMENTS:
1. Generate questions ONLY from facts explicitly stated in the article
2. Avoid hallucinations - do not invent information
3. Include questions of varying difficulty: mix of easy, medium, and hard
4. Provide 4 plausible options (A, B, C, D) where only ONE is correct
5. For each question, provide a brief explanation citing the relevant section
6. Ensure questions test comprehension, not just memorization

Return ONLY a valid JSON array with this exact structure (no markdown, no extra text):
[
  {{
    "question": "Question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Correct option text",
    "difficulty": "easy|medium|hard",
    "explanation": "Why this answer is correct with section reference"
  }}
]

Generate the questions now:"""
)

RELATED_TOPICS_PROMPT = PromptTemplate(
    input_variables=["content", "title"],
    template="""Based on this Wikipedia article about "{title}", identify 5-7 related Wikipedia topics that a reader should explore for deeper understanding.

ARTICLE CONTENT:
{content}

Requirements:
1. Topics should be closely related to the article's subject matter
2. They should help understand the context, history, or applications
3. Return ONLY a JSON array of topic names as strings
4. Topics should be real Wikipedia articles (no fictional topics)

Return ONLY a valid JSON array like this (no markdown, no extra text):
["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"]

Generate the topics now:"""
)

# ============ MAIN FUNCTIONS ============

def generate_quiz_with_llm(content: str, title: str, sections: List[str], num_questions: int = 7) -> Dict:
    """
    Generate quiz questions and related topics using Gemini LLM.
    
    Args:
        content: Full article content from scraper
        title: Article title
        sections: List of section titles
        num_questions: Number of questions to generate (5-10)
    
    Returns:
        Dictionary with quiz questions and related topics
    """
    try:
        # Validate number of questions
        num_questions = max(5, min(10, num_questions))
        
        logger.info(f"Generating {num_questions} quiz questions for: {title}")
        
        # Generate quiz questions
        quiz_questions = generate_quiz_questions(content, num_questions)
        
        # Generate related topics
        related_topics = generate_related_topics(content, title)
        
        logger.info(f"Successfully generated quiz for: {title}")
        
        return {
            "quiz": quiz_questions,
            "related_topics": related_topics
        }
    
    except Exception as e:
        logger.error(f"Error in quiz generation: {str(e)}")
        # Return fallback quiz to prevent complete failure
        return {
            "quiz": generate_fallback_quiz(),
            "related_topics": ["General Knowledge", "Further Reading"]
        }

def generate_quiz_questions(content: str, num_questions: int) -> List[Dict]:
    """
    Use Gemini LLM to generate quiz questions from article content.
    Prompt is grounded to minimize hallucination.
    """
    try:
        # Truncate content to reasonable length for API
        max_length = 8000
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        # Create prompt
        prompt = QUIZ_GENERATION_PROMPT.format(
            content=content,
            num_questions=num_questions
        )
        
        # Call LLM
        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        # Parse JSON response
        quiz_questions = parse_json_safely(response_text)
        
        # Validate and clean questions
        validated_questions = validate_quiz_questions(quiz_questions)
        
        # Ensure we have enough questions
        while len(validated_questions) < num_questions and len(validated_questions) < 10:
            logger.warning(f"Generated only {len(validated_questions)} questions, attempting regeneration...")
            validated_questions.extend(generate_fallback_quiz()[:num_questions - len(validated_questions)])
        
        return validated_questions[:num_questions]
    
    except Exception as e:
        logger.error(f"Error generating quiz questions: {str(e)}")
        return generate_fallback_quiz()

def generate_related_topics(content: str, title: str) -> List[str]:
    """
    Use Gemini LLM to suggest related Wikipedia topics.
    """
    try:
        # Truncate content
        max_length = 5000
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        # Create prompt
        prompt = RELATED_TOPICS_PROMPT.format(
            title=title,
            content=content
        )
        
        # Call LLM
        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        # Parse JSON response
        topics = parse_json_safely(response_text)
        
        # Validate topics
        if isinstance(topics, list) and all(isinstance(t, str) for t in topics):
            return [t.strip() for t in topics if t.strip()][:7]
        
        return ["Further Reading", "Related Articles"]
    
    except Exception as e:
        logger.error(f"Error generating related topics: {str(e)}")
        return ["Further Reading", "Related Articles"]

# ============ HELPER FUNCTIONS ============

def parse_json_safely(text: str):
    """
    Safely parse JSON from LLM response, handling common formatting issues.
    """
    try:
        # Remove markdown code blocks if present
        text = re.sub(r'```json\n?', '', text)
        text = re.sub(r'```\n?', '', text)
        text = text.strip()
        
        # Attempt to parse
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        logger.debug(f"Failed to parse: {text[:200]}")
        return []

def validate_quiz_questions(questions: List[Dict]) -> List[Dict]:
    """
    Validate quiz questions structure and content.
    """
    validated = []
    
    for q in questions:
        if not isinstance(q, dict):
            continue
        
        # Check required fields
        if not all(k in q for k in ["question", "options", "answer", "explanation"]):
            logger.warning(f"Skipping malformed question: {q}")
            continue
        
        # Validate structure
        if not isinstance(q["options"], list) or len(q["options"]) != 4:
            logger.warning(f"Invalid options for question: {q['question']}")
            continue
        
        if q["answer"] not in q["options"]:
            logger.warning(f"Answer not in options for: {q['question']}")
            continue
        
        # Set default difficulty if missing
        difficulty = q.get("difficulty", "medium")
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "medium"
        
        # Clean and add to validated list
        validated.append({
            "question": str(q["question"]).strip(),
            "options": [str(opt).strip() for opt in q["options"]],
            "answer": str(q["answer"]).strip(),
            "difficulty": difficulty,
            "explanation": str(q.get("explanation", "")).strip()
        })
    
    return validated

def generate_fallback_quiz() -> List[Dict]:
    """
    Fallback quiz if LLM generation fails.
    This ensures system doesn't completely fail.
    """
    return [
        {
            "question": "What is the primary subject of this article?",
            "options": ["History", "Science", "Biography", "Technology"],
            "answer": "Biography",
            "difficulty": "easy",
            "explanation": "This is a default fallback question. Please regenerate."
        }
    ]