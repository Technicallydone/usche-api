from rest_framework import serializers

class AbstractSubmissionSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=True)
    content = serializers.CharField(required=True)
    keywords = serializers.CharField(max_length=255, required=True)
    sub_theme = serializers.UUIDField(required=True)
    document = serializers.FileField(required=True)
    authors = serializers.CharField(
        required=True,
        help_text="Comma-separated list of author names"
    )

    def validate_keywords(self, value):
        """
        Custom validation for the keywords field. The value should be a string containing
        keywords separated by commas, and there should be between 3 and 5 keywords.
        """
        keywords = value.split(',')
        keywords = [keyword.strip() for keyword in keywords]
        num_keywords = len(keywords)

        if num_keywords < 3 or num_keywords > 5:
            raise serializers.ValidationError("Keywords should contain between 3 and 5 keywords.")

        return value