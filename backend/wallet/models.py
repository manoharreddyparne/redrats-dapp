from django.db import models
from users.models import GoogleUser 

class Wallet(models.Model):
    user = models.OneToOneField(GoogleUser, on_delete=models.CASCADE, related_name="wallet", null=True, blank=True)
    public_key = models.CharField(max_length=100, unique=True)
    backup_drive_file_id = models.CharField(max_length=255, blank=True, null=True)
    wallet_name = models.CharField(max_length=100, blank=True, null=True)
    password_hint = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.public_key
