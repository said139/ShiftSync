from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    handover_code = serializers.CharField(
        source="related_handover.report_code", read_only=True, default=None
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "organisation",
            "recipient",
            "notification_type",
            "type_display",
            "related_handover",
            "handover_code",
            "related_task",
            "title",
            "message",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields
