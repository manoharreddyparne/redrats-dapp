from django.urls import path
from . import views

urlpatterns = [
    path('auth/init/', views.initiate_auth, name='initiate_auth'),
    path('oauth2callback/', views.oauth2_callback, name='oauth2_callback'),
    path('upload/', views.upload_wallet_backup, name='upload_wallet_backup'),
     path('download/', views.download_wallet_backup, name='download_wallet_backup'), 
]
