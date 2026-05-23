from rest_framework import serializers
from abstracts.models import Abstract
from config.api_endpoints import APIEndpoints
from usche_app import settings
from user.serializers import UserResponseSerializer

class AbstractAuthorSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)

    abstract = serializers.UUIDField(read_only=True)

    full_name = serializers.CharField(max_length=255)
    affiliation = serializers.CharField(max_length=255)

    is_presenting_author = serializers.BooleanField(default=False)
    order = serializers.IntegerField(default=0)


class AbstractSerializer(serializers.Serializer):
    abstract_id = serializers.UUIDField()
    sub_theme = serializers.UUIDField()

    title = serializers.CharField()
    content = serializers.CharField()
    keywords = serializers.CharField()

    status = serializers.CharField()
    sent_at = serializers.DateTimeField(allow_null=True)
    comment = serializers.CharField(allow_null=True)

    is_payment_done = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    document = serializers.SerializerMethodField()

    user = UserResponseSerializer()

    authors = AbstractAuthorSerializer(many=True, read_only=True)

    def get_document(self, obj: Abstract):
        return f"{APIEndpoints.ABSTRACT_DOCUMENT}/{obj.abstract_id}/download-document"