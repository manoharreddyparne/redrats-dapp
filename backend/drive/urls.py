from django.urls import path
from . import views

app_name = 'drive'  # Optional but recommended for namespacing
from .views_debug import debug_wallet_view
urlpatterns = [
    path('auth/init/', views.initiate_auth, name='initiate_auth'),
    path('oauth2callback/', views.oauth2_callback, name='oauth2_callback'),

    path('upload/', views.upload_wallet_backup, name='upload_wallet_backup'),
    path('download/', views.download_wallet_backup, name='download_wallet_backup'),
    path('debug/', debug_wallet_view, name='debug_wallet'),
]
