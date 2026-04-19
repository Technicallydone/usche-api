from rest_framework import serializers

class CreateMainThemeSerializer(serializers.Serializer):
    conference_id = serializers.UUIDField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)


class CreateSubThemeSerializer(serializers.Serializer):
    theme_id = serializers.UUIDField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)


class UpdateMainThemeSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=True)


class UpdateSubThemeSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    theme_id = serializers.CharField(required=True)

    title = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=True)
    
class BulkUpdateSubThemesSerializer(serializers.Serializer):
    theme_id = serializers.CharField(required=True)
    sub_themes = UpdateSubThemeSerializer(many=True)