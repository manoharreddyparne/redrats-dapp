# users/urls.py
from django.urls import path
from .views import get_user_profile, google_login, logout_user

app_name = "users"  # ✅ namespace for reverse lookups

urlpatterns = [
    # ✅ Public endpoint for Google login
    path('login/google/', google_login, name='google_login'),

    # ✅ Authenticated endpoints
    path('me/', get_user_profile, name='get_user_profile'),
    path('logout/', logout_user, name='logout_user'),
]
