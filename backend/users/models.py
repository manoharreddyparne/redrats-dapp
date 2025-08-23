from django.db import models

class GoogleUser(models.Model):
    sub = models.CharField(max_length=255, unique=True)  # Unique user ID (used always)
    email = models.EmailField(unique=True, null=True, blank=True)  # Only populated when Drive backup is enabled
    name = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email if self.email else f"User-{self.sub}"
