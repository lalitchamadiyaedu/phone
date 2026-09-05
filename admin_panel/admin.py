from django.contrib import admin
from .models import DeviceLink, CapturedDeviceDetail, EnterpriseAsset

@admin.register(DeviceLink)
class DeviceLinkAdmin(admin.ModelAdmin):
    list_display = ('target_label', 'token', 'click_count', 'created_at')
    search_fields = ('target_label', 'token')

@admin.register(CapturedDeviceDetail)
class CapturedDeviceDetailAdmin(admin.ModelAdmin):
    list_display = ('device_model', 'session_status', 'battery_info', 'network_info', 'ip_address', 'last_ping')
    list_filter = ('session_status', 'is_online', 'page_focused')
    search_fields = ('device_model', 'ip_address', 'session_token')

@admin.register(EnterpriseAsset)
class EnterpriseAssetAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'device_model', 'admin_active', 'password_compliant', 'registered_at')
    list_filter = ('admin_active', 'password_compliant')
    search_fields = ('phone_number', 'device_model', 'asset_id')
