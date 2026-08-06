from rest_framework import serializers


class CertificateZipSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    conference_id = serializers.UUIDField(source="conference.conference_id", read_only=True)
    conference_name = serializers.CharField(source="conference.conference_name", read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CertificateGenerationJobSerializer(serializers.Serializer):
    job_id = serializers.UUIDField(read_only=True)
    conference_id = serializers.UUIDField(read_only=True)
    conference_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    total_attendees = serializers.IntegerField(read_only=True)
    processed_attendees = serializers.IntegerField(read_only=True)
    successful_certificates = serializers.IntegerField(read_only=True)
    failed_certificates = serializers.IntegerField(read_only=True)
    progress = serializers.FloatField(read_only=True)
    zip_file = serializers.CharField(read_only=True, allow_null=True)
    started_at = serializers.DateTimeField(read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)