from rest_framework import serializers
from abstracts.models import Abstract
from usche_app import settings
from user.serializers import UserResponseSerializer


class AbstractSerializer(serializers.Serializer):
    abstract_id = serializers.UUIDField()
    sub_theme = serializers.UUIDField()

    title = serializers.CharField()
    authors = serializers.CharField(allow_null=True, required=False)
    content = serializers.CharField()
    keywords = serializers.CharField()

    status = serializers.CharField()
    sent_at = serializers.DateTimeField(allow_null=True)
    comment = serializers.CharField(allow_null=True)

    is_payment_done = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    document = serializers.SerializerMethodField()

    user = UserResponseSerializer()

    def get_document(self, obj: Abstract):
        return f"{settings.ABSTRACT_DOCUMENT_URL}/{obj.abstract_id}/"