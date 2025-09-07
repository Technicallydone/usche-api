from rest_framework import serializers

from abstracts.models import Abstract
from usche_app import settings
from user.serializers import UserResponseSerializer

class AbstractSerializer(serializers.ModelSerializer):
    document = serializers.SerializerMethodField()
    user = UserResponseSerializer(many=False)

    class Meta:
        model = Abstract
        fields = '__all__'
        
    def get_document(self, obj):
        abstract_id = obj.abstract_id
        
        return f"{settings.ABSTRACT_DOCUMENT_URL}/{abstract_id}/"
