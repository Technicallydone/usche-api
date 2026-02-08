# user/serializers/role_assignment.py
from rest_framework import serializers

from user.enums.user_role_action_enum import UserRoleActionEnum

class UserRoleAssignmentSerializer(serializers.Serializer):
    """
    Serializer to assign or unassign a role to/from a user.
    """
    role_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the role to assign or unassign"
    )
    action = serializers.ChoiceField(
        choices=UserRoleActionEnum.choices(),
        required=True,
        help_text="Action to perform: 'assign' or 'unassign'"
    )
