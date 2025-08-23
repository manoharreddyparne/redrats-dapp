from django.db import models
from users.models import GoogleUser

class Wallet(models.Model):
    user = models.ForeignKey(
    GoogleUser,
    on_delete=models.CASCADE,
    related_name="wallets"
)

    public_key = models.CharField(max_length=100, unique=True)
    encrypted_mnemonic = models.TextField()
    encryption_salt = models.CharField(max_length=255, null=True, blank=True)  # <-- Needed for decryption
    backup_drive_file_id = models.CharField(max_length=255, blank=True, null=True)
    wallet_name = models.CharField(max_length=100, blank=True, null=True)
    password_hint = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.public_key[:8]}... ({self.user.sub})"
