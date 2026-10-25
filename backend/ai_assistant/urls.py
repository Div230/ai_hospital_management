from django.urls import path
from .views import (
    SymptomCheckStartView, SymptomCheckReplyView, MySymptomSessionsView,
    DietRecommendationView, ExerciseRecommendationView, LifestyleRecommendationView,
    MedicineExplanationView, HealthScoreView, HealthChatView, DiseaseRiskPredictionView,
)

app_name = 'ai_assistant'

urlpatterns = [
    path('symptom-check/start/', SymptomCheckStartView.as_view(), name='symptom_start'),
    path('symptom-check/reply/', SymptomCheckReplyView.as_view(), name='symptom_reply'),
    path('symptom-check/sessions/', MySymptomSessionsView.as_view(), name='symptom_sessions'),
    path('recommendations/diet/', DietRecommendationView.as_view(), name='diet'),
    path('recommendations/exercise/', ExerciseRecommendationView.as_view(), name='exercise'),
    path('recommendations/lifestyle/', LifestyleRecommendationView.as_view(), name='lifestyle'),
    path('medicine-explanation/', MedicineExplanationView.as_view(), name='medicine_explanation'),
    path('health-score/', HealthScoreView.as_view(), name='health_score'),
    path('health-chat/', HealthChatView.as_view(), name='health_chat'),
    path('disease-risk/', DiseaseRiskPredictionView.as_view(), name='disease_risk'),
]
