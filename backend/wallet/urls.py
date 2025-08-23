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
from .views_avalanche import (
        send_avax,
    send_token,
    contract_call
)

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')

app_name = "wallet"  # ✅ namespace for reverse lookups

urlpatterns = [
    path('wallets/me/', my_wallet, name='my_wallet'),
    path('wallets/import/', import_wallet, name='import_wallet'),
    path('wallets/logout/', logout_wallet, name='logout_wallet'),
    path("wallets/restore/", restore_wallet_from_drive, name='restore_wallet'),
    path("wallets/set-backup-password/", set_backup_password, name='set_backup_password'),
    path("wallets/session/restore/", restore_wallet_session, name='restore_wallet_session'),
    path("wallets/send-avax/", send_avax, name="send_avax"),
    path("wallets/send-token/", send_token, name="send_token"),
    path("wallets/contract-call/", contract_call, name="contract_call"),

    # ✅ Include ViewSet router
    path('', include(router.urls)),
]
