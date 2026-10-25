"""
AI Symptom Checker — implemented as a LangGraph state machine so the model
can ask clarifying follow-up questions before committing to a risk
assessment, instead of a single-shot prompt.

Graph:  collect_symptoms -> ask_followup -> (loop until enough info) -> assess_risk -> END
"""
import json
import logging
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from .llm import get_llm

logger = logging.getLogger('healthcare')

def _extract_text(content):
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

MAX_FOLLOWUPS = 3

SYSTEM_PROMPT = """You are a cautious AI medical triage assistant embedded in a hospital
platform. You are NOT a doctor and must never give a definitive diagnosis.
Given a patient's described symptoms and conversation so far, decide whether you
have enough information to produce a risk assessment, or whether you need to ask
ONE more clarifying follow-up question (duration, severity, associated symptoms,
medical history relevance).

Always respond with STRICT JSON only, no markdown fences, in this shape:
{
  "need_followup": true|false,
  "followup_question": "string or empty",
  "possible_conditions": ["condition1", "condition2"],
  "risk_level": "LOW|MODERATE|HIGH|EMERGENCY",
  "recommendation": "plain language next-step advice, and always advise seeing a doctor for HIGH/EMERGENCY"
}
"""


class SymptomState(TypedDict):
    conversation: List[Dict[str, str]]
    followup_count: int
    result: Dict


def _call_model(state: SymptomState) -> SymptomState:
    llm = get_llm(temperature=0.2)
    convo_text = "\n".join(f"{m['role']}: {m['content']}" for m in state['conversation'])

    if llm is None:
        # Demo-mode fallback when no API key is configured
        state['result'] = {
            'need_followup': False,
            'followup_question': '',
            'possible_conditions': ['Unable to analyze — AI provider not configured'],
            'risk_level': 'MODERATE',
            'recommendation': 'Please consult a doctor directly. AI service is not configured in this demo.',
        }
        return state

    try:
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Conversation so far:\n{convo_text}\n\nRespond with JSON only."),
        ])
        raw = _extract_text(response.content).strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        state['result'] = json.loads(raw)
    except Exception as e:
        logger.error(f'Symptom checker LLM call failed: {e}')
        state['result'] = {
            'need_followup': False,
            'followup_question': '',
            'possible_conditions': [],
            'risk_level': 'MODERATE',
            'recommendation': 'Something went wrong analyzing your symptoms. Please consult a doctor.',
        }
    return state


def _route(state: SymptomState) -> str:
    result = state['result']
    if result.get('need_followup') and state['followup_count'] < MAX_FOLLOWUPS:
        return 'ask_followup'
    return 'finalize'


def _ask_followup(state: SymptomState) -> SymptomState:
    state['followup_count'] += 1
    return state


def build_symptom_checker_graph():
    graph = StateGraph(SymptomState)
    graph.add_node('analyze', _call_model)
    graph.add_node('ask_followup', _ask_followup)
    graph.set_entry_point('analyze')
    graph.add_conditional_edges('analyze', _route, {'ask_followup': 'ask_followup', 'finalize': END})
    graph.add_edge('ask_followup', END)  # return control to caller; next turn re-enters graph
    return graph.compile()


_GRAPH = None


def run_symptom_check_turn(conversation_history, followup_count=0):
    """
    Runs a single turn of the symptom-checker graph. The Django view is
    responsible for persisting `conversation_history` between turns and
    calling this again when the patient answers a follow-up question.
    """
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_symptom_checker_graph()

    state: SymptomState = {
        'conversation': conversation_history,
        'followup_count': followup_count,
        'result': {},
    }
    final_state = _GRAPH.invoke(state)
    return final_state['result'], final_state['followup_count']
