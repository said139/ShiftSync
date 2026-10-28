from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .engine import nlp_service_singleton


class NLPPredictRequestSerializer(serializers.Serializer):
    description = serializers.CharField(required=True, allow_blank=False)
    provider = serializers.CharField(required=False, allow_blank=True, default="")


class NLPBatchNarrativeSerializer(serializers.Serializer):
    shift_notes = serializers.CharField(required=True, allow_blank=False)


class NLPPredictAPIView(APIView):
    """
    POST /api/nlp/predict/
    Receives a task description, preprocesses text, runs the configured NLP classifier,
    and returns suggested category, priority, confidence score, and low-confidence warning.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        raw_desc = request.data.get("description")
        if raw_desc is None or not str(raw_desc).strip():
            return Response(
                {"detail": "Task description is required for NLP classification."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        org = getattr(request.user, "organisation", None)
        if org and not org.nlp_enabled:
            return Response(
                {
                    "available": False,
                    "task": str(raw_desc).strip(),
                    "category": "Operations",
                    "priority": "Medium",
                    "suggested_status": "Pending",
                    "category_confidence": 0.0,
                    "priority_confidence": 0.0,
                    "confidence_score": 0.0,
                    "is_low_confidence": True,
                    "provider": "disabled_by_admin",
                    "warning": (
                        "Automated NLP suggestions are disabled in your organisation settings. "
                        "Please select the category and priority manually."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        threshold = (
            float(org.low_confidence_threshold)
            if org and org.low_confidence_threshold is not None
            else None
        )
        requested_provider = (request.data.get("provider") or "").strip() or None

        try:
            result = nlp_service_singleton.classify_task(
                description=str(raw_desc),
                low_confidence_threshold=threshold,
                requested_provider=requested_provider,
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class NLPAnalyzeShiftNarrativeAPIView(APIView):
    """
    POST /api/nlp/analyze-log/
    Segments a multi-task shift activity log into discrete tasks and classifies each item.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        raw_notes = request.data.get("shift_notes") or request.data.get("description")
        if raw_notes is None or not str(raw_notes).strip():
            return Response(
                {"detail": "Shift activity notes are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        org = getattr(request.user, "organisation", None)
        threshold = (
            float(org.low_confidence_threshold)
            if org and org.low_confidence_threshold is not None
            else None
        )

        try:
            result = nlp_service_singleton.analyze_shift_narrative(
                shift_notes=str(raw_notes),
                low_confidence_threshold=threshold,
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class NLPStatusAPIView(APIView):
    """
    GET /api/nlp/status/
    Returns current NLP provider availability, thresholds, and evaluation metrics.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            nlp_service_singleton.get_status_metadata(),
            status=status.HTTP_200_OK,
        )
