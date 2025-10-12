from rest_framework import serializers

class UsersSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(source="user.user_id", allow_null=True)
    first_name = serializers.CharField(source="user.first_name", allow_null=True)
    middle_name = serializers.CharField(source="user.middle_name", allow_null=True)
    last_name = serializers.CharField(source="user.last_name", allow_null=True)
    phone_number = serializers.CharField(source="user.phone_number", allow_null=True)
    email = serializers.EmailField(source="user.email", allow_null=True)
    country = serializers.CharField(source="user.country", allow_null=True)
    occupation = serializers.CharField(source="user.occupation", allow_null=True)
    title = serializers.CharField(source="user.title", allow_null=True)
    affiliation = serializers.CharField(source="user.affiliation", allow_null=False)
    invitation_status = serializers.BooleanField()
    invitation_sent = serializers.BooleanField()
