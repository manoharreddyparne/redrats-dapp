from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WalletViewSet, my_wallet, import_wallet, logout_wallet,restore_wallet_from_drive
router = DefaultRouter()
router.register(r'wallets', WalletViewSet) 

urlpatterns = [
    path('wallets/me/', my_wallet, name='my_wallet'),
    path('wallets/import/', import_wallet, name='import_wallet'),
    path('wallets/logout/', logout_wallet, name='logout_wallet'),
    path("wallets/restore/", restore_wallet_from_drive),
    path('', include(router.urls)),
]
