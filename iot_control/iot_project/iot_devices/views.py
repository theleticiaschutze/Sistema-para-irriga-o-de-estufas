import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.forms import UserChangeForm

from .models import CommandDevice, SensorDevice, IrrigationConfig
from .mqtt_client import publish_message


@csrf_exempt
def update_sensor_value_by_topic(request):
    if request.method == "POST":
        topic = request.POST.get("topic")
        value = request.POST.get("value")

        if topic and value is not None:
            
            try:
                sensor = SensorDevice.objects.get(topic=topic)
                sensor.current_value = float(value)
                sensor.save()
                return JsonResponse({"status": "success", "type": "sensor", "value": sensor.current_value})
            except SensorDevice.DoesNotExist:
                pass

            
            try:
                device = CommandDevice.objects.get(status_topic=topic)
                
                val_str = str(value).strip().lower()
                device.status = val_str in ['1', '1.0', 'on', 'true']
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
        status_topic = request.POST.get('status_topic')  
        tipo_sensor = request.POST.get('tipo_sensor')
        
        try:
            if device_type == 'command':
                CommandDevice.objects.create(
                    name=name, 
                    topic=topic, 
                    status_topic=status_topic if status_topic else None,
                    user=request.user
                )
            elif device_type == 'sensor':            
                SensorDevice.objects.create(
                    name=name, 
                    topic=topic, 
                    tipo_sensor=tipo_sensor, 
                    user=request.user
                )
            
            return redirect('device_list')
        except Exception as e:
            return render(request, 'iot_devices/add_device.html', {
                'error': f"Erro ao adicionar dispositivo: {e}"
            })

    return render(request, 'iot_devices/add_device.html')


@login_required
def control_command_device(request, device_id):
    device = get_object_or_404(CommandDevice, id=device_id, user=request.user)
    action = request.GET.get('action')
    if action in ['on', 'off']:
        try:
            publish_message(device.topic, action)
        except Exception as e:
            print("Erro ao publicar MQTT no controle manual:", e)

    url_anterior = request.META.get('HTTP_REFERER')
    if url_anterior:
        return redirect(url_anterior) 
        
    return redirect('device_list') 


@login_required
def edit_device(request, device_id):
    tipo_solicitado = request.GET.get('type') or request.POST.get('type')
    
    if tipo_solicitado == 'sensor':
        device = get_object_or_404(SensorDevice, id=device_id, user=request.user)
        device_type = 'sensor'
    else:
        device = get_object_or_404(CommandDevice, id=device_id, user=request.user)
        device_type = 'command'

    if request.method == "POST":
        device.name = request.POST.get('name')
        device.topic = request.POST.get('topic')
        if device_type == 'sensor':
            device.tipo_sensor = request.POST.get('tipo_sensor')
        elif device_type == 'command':
            device.status_topic = request.POST.get('status_topic') or None
        device.save()
        return redirect('device_list')
        
    return render(request, 'iot_devices/edit_device.html', {'device': device, 'device_type': device_type})


@login_required
def delete_device(request, device_id):
    pk = device_id
    try:
        device = CommandDevice.objects.get(id=pk, user=request.user)
    except CommandDevice.DoesNotExist:
        try:
            device = SensorDevice.objects.get(id=pk, user=request.user)
        except SensorDevice.DoesNotExist:
            return redirect('device_list')

    if request.method == "POST":
        device.delete()
        return redirect('device_list')
    return render(request, 'iot_devices/delete_device.html', {'device': device})


@csrf_exempt
def update_sensor_value(request, sensor_id):
    if request.method == "POST":
        value = request.POST.get("value")
        try:
            sensor = get_object_or_404(SensorDevice, id=sensor_id)
            sensor.current_value = float(value)
            sensor.save()
        except (ValueError, TypeError):
            pass
    return redirect('device_list')


@login_required
def get_sensor_values(request):
    sensors = SensorDevice.objects.filter(user=request.user)
    
    sensors_data = [
        {
            'id': sensor.id,
            'name': sensor.name,
            'topic': sensor.topic,
            'current_value': sensor.current_value if sensor.current_value is not None else "N/D",
            'unit': getattr(sensor, 'unit', ''),
            'tipo_sensor': sensor.tipo_sensor
        }
        for sensor in sensors
    ]

    config, _ = IrrigationConfig.objects.get_or_create(user=request.user)

    temp_sensor = sensors.filter(tipo_sensor='Temperatura').first()
    hum_sensor = sensors.filter(tipo_sensor='Humidade').first()

    temp_atual = temp_sensor.current_value if (temp_sensor and temp_sensor.current_value is not None) else None
    hum_atual = hum_sensor.current_value if (hum_sensor and hum_sensor.current_value is not None) else None

    # Se o modo automático estiver ativo e houver leituras válidas
    if config.auto_mode and (temp_atual is not None or hum_atual is not None):
        temp_limit = config.temp_limit if config.temp_limit is not None else 35.0
        hum_limit = config.hum_limit if config.hum_limit is not None else 40.0

        # Dispara se umidade for baixa ou temperatura excessiva
        condicao_temperatura = (temp_atual >= temp_limit) if temp_atual is not None else False
        condicao_umidade = (hum_atual <= hum_limit) if hum_atual is not None else False

        should_turn_on = condicao_temperatura or condicao_umidade
    else:
        # Se o modo automático for desligado no formulário, a válvula deve ser desligada
        should_turn_on = False

    # Executa a troca de estado quando houver alteração
    if config.valve_is_on != should_turn_on:
        config.valve_is_on = should_turn_on
        config.save()

        valve_device = CommandDevice.objects.filter(user=request.user).first()
        if valve_device:
            action = 'on' if should_turn_on else 'off'
            try:
                publish_message(valve_device.topic, action)
            except Exception as e:
                print("Erro ao publicar MQTT na automação:", e)

    return JsonResponse({
        'sensors': sensors_data,
        'valve_is_on': config.valve_is_on
    })


@login_required
def save_irrigation_config(request):
    if request.method == "POST":
        config, _ = IrrigationConfig.objects.get_or_create(user=request.user)
        
        temp_val = request.POST.get('temp_limit')
        hum_val = request.POST.get('hum_limit')

        try:
            if temp_val is not None and temp_val != "":
                config.temp_limit = float(temp_val)
            if hum_val is not None and hum_val != "":
                config.hum_limit = float(hum_val)
            
            config.auto_mode = 'auto_mode' in request.POST
            config.save()
            return JsonResponse({'status': 'success', 'message': 'Configurações salvas!'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Valores numéricos inválidos'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)


@login_required
def painel(request):    
    command_devices = CommandDevice.objects.filter(user=request.user)    
    sensor_devices = SensorDevice.objects.filter(user=request.user) 
    config, _ = IrrigationConfig.objects.get_or_create(user=request.user)
    
    return render(request, 'iot_devices/painel.html', {
        'command_devices': command_devices,
        'sensor_devices': sensor_devices,
        'config': config,
        'valve_is_on': config.valve_is_on
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