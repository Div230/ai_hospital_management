"""
Central LLM client factory. Primary = Gemini, fallback = Groq.
Gemini 503/timeout pe automatic Groq. Groq ka model name env var
GROQ_MODEL se aata hai, taaki model hat jaye to code change na karna pade.
"""
import logging
from decouple import config
from django.conf import settings

logger = logging.getLogger('healthcare')

GROQ_MODEL = config('GROQ_MODEL', default='openai/gpt-oss-20b')


def _build_gemini(temperature):
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model='gemini-flash-latest',
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
        timeout=12,
        max_retries=1,
    )


def _build_groq(temperature):
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=GROQ_MODEL,
        groq_api_key=settings.GROQ_API_KEY,
        temperature=temperature,
        timeout=20,
        max_retries=1,
    )


def get_llm(temperature=0.3):
    if not settings.EXTERNAL_AI_ENABLED:
        return None
    gemini = None
    groq = None

    if settings.GEMINI_API_KEY:
        try:
            gemini = _build_gemini(temperature)
        except Exception as e:
            logger.warning(f'Gemini init failed: {e}')

    if settings.GROQ_API_KEY:
        try:
            groq = _build_groq(temperature)
        except Exception as e:
            logger.warning(f'Groq init failed: {e}')

    if gemini and groq:
        return gemini.with_fallbacks([groq])
    return gemini or groq
