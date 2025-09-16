# user/decorators.py
from functools import wraps
from typing import cast
from django.http import HttpRequest
from rest_framework.response import Response

from user.models import User

def roles_required(*check_funcs):
    """
    Method-level decorator to check user roles.
    Accepts one or more check functions from user/utils.py
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request: HttpRequest, *args, **kwargs):
            user = cast(User, request.user)
            if not user.is_authenticated:
                return Response({"detail": "Authentication required"}, status=401)
            
            # If any check_func passes, allow access
            if not any(check(user) for check in check_funcs):
                return Response({"detail": "You do not have permission to perform this action"}, status=403)
            
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator
