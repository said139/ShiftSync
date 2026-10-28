from django.urls import path
from .views import (
    NLPAnalyzeShiftNarrativeAPIView,
    NLPPredictAPIView,
    NLPStatusAPIView,
)

urlpatterns = [
    path("predict/", NLPPredictAPIView.as_view(), name="nlp-predict"),
    path("analyze-log/", NLPAnalyzeShiftNarrativeAPIView.as_view(), name="nlp-analyze-log"),
    path("status/", NLPStatusAPIView.as_view(), name="nlp-status"),
]
