from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WalletViewSet,
    my_wallet,
    import_wallet,
    logout_wallet,
    restore_wallet_from_drive,
    restore_wallet_session,
    set_backup_password,
)


router = DefaultRouter()
router.register(r'wallets', WalletViewSet)

urlpatterns = [
    path('wallets/me/', my_wallet, name='my_wallet'),
    path('wallets/import/', import_wallet, name='import_wallet'),
    path('wallets/logout/', logout_wallet, name='logout_wallet'),
    path("wallets/restore/", restore_wallet_from_drive),
    path("wallets/set-backup-password/", set_backup_password, name='set_backup_password'),
    path("wallets/session/restore/", restore_wallet_session),
  # ✅ Debug route
    path('', include(router.urls)),
]
