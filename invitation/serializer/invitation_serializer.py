from rest_framework import serializers

class InvitationUserResponseSerializer(serializers.Serializer):
    # User details
    user_id = serializers.UUIDField()
    first_name = serializers.CharField()
    middle_name = serializers.CharField(allow_null=True)
    last_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    title = serializers.CharField()
    affiliation = serializers.CharField()

    # Invitation details (null when the user has not been invited)
    invitation_id = serializers.UUIDField(allow_null=True)
    is_invited = serializers.BooleanField()
    
    # Map the JSON property 'invitation_sent' to the safe annotation name 'is_invitation_sent'
    invitation_sent = serializers.BooleanField(source='is_invitation_sent', allow_null=True)
    
    daily_sent_count = serializers.IntegerField(allow_null=True)
    invited_on = serializers.DateTimeField(allow_null=True)
    sent_at = serializers.DateTimeField(allow_null=True)

    # Conference details
    conference_id = serializers.UUIDField(allow_null=True) # Allowed null since conference_id can be missing
    conference_name = serializers.CharField(allow_null=True)