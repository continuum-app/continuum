from dj_rest_auth.registration.views import RegisterView
from rest_framework.response import Response
from rest_framework import status
from .models import SiteSettings


class CustomRegisterView(RegisterView):
    """
    Custom registration view that checks if registration is allowed
    in the site settings before allowing new user registration.
    """
    
    def create(self, request, *args, **kwargs):
        # Check if registration is allowed
        settings = SiteSettings.get_settings()
        
        if not settings.allow_registration:
            return Response(
                {"detail": "Registration is currently disabled by the site administrator."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If registration is allowed, proceed with normal registration
        return super().create(request, *args, **kwargs)