"""Evidence-only label extraction. No drug dictionary or dosage inference."""
import re

FIELD_LABELS = {
    'doctor_name': r'(?:doctor|prescriber)',
    'clinic_name': r'(?:clinic|hospital)',
    'prescription_date': r'(?:prescription date|date)',
    'patient_name': r'(?:patient|patient name)',
    'medication_name': r'(?:medicine|medication|drug)',
    'strength': r'(?:strength)',
    'dosage': r'(?:dosage|dose)',
    'frequency': r'(?:frequency)',
    'duration': r'(?:duration)',
    'route': r'(?:route)',
    'instructions': r'(?:instructions)',
    'tests_requested': r'(?:tests|tests requested)',
    'follow_up': r'(?:follow up|follow-up)',
}
UNREADABLE = re.compile(r'\?|\[(?:unreadable|illegible|uncertain)\]|\b(?:unreadable|illegible)\b', re.I)
SAFETY_NOTICE = ('Machine transcription is unverified and may contain errors. This tool does not prescribe, '
                 'validate medication safety, or fill in missing instructions. Consult the original prescription '
                 'and a licensed clinician or pharmacist before acting on any extracted text.')


def extract_fields(pages):
    fields = []
    for key, labels in FIELD_LABELS.items():
        matches = []
        for page in pages:
            for match in re.finditer(r'^[ \t]*' + labels + r'[ \t]*:[ \t]*([^\n]*)', page['text'], re.I | re.M):
                evidence = match.group(1).strip()
                unreadable = not evidence or bool(UNREADABLE.search(evidence))
                matches.append({'field': key, 'value': None if unreadable else evidence,
                                'status': 'unreadable' if unreadable else 'uncertain',
                                'evidence': evidence, 'page': page['page']})
        fields.extend(matches or [{'field': key, 'value': None, 'status': 'not_present', 'evidence': '', 'page': None}])
    return fields


def build_result(pages, provider, latency_ms):
    text = '\n\n'.join(f"[Page {page['page']}]\n{page['text']}" for page in pages)
    readable = any(page['text'].strip() for page in pages)
    return {'transcription': text if readable else '', 'pages': pages, 'fields': extract_fields(pages),
            'readability': 'uncertain' if readable else 'unreadable', 'provider': provider,
            'latency_ms': round(latency_ms), 'confidence_calibrated': False,
            'notice': SAFETY_NOTICE, 'human_review_recommended': True}
