from rest_framework import serializers

class UserResponseSerializer(serializers.Serializer):
    user_id = serializers.UUIDField() 
    first_name = serializers.CharField(allow_null=True)
    middle_name = serializers.CharField(allow_null=True)
    last_name = serializers.CharField(allow_null=True)
    phone_number = serializers.CharField(allow_null=True)
    email = serializers.EmailField(allow_null=True)
    country = serializers.CharField(allow_null=True)
    occupation = serializers.CharField(allow_null=True)
    title = serializers.CharField(allow_null=True)
    affiliation = serializers.CharField(allow_null=False)
    invitation_status = serializers.BooleanField()
    invitation_sent = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    is_active = serializers.BooleanField()
