# user/serializers/query.py
from rest_framework import serializers

class UserFilterQuerySerializer(serializers.Serializer):
    search_query = serializers.CharField(required=False, allow_blank=True)
    staff = serializers.BooleanField(required=False)