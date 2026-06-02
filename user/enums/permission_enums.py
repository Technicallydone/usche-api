# user/model/app_permission_model.py
from enum import Enum

class AppPermissionEnum(str, Enum):
    # Roles
    CREATE_ROLES = 'permission.create.roles'
    READ_ROLES = 'permission.view.roles'
    UPDATE_ROLES = 'permission.update.roles'
    DELETE_ROLES = 'permission.delete.roles'
    ADD_PERMISSIONS = 'permission.add.permissions'
    REMOVE_PERMISSIONS = 'permission.remove.permissions'
    ASSIGN_USER_ROLE = 'permission.assign.user.role'
    REMOVE_USER_ROLE = 'permission.remove.user.role'
    CHANGE_USER_ROLE = 'permission.change.user.role'

    # Permissions
    CREATE_PERMISSIONS = 'permission.create.permissions'
    READ_PERMISSIONS = 'permission.view.permissions'
    UPDATE_PERMISSIONS = 'permission.update.permissions'
    DELETE_PERMISSIONS = 'permission.delete.permissions'

    # Users
    READ_USERS = 'permission.view.users'
    CREATE_USERS = 'permission.create.users'
    UPDATE_USERS = 'permission.update.users'
    DELETE_USERS = 'permission.delete.users'
    READ_USERS_REPORT = 'permission.view.users.report'
    UPDATE_STAFF_STATUS = 'permission.update.staff.status'
    MANAGE_STAFF_MEMBERSHIP = 'permission.manage.staff.membership'
    REQUEST_JOIN_TOCKER = 'permission.join.request.ticket'
    
    # Attendees
    READ_ATTENDEES = 'permission.view.attendees'
    CREATE_ATTENDEES = 'permission.create.attendees'
    UPDATE_ATTENDEES = 'permission.update.attendees'
    DELETE_ATTENDEES = 'permission.delete.attendees'
    UPDATE_ATTENDEE_STATUS = 'permission.update.attendee.status'

    # Profile & Password
    READ_PROFILE = 'permission.view.profile'
    CHANGE_PASSWORD = 'permission.change.password'
    
    # Statistics
    READ_CONFERENCE_STATS = 'permission.view.conference.stats'
    
    # dashboard
    VIEW_DASHBOARD = 'permission.view.dashobard'
    
    SIGN_OUT = 'permission.sign.out'
    
    # Conference Management
    MANAGE_CONFERENCE = 'permission.manage.conference'
    READ_CONFERENCE = 'permission.view.conference'
    UPDATE_CONFERENCE = 'permission.update.conference'
    DELETE_CONFERENCE = 'permission.delete.conference'
    CREATE_CONFERENCE = 'permission.create.conference'
    REQUEST_JOIN_CONFERENCE = 'permission.join.request.conference'
        
    # Theme Management
    CREATE_MAIN_THEME = 'permission.create.main-theme'
    UPDATE_MAIN_THEME = 'permission.update.main-theme'
    READ_MAIN_THEME = 'permission.view.main-theme'
    DELETE_MAIN_THEME = 'permission.delete.main-theme'
    READ_CONFERENCE_JOIN_REQUEST= 'permission.read.join.request.conference'
    READ_OWN_CONFERENCE_JOIN_REQUEST= 'permission.read.own.join.request.conference'
    REQUEST_JOIN_TICKET = 'permission.join.request.ticket'
    VERIFY_ATTENDEE = 'permission.verify.attendee'
    
    CREATE_SUB_THEME = 'permission.create.sub-theme'
    UPDATE_SUB_THEME = 'permission.update.sub-theme'
    READ_SUB_THEME = 'permission.view.sub-theme'
    DELETE_SUB_THEME = 'permission.delete.sub-theme'
    
    CREATE_SPEAKER = 'permission.create.speaker'
    UPDATE_SPEAKER = 'permission.update.speaker'
    READ_SPEAKER = 'permission.view.speaker'
    DELETE_SPEAKER = 'permission.delete.speaker'
    
    CREATE_SPONSOR = 'permission.create.sponsor'
    UPDATE_SPONSOR = 'permission.update.sponsor'
    READ_SPONSOR = 'permission.view.sponsor',
    DELETE_SPONSOR = 'permission.delete.sponsor'
    
    # Conference Abstracts
    CREATE_ABSTRACT = 'permission.create.abstract'
    READ_ABSTRACT_ALL = 'permission.view.abstract.all'
    READ_ABSTRACT = 'permission.view.abstract'
    READ_ABSTRACT_OWN = 'permission.view.abstract.own'
    UPDATE_ABSTRACT = 'permission.update.abstract'
    DELETE_ABSTRACT = 'permission.delete.abstract'
    DOWNLOAD_ABSTRACT_DOCUMENT = 'permission.abstract.download'
    DOWNLOAD_OWN_ABSTRACT_DOCUMENT = 'permission.abstract.download.own'
    APPROVE_ABSTRACT = 'permission.abstract.approve'
    REJECT_ABSTRACT = 'permission.abstract.reject'

    # Payments
    CREATE_PAYMENTS = 'permission.create.payments'
    READ_PAYMENTS = 'permission.view.payments'
    READ_OWN_PAYMENTS = 'permission.view.own.payments'
    UPDATE_PAYMENTS = 'permission.update.payments'
    DELETE_PAYMENTS = 'permission.delete.payments'
    APPROVE_PAYMENTS = 'permission.approve.payments'
    REJECT_PAYMENTS = 'permission.reject.payments'
    VERIFY_PAYMENTS = 'permission.verify.payments'
    DOWNLOAD_PAYMENT_SLIP = 'permission.payments.slip.download'
    
    # -----------------------------------
    # INVITATIONS
    # -----------------------------------
    CREATE_INVITATION = 'permission.create.invitation'
    READ_INVITATION = 'permission.view.invitation'
    UPDATE_INVITATION = 'permission.update.invitation'
    DELETE_INVITATION = 'permission.delete.invitation'
    SEND_INVITATION = 'permission.send.invitation'
    RESEND_INVITATION = 'permission.resend.invitation'
    
    # -----------------------------------
    # SCHEDULE
    # -----------------------------------
    CREATE_SCHEDULE = 'permission.create.schedule'
    UPDATE_SCHEDULE = 'permission.update.schedule'
    DELETE_SCHEDULE = 'permission.delete.schedule'
    
    
    CREATE_BADGE = 'permission.create.badge'
    READ_BADGE = 'permission.view.badge'
    UPDATE_BADGE = 'permission.update.badge'
    DELETE_BADGE = 'permission.delete.badge'
    
    NONE = 'none'

    @staticmethod
    def seed_permissions():
        '''Create missing permissions automatically in DB.'''
        from django.db import transaction
        from user.model.app_permission_model import AppPermission

        with transaction.atomic():
            for perm in AppPermissionEnum:
                if not AppPermission.permission_exists(perm):
                    AppPermission.objects.create(code_name=perm)