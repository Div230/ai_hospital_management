"""
LangChain chains for the single-shot AI features: diet/exercise/lifestyle
recommendations, medicine explanation, clinical note structuring, and
medical report analysis. Kept as small composable chains rather than one
mega-prompt, matching the modular-app philosophy of the rest of the project.
"""
import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from .llm import get_llm

logger = logging.getLogger('healthcare')

def _extract_text(content):
    """
    LangChain's Gemini wrapper sometimes returns response.content as a
    plain string, and sometimes as a list of content parts (e.g. when the
    model uses tool-calling internally). This normalizes both cases to a
    single string so downstream .strip()/.replace() calls don't crash.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get('text', ''))
        return ''.join(parts)
    return str(content)


def _safe_json_invoke(system_prompt, user_prompt, fallback):
    llm = get_llm(temperature=0.4)
    if llm is None:
        return fallback
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        raw = _extract_text(response.content).strip().replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except Exception as e:
        logger.error(f'AI chain call failed: {e}')
        return fallback


def generate_diet_recommendation(patient_profile: dict):
    system = (
        "You are a clinical nutrition assistant. Given a patient profile "
        "(age, weight, height, conditions, allergies), suggest a general diet "
        "plan. Respond as JSON: {\"summary\": str, \"foods_to_eat\": [str], "
        "\"foods_to_avoid\": [str], \"disclaimer\": str}. Always include a "
        "disclaimer to consult a dietitian for medical conditions."
    )
    return _safe_json_invoke(
        system, json.dumps(patient_profile),
        {'summary': 'AI service unavailable in demo mode.', 'foods_to_eat': [], 'foods_to_avoid': [],
         'disclaimer': 'Please consult a registered dietitian.'}
    )


def generate_exercise_recommendation(patient_profile: dict):
    system = (
        "You are a fitness advisor. Given a patient profile, suggest a safe "
        "general exercise routine. Respond as JSON: {\"summary\": str, "
        "\"recommended_activities\": [str], \"precautions\": [str], \"disclaimer\": str}."
    )
    return _safe_json_invoke(
        system, json.dumps(patient_profile),
        {'summary': 'AI service unavailable in demo mode.', 'recommended_activities': [],
         'precautions': [], 'disclaimer': 'Please consult your doctor before starting any exercise plan.'}
    )


def generate_lifestyle_suggestions(patient_profile: dict):
    system = (
        "You are a preventive-health lifestyle advisor. Respond as JSON: "
        "{\"summary\": str, \"suggestions\": [str], \"disclaimer\": str}."
    )
    return _safe_json_invoke(
        system, json.dumps(patient_profile),
        {'summary': 'AI service unavailable in demo mode.', 'suggestions': [],
         'disclaimer': 'General guidance only, not a substitute for medical advice.'}
    )


def explain_medicine(medicine_name: str, dosage: str = ''):
    system = (
        "You explain medicines in simple language for patients. Respond as JSON: "
        "{\"what_it_is\": str, \"common_uses\": str, \"how_to_take\": str, "
        "\"common_side_effects\": [str], \"disclaimer\": str}."
    )
    return _safe_json_invoke(
        system, f'Medicine: {medicine_name}, Dosage: {dosage}',
        {'what_it_is': 'AI service unavailable in demo mode.', 'common_uses': '', 'how_to_take': '',
         'common_side_effects': [], 'disclaimer': 'Consult your doctor or pharmacist.'}
    )


def structure_clinical_note(raw_dictation: str):
    system = (
        "You convert a doctor's free-text consultation notes into a structured "
        "clinical note. Respond as JSON: {\"chief_complaint\": str, \"observations\": str, "
        "\"diagnosis\": str, \"summary\": str}."
    )
    return _safe_json_invoke(
        system, raw_dictation,
        {'chief_complaint': '', 'observations': raw_dictation, 'diagnosis': '',
         'summary': 'AI structuring unavailable in demo mode — raw text preserved.'}
    )


def analyze_medical_report(ocr_text: str, report_type: str):
    system = (
        "You are a medical report analyzer. Given OCR-extracted text from a "
        f"{report_type} report, extract structured findings. Respond as JSON: "
        "{\"summary\": str, \"parameters\": [{\"name\": str, \"value\": str, "
        "\"unit\": str, \"normal_range\": str, \"flag\": \"NORMAL|LOW|HIGH\"}], "
        "\"abnormal_findings\": [str], \"disclaimer\": str}. If the text is not "
        "a recognizable medical report, say so in summary."
    )
    return _safe_json_invoke(
        system, ocr_text[:6000],
        {'summary': 'AI service unavailable in demo mode.', 'parameters': [],
         'abnormal_findings': [], 'disclaimer': 'This is not a medical diagnosis. Consult your doctor.'}
    )


def compute_ai_health_score(patient_profile: dict, recent_reports_summary: list):
    system = (
        "You compute a general wellness score (0-100, higher is better) from "
        "a patient's profile and recent report summaries. Respond as JSON: "
        "{\"score\": int, \"risk_flags\": [str], \"reasoning\": str}."
    )
    payload = {'profile': patient_profile, 'recent_reports': recent_reports_summary}
    return _safe_json_invoke(
        system, json.dumps(payload),
        {'score': None, 'risk_flags': [], 'reasoning': 'AI service unavailable in demo mode — no score calculated.'}
    )


def general_health_chat_reply(conversation_history: list):
    """Free-form conversational health assistant (distinct from the
    structured multi-turn Symptom Checker). Answers general wellness
    questions, explains conditions in plain language, etc."""
    system = (
        "You are a friendly AI health assistant embedded in a hospital platform. "
        "Answer the patient's general health/wellness questions in plain, warm "
        "language. You are NOT a replacement for a doctor — for anything symptom-"
        "specific or urgent, gently suggest using the Symptom Checker or booking "
        "a doctor. Keep replies concise (3-5 sentences)."
    )
    llm = get_llm(temperature=0.5)
    if llm is None:
        return "AI service isn't configured in this demo. Please consult your doctor for personalized advice."
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        history_text = "\n".join(f"{m['role']}: {m['content']}" for m in conversation_history)
        response = llm.invoke([SystemMessage(content=system), HumanMessage(content=history_text)])
        return _extract_text(response.content).strip()
    except Exception as e:
        logger.error(f'General health chat failed: {e}')
        return "Something went wrong answering that. Please try again or consult your doctor."


def predict_disease_risk(patient_profile: dict, recent_reports_summary: list):
    """Estimates risk percentages for a handful of common conditions based on
    profile + recent report findings. Distinct from the AI Health Score:
    this is condition-specific rather than a single aggregate number."""
    system = (
        "You are a preventive-health risk estimator. Given a patient profile and "
        "recent report summaries, estimate risk for up to 4 relevant conditions "
        "(e.g. Type 2 Diabetes, Hypertension, Cardiovascular Disease, based on "
        "what's actually relevant to this profile). Respond as JSON: "
        "{\"predictions\": [{\"condition_name\": str, \"risk_percentage\": float, "
        "\"contributing_factors\": [str], \"recommendation\": str}], \"disclaimer\": str}. "
        "Be conservative — this is a screening aid, not a diagnosis."
    )
    payload = {'profile': patient_profile, 'recent_reports': recent_reports_summary}
    return _safe_json_invoke(
        system, json.dumps(payload),
        {'predictions': [], 'disclaimer': 'AI service unavailable in demo mode.'}
    )
