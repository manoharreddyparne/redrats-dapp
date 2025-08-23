# users/serializers.py
from rest_framework import serializers
from .models import GoogleUser

class GoogleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleUser
        fields = ['id', 'sub', 'email', 'name', 'created_at', 'last_login']
