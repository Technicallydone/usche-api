from rest_framework import serializers

from user.enums.invitation_status import InvitationStatusEnum


class InvitationFilterQuerySerializer(serializers.Serializer):
    search_query = serializers.CharField(required=False, allow_blank=True)
    conference_id = serializers.UUIDField(required=False)
    created_from = serializers.DateField(required=False)
    created_to = serializers.DateField(required=False)

    invitation_status = serializers.ChoiceField(
        choices=[
            InvitationStatusEnum.SENT.value,
            InvitationStatusEnum.NOT_SENT.value,
            "invited",
            "not_invited",
            "all",
        ],
        required=False,
        default="all",
    )