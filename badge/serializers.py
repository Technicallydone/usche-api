from rest_framework import serializers


class BadgeGenerationJobSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    conference_id = serializers.UUIDField()
    conference_name = serializers.CharField()

    status = serializers.CharField()

    total_attendees = serializers.IntegerField()
    processed_attendees = serializers.IntegerField()
    successful_badges = serializers.IntegerField()
    failed_badges = serializers.IntegerField()

    progress = serializers.FloatField()

    zip_file = serializers.CharField(allow_null=True, required=False)

    started_at = serializers.DateTimeField(allow_null=True)
    completed_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()


class BadgeDownloadSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    download_url = serializers.CharField()
    status = serializers.CharField()