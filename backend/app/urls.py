from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HabitViewSet, CategoryViewSet

# Create router for API endpoints
router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habit")
router.register(r"categories", CategoryViewSet, basename="category")

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),
    # API routes (habits and categories)
    path("api/", include(router.urls)),
    # Authentication routes
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
]
