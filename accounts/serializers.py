from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from rest_framework import serializers
from .models import User

class CustomUserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone_number', 'password']
        
    def validate(self, attrs):
        if not attrs.get('email') and not attrs.get('phone_number'):
            raise serializers.ValidationError("Provide either email or phone number.")
        return attrs
    
    def create(self, validated_data):
        validated_data['role'] = User.CUSTOMER
        return super().create(validated_data)

class CustomUserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'username',
            'email', 'phone_number', 'role', 'is_active'
        ]
