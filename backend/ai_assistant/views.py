import logging
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from core.permissions import IsPatient
from patients.models import Patient
from .models import SymptomCheckSession, AIRecommendation, AIHealthAssistantMessage, DiseaseRiskPrediction
from .serializers import (
    SymptomCheckSessionSerializer, SymptomCheckStartSerializer,
    SymptomCheckReplySerializer, AIRecommendationSerializer,
    AIHealthAssistantMessageSerializer, DiseaseRiskPredictionSerializer,
)
from .services.symptom_checker import run_symptom_check_turn
from .services import chains

class ConfiguredAIView(APIView):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method == 'POST':
            from .services.llm import get_llm
            from rest_framework.exceptions import APIException, PermissionDenied
            if get_llm() is None:
                error = APIException('AI service is unavailable or disabled by the operator.')
                error.status_code = 503
                raise error
            if request.headers.get('X-AI-Consent') != 'true':
                raise PermissionDenied('Explicit consent is required before sending health data to an external AI provider.')


logger = logging.getLogger('healthcare')


def _get_patient(request):
    patient, _ = Patient.objects.get_or_create(user=request.user)
    return patient


class SymptomCheckStartView(ConfiguredAIView):
    """POST { initial_complaint } -> creates a session and runs the first AI turn."""
    permission_classes = [IsPatient]

    def post(self, request):
        serializer = SymptomCheckStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        complaint = serializer.validated_data['initial_complaint']

        patient = _get_patient(request)
        conversation = [{'role': 'user', 'content': complaint}]
        result, followup_count = run_symptom_check_turn(conversation, followup_count=0)

        session = SymptomCheckSession.objects.create(
            patient=patient,
            initial_complaint=complaint,
            conversation_history=conversation + [{'role': 'assistant', 'content': result}],
            possible_conditions=result.get('possible_conditions', []),
            risk_level=result.get('risk_level', ''),
            recommendation=result.get('recommendation', ''),
            status='ACTIVE' if result.get('need_followup') else 'COMPLETED',
        )
        return Response(
            {'success': True, 'session_id': session.id, 'result': result},
            status=status.HTTP_201_CREATED,
        )


class SymptomCheckReplyView(ConfiguredAIView):
    """POST { session_id, message } -> continues an existing session with the patient's answer."""
    permission_classes = [IsPatient]

    def post(self, request):
        serializer = SymptomCheckReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data['session_id']
        message = serializer.validated_data['message']

        patient = _get_patient(request)
        try:
            session = SymptomCheckSession.objects.get(id=session_id, patient=patient)
        except SymptomCheckSession.DoesNotExist:
            return Response({'success': False, 'message': 'Session not found.'}, status=404)

        conversation = session.conversation_history + [{'role': 'user', 'content': message}]
        followup_count = sum(1 for m in conversation if m['role'] == 'user') - 1
        result, followup_count = run_symptom_check_turn(conversation, followup_count=followup_count)

        session.conversation_history = conversation + [{'role': 'assistant', 'content': result}]
        session.possible_conditions = result.get('possible_conditions', [])
        session.risk_level = result.get('risk_level', '')
        session.recommendation = result.get('recommendation', '')
        session.status = 'ACTIVE' if result.get('need_followup') else 'COMPLETED'
        session.save()

        return Response({'success': True, 'session_id': session.id, 'result': result})


class MySymptomSessionsView(generics.ListAPIView):
    serializer_class = SymptomCheckSessionSerializer
    permission_classes = [IsPatient]

    def get_queryset(self):
        return SymptomCheckSession.objects.filter(patient__user=self.request.user)


class DietRecommendationView(ConfiguredAIView):
    permission_classes = [IsPatient]

    def post(self, request):
        patient = _get_patient(request)
        profile = {
            'date_of_birth': str(patient.date_of_birth) if patient.date_of_birth else None,
            'gender': patient.gender,
            'weight_kg': str(patient.weight_kg) if patient.weight_kg else None,
            'height_cm': str(patient.height_cm) if patient.height_cm else None,
            'allergies': patient.allergies,
            'chronic_conditions': patient.chronic_conditions,
        }
        result = chains.generate_diet_recommendation(profile)
        rec = AIRecommendation.objects.create(patient=patient, category='DIET', content=result)
        return Response({'success': True, 'data': AIRecommendationSerializer(rec).data})


class ExerciseRecommendationView(ConfiguredAIView):
    permission_classes = [IsPatient]

    def post(self, request):
        patient = _get_patient(request)
        profile = {
            'age': str(patient.date_of_birth) if patient.date_of_birth else None,
            'gender': patient.gender,
            'weight_kg': str(patient.weight_kg) if patient.weight_kg else None,
            'chronic_conditions': patient.chronic_conditions,
        }
        result = chains.generate_exercise_recommendation(profile)
        rec = AIRecommendation.objects.create(patient=patient, category='EXERCISE', content=result)
        return Response({'success': True, 'data': AIRecommendationSerializer(rec).data})


class LifestyleRecommendationView(ConfiguredAIView):
    permission_classes = [IsPatient]

    def post(self, request):
        patient = _get_patient(request)
        profile = {
            'chronic_conditions': patient.chronic_conditions,
            'allergies': patient.allergies,
        }
        result = chains.generate_lifestyle_suggestions(profile)
        rec = AIRecommendation.objects.create(patient=patient, category='LIFESTYLE', content=result)
        return Response({'success': True, 'data': AIRecommendationSerializer(rec).data})


class MedicineExplanationView(ConfiguredAIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        medicine_name = request.data.get('medicine_name')
        dosage = request.data.get('dosage', '')
        if not medicine_name:
            return Response({'success': False, 'message': 'medicine_name is required.'}, status=400)
        result = chains.explain_medicine(medicine_name, dosage)
        return Response({'success': True, 'data': result})


class HealthScoreView(ConfiguredAIView):
    permission_classes = [IsPatient]

    def post(self, request):
        patient = _get_patient(request)
        recent_reports = list(
            patient.medical_reports.order_by('-created_at')[:5]
            .values_list('ai_structured_summary', flat=True)
        )
        profile = {
            'age': str(patient.date_of_birth) if patient.date_of_birth else None,
            'weight_kg': str(patient.weight_kg) if patient.weight_kg else None,
            'height_cm': str(patient.height_cm) if patient.height_cm else None,
            'chronic_conditions': patient.chronic_conditions,
        }
        result = chains.compute_ai_health_score(profile, recent_reports)
        patient.ai_health_score = result.get('score', patient.ai_health_score)
        patient.ai_risk_flags = result.get('risk_flags', [])
        patient.save(update_fields=['ai_health_score', 'ai_risk_flags'])
        return Response({'success': True, 'data': result})


class HealthChatView(ConfiguredAIView):
    """Free-form conversational AI health assistant (separate from the
    structured multi-turn Symptom Checker)."""
    permission_classes = [IsPatient]

    def get(self, request):
        patient = _get_patient(request)
        messages = patient.ai_chat_messages.order_by('created_at')
        return Response({
            'success': True,
            'messages': AIHealthAssistantMessageSerializer(messages, many=True).data,
        })

    def post(self, request):
        message = request.data.get('message', '').strip()
        if not message:
            return Response({'success': False, 'message': 'message is required.'}, status=400)

        patient = _get_patient(request)
        AIHealthAssistantMessage.objects.create(patient=patient, role='user', content=message)

        history = list(
            patient.ai_chat_messages.order_by('created_at').values('role', 'content')[:20]
        )
        reply = chains.general_health_chat_reply(history)
        assistant_msg = AIHealthAssistantMessage.objects.create(
            patient=patient, role='assistant', content=reply,
        )
        return Response({
            'success': True,
            'reply': AIHealthAssistantMessageSerializer(assistant_msg).data,
        }, status=status.HTTP_201_CREATED)


class DiseaseRiskPredictionView(ConfiguredAIView):
    permission_classes = [IsPatient]

    def get(self, request):
        patient = _get_patient(request)
        predictions = patient.risk_predictions.order_by('-created_at')[:10]
        return Response({
            'success': True,
            'data': DiseaseRiskPredictionSerializer(predictions, many=True).data,
        })

    def post(self, request):
        patient = _get_patient(request)
        recent_reports = list(
            patient.medical_reports.order_by('-created_at')[:5]
            .values_list('ai_structured_summary', flat=True)
        )
        profile = {
            'age': str(patient.date_of_birth) if patient.date_of_birth else None,
            'gender': patient.gender,
            'weight_kg': str(patient.weight_kg) if patient.weight_kg else None,
            'height_cm': str(patient.height_cm) if patient.height_cm else None,
            'chronic_conditions': patient.chronic_conditions,
        }
        result = chains.predict_disease_risk(profile, recent_reports)
        created = []
        for pred in result.get('predictions', []):
            obj = DiseaseRiskPrediction.objects.create(
                patient=patient,
                condition_name=pred.get('condition_name', 'Unknown'),
                risk_percentage=pred.get('risk_percentage', 0),
                contributing_factors=pred.get('contributing_factors', []),
                recommendation=pred.get('recommendation', ''),
            )
            created.append(obj)
        return Response({
            'success': True,
            'data': DiseaseRiskPredictionSerializer(created, many=True).data,
            'disclaimer': result.get('disclaimer', ''),
        }, status=status.HTTP_201_CREATED)
