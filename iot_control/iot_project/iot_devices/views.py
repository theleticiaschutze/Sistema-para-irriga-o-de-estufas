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

@csrf_exempt
def update_sensor_value_by_topic(request):
    if request.method == "POST":
        topic = request.POST.get("topic")
        value = request.POST.get("value")

        if topic and value is not None:
            # 1. Tenta atualizar se for SensorDevice
            try:
                sensor = SensorDevice.objects.get(topic=topic)
                sensor.current_value = float(value)
                sensor.save()
                return JsonResponse({"status": "success", "type": "sensor", "value": sensor.current_value})
            except SensorDevice.DoesNotExist:
                pass

            # 2. Tenta atualizar se for CommandDevice (Status do Atuador)
            try:
                device = CommandDevice.objects.get(status_topic=topic)
                # Converte "1" / "on" para True, e "0" / "off" para False
                device.status = str(value).strip() in ['1', 'on', 'true', 'True']
                device.save()
                return JsonResponse({"status": "success", "type": "command", "is_active": device.status})
            except CommandDevice.DoesNotExist:
                return JsonResponse({"error": "Tópico não cadastrado"}, status=404)

    return JsonResponse({"error": "Método não permitido"}, status=405)

@login_required
def get_actuator_values(request):
    actuators = CommandDevice.objects.filter(user=request.user)
    data = [
        {
            'id': dev.id,
            'name': dev.name,
            'status': dev.status
        }
        for dev in actuators
    ]
    return JsonResponse(data, safe=False)

@login_required
def device_list(request): # listagem dos dispositivos
    command_devices = CommandDevice.objects.filter(user=request.user) # puxa os dispositivos atuadores do db conforme o user
    sensor_devices = SensorDevice.objects.filter(user=request.user) # puxa os dispositivos sensores do db conforme o user
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
        tipo_sensor = request.POST.get('tipo_sensor') #adicionei tipo sensor em add_device
        #if else para se for comando ou sensor, so sensor mostra tipo
        if device_type == 'command':
            CommandDevice.objects.create(name=name, topic=topic, user=request.user)
        elif device_type == 'sensor':            
            SensorDevice.objects.create(name=name, topic=topic, tipo_sensor=tipo_sensor, user=request.user)
        
        return redirect('device_list')
    return render(request, 'iot_devices/add_device.html')

@login_required
def control_command_device(request, device_id):
    device = CommandDevice.objects.get(id=device_id)
    action = request.GET.get('action')  # 'on' ou 'off'
    if action in ['on', 'off']:
        publish_message(device.topic, action)

    url_anterior = request.META.get('HTTP_REFERER')
    
    if url_anterior:
        return redirect(url_anterior) 
        
    return redirect('device_list') 
    

@login_required
def edit_device(request, device_id):
    
    try:
        device = SensorDevice.objects.get(id=device_id, user=request.user)
        device_type = 'sensor'
    except SensorDevice.DoesNotExist:
        
        device = get_object_or_404(CommandDevice, id=device_id, user=request.user)
        device_type = 'command'

    if request.method == "POST":
        device.name = request.POST.get('name')
        device.topic = request.POST.get('topic')
        
        if device_type == 'sensor':
            device.tipo_sensor = request.POST.get('tipo_sensor')
            
        device.save()
        return redirect('device_list')
        
    return render(request, 'iot_devices/edit_device.html', {'device': device, 'device_type': device_type})



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
            'unit': sensor.unit,
            'tipo_sensor': sensor.tipo_sensor #adicionei isso
        }
        for sensor in sensors
    ]
   if config.auto_mode:
        temp_sensor = sensors.filter(tipo_sensor='Temperatura').first()
        hum_sensor = sensors.filter(tipo_sensor='Humidade').first()

        temp_atual = temp_sensor.current_value if temp_sensor and temp_sensor.current_value is not None else -999
        hum_atual = hum_sensor.current_value if hum_sensor and hum_sensor.current_value is not None else 999

        # Aciona se Temp for MAIOR/IGUAL ao limite OU se Umidade for MENOR/IGUAL ao limite
        should_turn_on = (temp_atual >= config.temp_limit) or (hum_atual <= config.hum_limit)

        if config.valve_is_on != should_turn_on:
            config.valve_is_on = should_turn_on
            config.save()

            # Se houver um atuador cadastrado, envia o comando via MQTT
            valve_device = CommandDevice.objects.filter(user=request.user).first()
            if valve_device:
                action = 'on' if should_turn_on else 'off'
                publish_message(valve_device.topic, action)
                valve_device.status = should_turn_on
                valve_device.save()

    return JsonResponse({
        'sensors': sensors_data,
        'valve_is_on': config.valve_is_on
    })


@login_required
def save_irrigation_config(request):
    if request.method == "POST":
        config, _ = IrrigationConfig.objects.get_or_create(user=request.user)
        config.temp_limit = float(request.POST.get('temp_limit', config.temp_limit))
        config.hum_limit = float(request.POST.get('hum_limit', config.hum_limit))
        config.auto_mode = 'auto_mode' in request.POST
        config.save()
        return JsonResponse({'status': 'success', 'message': 'Configurações salvas!'})
    return JsonResponse({'status': 'error', 'message': 'Método inválido'}, status=400)

@login_required
def painel(request):    
    command_devices = CommandDevice.objects.filter(user=request.user)    
    
    sensor_devices = SensorDevice.objects.filter(user=request.user) 
    
    return render(request, 'iot_devices/painel.html', {
        'command_devices': command_devices,
        'sensor_devices': sensor_devices
    })


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