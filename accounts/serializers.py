from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from rest_framework import serializers
from .models import User, VendorProfile

class CustomUserCreateSerializer(BaseUserCreateSerializer):    
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone_number', 'password']
        
    def validate(self, attrs):
        if not attrs.get('email') and not attrs.get('phone_number'):
            raise serializers.ValidationError("Provide either email or phone number.")
        return attrs
    

class CustomUserSerializer(BaseUserSerializer):
    role = serializers.SerializerMethodField()
    
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'username',
            'email', 'phone_number', 'role', 'is_active'
        ]
        
    def get_role(self, obj):
        return obj.get_role_display().lower()

class VendorRegisterSerializer(BaseUserCreateSerializer):
    store_name = serializers.CharField(write_only=True)
    business_license = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    business_phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = [
            "id", "first_name", "last_name", "username",
            "email", "phone_number", "password",
            "store_name", "business_license", "address", "business_phone",
        ]
        extra_kwargs = {"password": {"write_only": True}}
        
    def validate(self, attrs):
        # remove vendor fields so they don’t get passed to User()
        self._vendor_data = {
            "store_name": attrs.pop("store_name"),
            "business_license": attrs.pop("business_license", ""),
            "address": attrs.pop("address", ""),
            "business_phone": attrs.pop("business_phone", ""),
        }
        return super().validate(attrs)

    def create(self, validated_data):
        user = User.objects.create_user(
            role=User.VENDOR,
            **validated_data
        )

        # create vendor profile
        VendorProfile.objects.create(
            user=user,
            **self._vendor_data
        )
        return user

class VendorSerializer(serializers.ModelSerializer):
    vendor_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "first_name", "last_name", "username",
            "email", "phone_number", "role", "is_active",
            "vendor_profile",
        ]

    def get_vendor_profile(self, obj):
        if hasattr(obj, "vendor_profile"):
            vp = obj.vendor_profile
            return {
                "store_name": vp.store_name,
                "business_license": vp.business_license,
                "address": vp.address,
                "phone": vp.phone,
            }
        return None
