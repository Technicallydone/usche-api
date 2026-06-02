from django.db import transaction

from user.enums.default_roles_enum import DefaultAppRolesEnum
from user.enums.permission_enums import AppPermissionEnum
from user.model.app_permission_model import AppPermission
from user.model.role_model import Role


class RoleSeeder:
    COMMON_PERMISSIONS = [
        AppPermissionEnum.READ_PROFILE,
        AppPermissionEnum.CHANGE_PASSWORD,
        AppPermissionEnum.SIGN_OUT,
        AppPermissionEnum.READ_OWN_CONFERENCE_JOIN_REQUEST,
        AppPermissionEnum.REQUEST_JOIN_CONFERENCE,
        AppPermissionEnum.READ_OWN_PAYMENTS,
        AppPermissionEnum.DOWNLOAD_PAYMENT_SLIP,
        AppPermissionEnum.DOWNLOAD_OWN_ABSTRACT_DOCUMENT,
        AppPermissionEnum.REQUEST_JOIN_TICKET,
        AppPermissionEnum.READ_CONFERENCE,
        AppPermissionEnum.READ_MAIN_THEME,
        AppPermissionEnum.READ_SUB_THEME,
        AppPermissionEnum.READ_SPEAKER,
        AppPermissionEnum.READ_SPONSOR,
        AppPermissionEnum.READ_ABSTRACT_OWN,
        AppPermissionEnum.CREATE_ABSTRACT,
        AppPermissionEnum.UPDATE_ABSTRACT,
        AppPermissionEnum.VIEW_DASHBOARD
    ]

    ROLE_PERMISSIONS = {
        DefaultAppRolesEnum.User: [],

        DefaultAppRolesEnum.Organizer: [
            AppPermissionEnum.READ_USERS,
            AppPermissionEnum.READ_USERS_REPORT,

            AppPermissionEnum.READ_ATTENDEES,

            AppPermissionEnum.READ_CONFERENCE_STATS,

            AppPermissionEnum.READ_CONFERENCE_JOIN_REQUEST,

            AppPermissionEnum.READ_ABSTRACT_ALL,
            AppPermissionEnum.APPROVE_ABSTRACT,
            AppPermissionEnum.REJECT_ABSTRACT,

            AppPermissionEnum.READ_INVITATION,
            AppPermissionEnum.SEND_INVITATION,
            AppPermissionEnum.RESEND_INVITATION,

            AppPermissionEnum.CREATE_SCHEDULE,
            AppPermissionEnum.UPDATE_SCHEDULE,
            AppPermissionEnum.DELETE_SCHEDULE,
            
            AppPermissionEnum.VERIFY_ATTENDEE,
        ],

        DefaultAppRolesEnum.Bursar: [
            AppPermissionEnum.READ_USERS,
            AppPermissionEnum.UPDATE_USERS,
            AppPermissionEnum.READ_USERS_REPORT,

            AppPermissionEnum.READ_PAYMENTS,
            AppPermissionEnum.VERIFY_PAYMENTS,
            AppPermissionEnum.APPROVE_PAYMENTS,
            AppPermissionEnum.REJECT_PAYMENTS,
            AppPermissionEnum.UPDATE_PAYMENTS,

            AppPermissionEnum.READ_CONFERENCE_STATS,
            AppPermissionEnum.VERIFY_ATTENDEE,
        ],
    }

    @classmethod
    def seed_default_roles(cls):
        with transaction.atomic():
            for role_enum in DefaultAppRolesEnum:
                role, _ = Role.objects.get_or_create(
                    name=role_enum.value
                )

                if role_enum == DefaultAppRolesEnum.Admin:
                    permissions = AppPermission.objects.filter(
                        code_name__in=[
                            perm.value
                            for perm in AppPermissionEnum
                            if perm != AppPermissionEnum.NONE
                        ]
                    )

                    role.permissions.set(permissions)
                    role.save()

                    continue

                permission_codes = (
                    cls.COMMON_PERMISSIONS
                    + cls.ROLE_PERMISSIONS.get(role_enum, [])
                )

                permissions = AppPermission.objects.filter(
                    code_name__in=[
                        permission.value
                        for permission in permission_codes
                    ]
                )

                role.permissions.set(permissions)
                role.save()

        print("All default roles seeded successfully!")