from rest_framework import serializers
import re

class CreatePermissionRequestSerializer(serializers.Serializer):
    code_name = serializers.CharField(
        required=True,  # mandatory
        help_text="Code name (mandatory, must contain only letters, numbers, underscores, no spaces)"
    )
    description = serializers.CharField(
        required=False,  # optional
        allow_blank=True,
        help_text="Permission description (optional)"
    )

    def validate_code_name(self, value: str) -> str:
        """
        Validate that code_name contains only letters, numbers, and underscores, no spaces.
        """
        # Strip leading/trailing whitespace
        value = value.strip()

        # Regex: only letters, numbers, underscores
        if not re.fullmatch(r'[A-Za-z0-9_]+', value):
            raise serializers.ValidationError(
                "code_name must only contain letters, numbers, and underscores, with no spaces."
            )
        return value
