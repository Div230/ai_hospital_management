from rest_framework import serializers
from .models import (
    SymptomCheckSession, AIHealthAssistantMessage,
    DiseaseRiskPrediction, AIRecommendation,
)


class SymptomCheckSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SymptomCheckSession
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at',
            'id', 'patient', 'status', 'conversation_history',
            'possible_conditions', 'risk_level', 'recommendation', 'created_at',
        ]


class SymptomCheckStartSerializer(serializers.Serializer):
    initial_complaint = serializers.CharField()


class SymptomCheckReplySerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    message = serializers.CharField()


class AIHealthAssistantMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIHealthAssistantMessage
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'created_at']


class DiseaseRiskPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseRiskPrediction
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'created_at']


class AIRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRecommendation
        fields = '__all__'
        read_only_fields = ['is_deleted', 'deleted_at', 'updated_at', 'id', 'patient', 'created_at']
