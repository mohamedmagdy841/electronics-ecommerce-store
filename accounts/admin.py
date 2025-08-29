from django.contrib import admin
from unfold.admin import ModelAdmin
from accounts.models import User, UserProfile, VendorProfile, PhoneOtp

@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'role', 'is_active', 'is_superuser', 'is_verified')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    list_filter = ('role', 'is_active', 'is_superuser', 'is_verified')
    list_per_page = 10
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'modified_at', 'password')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'username', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'is_verified')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
@admin.register(UserProfile)   
class UserProfileAdmin(ModelAdmin):
    list_display = ('user', 'profile_picture', 'address', 'city', 'state', 'country', 'postal_code')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'user__username')
    list_filter = ('city', 'state', 'country')
    list_per_page = 10
    readonly_fields = ('created_at', 'modified_at')
    fieldsets = (
        (None, {'fields': ('user', 'profile_picture')}),
        ('Address', {'fields': ('address', 'city', 'state', 'country', 'postal_code')}),
        ('Important dates', {'fields': ('created_at', 'modified_at')}),
    )

@admin.register(VendorProfile)
class VendorProfileAdmin(ModelAdmin):
    list_display = ('user', 'store_name', 'business_license', 'address', 'business_phone')
    search_fields = ('user__email', 'user__username', 'store_name', 'business_phone')
    list_filter = ('store_name',)
    list_per_page = 10
    readonly_fields = ('created_at', 'modified_at')
    fieldsets = (
        (None, {'fields': ('user', 'store_name', 'business_license')}),
        ('Contact info', {'fields': ('address', 'business_phone')}),
        ('Important dates', {'fields': ('created_at', 'modified_at')}),
    )


@admin.register(PhoneOtp)
class PhoneOtpAdmin(ModelAdmin):
    list_display = ('phone_number', 'otp', 'is_verified', 'created_at')
    search_fields = ('phone_number',)
    list_filter = ('is_verified',)
    list_per_page = 10
    readonly_fields = ('created_at',)
