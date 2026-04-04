# user/serializers/role_assignment.py
from rest_framework import serializers

class UserRoleAssignmentSerializer(serializers.Serializer):
    """
    Serializer to assign or unassign a role to/from a user.
    """
    role_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the role to assign or unassign"
    )
