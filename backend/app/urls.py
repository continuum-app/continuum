from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HabitViewSet, CategoryViewSet, UserInfoView, SiteSettingsViewSet
from .custom_views import CustomRegisterView

# Create router for API endpoints
router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habit")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"settings", SiteSettingsViewSet, basename="settings")

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),
    # API routes (habits and categories)
    path("api/", include(router.urls)),
    # User info endpoint
    path("api/auth/user/", UserInfoView.as_view(), name="user-info"),
    # Authentication routes
    path("api/auth/", include("dj_rest_auth.urls")),
    # Custom registration endpoint
    path("api/auth/registration/", CustomRegisterView.as_view(), name="rest_register"),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
]
