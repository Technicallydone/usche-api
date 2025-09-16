# user/utils/roles.py
from user.models import User
from user.enums import ROLE

# --- Single role checks ---
def isAttendee(user: User) -> bool:
    return user.role == ROLE.ATTENDEE.value

def isOrganizer(user: User) -> bool:
    return user.role == ROLE.ORGANIZER.value

def isAdmin(user: User) -> bool:
    return user.role == ROLE.ADMIN.value

def isBursar(user: User) -> bool:
    return user.role == ROLE.BURSAR.value


# --- Two-role combinations ---
def isAttendeeOrOrganizer(user: User) -> bool:
    return user.role in {ROLE.ATTENDEE.value, ROLE.ORGANIZER.value}

def isAttendeeOrAdmin(user: User) -> bool:
    return user.role in {ROLE.ATTENDEE.value, ROLE.ADMIN.value}

def isAttendeeOrBursar(user: User) -> bool:
    return user.role in {ROLE.ATTENDEE.value, ROLE.BURSAR.value}

def isOrganizerOrAdmin(user: User) -> bool:
    return user.role in {ROLE.ORGANIZER.value, ROLE.ADMIN.value}

def isOrganizerOrBursar(user: User) -> bool:
    return user.role in {ROLE.ORGANIZER.value, ROLE.BURSAR.value}

def isAdminOrBursar(user: User) -> bool:
    return user.role in {ROLE.ADMIN.value, ROLE.BURSAR.value}


# --- Three-role combinations ---
def isAttendeeOrganizerAdmin(user: User) -> bool:
    return user.role in {ROLE.ATTENDEE.value, ROLE.ORGANIZER.value, ROLE.ADMIN.value}

def isAttendeeOrganizerBursar(user: User) -> bool:
    return user.role in {ROLE.ATTENDEE.value, ROLE.ORGANIZER.value, ROLE.BURSAR.value}

def isAttendeeAdminBursar(user: User) -> bool:
    return user.role in {ROLE.ATTENDEE.value, ROLE.ADMIN.value, ROLE.BURSAR.value}

def isOrganizerAdminBursar(user: User) -> bool:
    return user.role in {ROLE.ORGANIZER.value, ROLE.ADMIN.value, ROLE.BURSAR.value}


# --- All roles ---
def isAnyRole(user: User) -> bool:
    return user.role in {role.value for role in ROLE}
