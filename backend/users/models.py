from django.db import models

class GoogleUser(models.Model):
    sub = models.CharField(max_length=255, unique=True)  # Unique Google ID
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.email
