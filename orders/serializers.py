from rest_framework import serializers
from .models import ShippingAddress

class ShippingAddressSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = ShippingAddress
        fields = [
            "id", "full_name", "phone_number",
            "address_line_1", "address_line_2",
            "city", "state", "postal_code", "country", "country_name",
            "instructions", "is_default", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        
    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["user"] = user

        if not ShippingAddress.objects.filter(user=user).exists():
            validated_data["is_default"] = True

        if validated_data.get("is_default") is True:
            ShippingAddress.objects.filter(user=user).update(is_default=False)
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('is_default') is True:
            (ShippingAddress.objects
             .filter(user=instance.user)
             .exclude(pk=instance.pk)
             .update(is_default=False))
            
        return super().update(instance, validated_data)
