from django.shortcuts import render, redirect, get_object_or_404
from .models import CommandDevice
from .models import SensorDevice
from django.contrib.auth.decorators import login_required
from .mqtt_client import publish_message
from django.http import JsonResponse
from .models import SensorDevice
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from .models import CommandDevice, SensorDevice
from django.contrib.auth.decorators import login_required

@login_required
def device_list(request):
    command_devices = CommandDevice.objects.filter(user=request.user)
    sensor_devices = SensorDevice.objects.filter(user=request.user)
    return render(request, 'iot_devices/device_list.html', {
        'command_devices': command_devices,
        'sensor_devices': sensor_devices
    })

@login_required
def add_device(request):
    if request.method == "POST":
        device_type = request.POST.get('type')
        name = request.POST.get('name')
        topic = request.POST.get('topic')

        if device_type == 'command':
            CommandDevice.objects.create(name=name, topic=topic, user=request.user)
        elif device_type == 'sensor':
            SensorDevice.objects.create(name=name, topic=topic, user=request.user)
        
        return redirect('device_list')
    return render(request, 'iot_devices/add_device.html')

@login_required
def control_command_device(request, device_id):
    device = CommandDevice.objects.get(id=device_id)
    action = request.GET.get('action')  # 'on' ou 'off'
    if action in ['on', 'off']:
        publish_message(device.topic, action)
    return redirect('device_list')

@login_required
def edit_device(request, device_id):
    print("Editing device with ID:", device_id)
    pk = device_id

    # Tenta obter o dispositivo como CommandDevice ou SensorDevice
    try:
        device = CommandDevice.objects.get(id=pk, user=request.user)
    except CommandDevice.DoesNotExist:
        try:
            device = SensorDevice.objects.get(id=pk, user=request.user)
        except SensorDevice.DoesNotExist:
            # Nenhum dos dispositivos foi encontrado
            return redirect('device_list')  # Ou raise 404

    if request.method == "POST":
        device.name = request.POST.get('name')
        device.topic = request.POST.get('topic')
        device.save()
        return redirect('device_list')
    return render(request, 'iot_devices/edit_device.html', {'device': device})

@login_required
def delete_device(request, device_id):
    pk = device_id
    
    # Tenta obter o dispositivo como CommandDevice ou SensorDevice
    try:
        device = CommandDevice.objects.get(id=pk, user=request.user)
    except CommandDevice.DoesNotExist:
        try:
            device = SensorDevice.objects.get(id=pk, user=request.user)
        except SensorDevice.DoesNotExist:
            # Nenhum dos dispositivos foi encontrado
            return redirect('device_list')  # Ou raise 404
    
    print("Deleting device with ID:", device_id)

    if request.method == "POST":
        device.delete()
        return redirect('device_list')
    return render(request, 'iot_devices/delete_device.html', {'device': device})

@csrf_exempt##Cuidado ao utilizar o csrf_exempt, pois pode abrir brechas de segurança e permite requisições de qualquer origem
def update_sensor_value(request, sensor_id):
    #print("Received request user:", request.user)
    print("Updating sensor value for sensor ID:", sensor_id)

    if request.method == "POST":
        value = request.POST.get("value")
        try:
            #sensor = get_object_or_404(SensorDevice, id=sensor_id, user=request.user)
            sensor = get_object_or_404(SensorDevice, id=sensor_id)
            sensor.current_value = float(value)
            #print("Sensor current value updated to:", sensor.current_value)
            sensor.save()
        except ValueError:
            pass  # Trate se o valor não for numérico
    return redirect('device_list')

@login_required #corrigir atualização via ajax, que não pode estar autenticado.
#@csrf_exempt ##corrigir atualização via ajax, que não pode estar autenticado.
def get_sensor_values(request):
    sensors = SensorDevice.objects.filter(user=request.user)
    print("Fetching sensor values for user:", sensors[0])
    data = [
        {
            'id': sensor.id,
            'name': sensor.name,
            'topic': sensor.topic,
            'current_value': sensor.current_value if sensor.current_value is not None else "N/D",
            'unit': sensor.unit
        }
        for sensor in sensors
    ]
    return JsonResponse(data, safe=False)


@login_required
def profile(request):
    return render(request, 'registration/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, 'registration/edit_profile.html', {'form': form})