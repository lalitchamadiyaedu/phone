from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('sw.js', views.sw_js, name='sw_js'),
    path('manifest.json', views.manifest_json, name='manifest_json'),
    path('download-app/', views.download_app, name='download_app'),
    path('api/register-asset/', views.register_asset, name='register_asset'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('generate-link/', views.generate_link, name='generate_link'),
    path('delete-device/<int:device_id>/', views.delete_device, name='delete_device'),
    path('delete-link/<int:link_id>/', views.delete_link, name='delete_link'),
    path('api/device-details/<int:device_id>/', views.get_device_detail_json, name='device_detail_json'),
    path('api/live-devices/', views.api_live_devices, name='api_live_devices'),
    path('inspect/<str:token>/', views.inspect_device, name='inspect_device'),
    path('api/submit-device-info/<str:token>/', views.submit_device_info, name='submit_device_info'),
    path('logout/', views.logout_view, name='logout'),
]
