from django.db import models
from django.contrib.auth.models import User

#aqui são os dispositivos atuadores (a valvula)
class CommandDevice(models.Model): 
    name = models.CharField(max_length=100)
    topic = models.CharField(max_length=200, unique=True)
    status_topic = models.CharField(max_length=200, unique=True, null=True, blank=True)
    status = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {'LIGADO' if self.status else 'DESLIGADO'}"  
    

# aqui dispositivos de leitura (os sensores)
class SensorDevice(models.Model):
    TIPO_SENSOR = [ #adicionamos escolha de tipos de sensor
        ('Temperatura', 'Temperatura'),        
        ('Humidade', 'Humidade'),
    ]

    name = models.CharField(max_length=100)
    topic = models.CharField(max_length=200, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)    
    current_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=10, editable=False)
    tipo_sensor = models.CharField(max_length=15, choices=TIPO_SENSOR, default="Temperatura")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.current_value if self.current_value is not None else 'N/D'} {self.unit})"

    def save(self, *args, **kwargs): #unidades por tipo
        if self.tipo_sensor == 'Temperatura':
            self.unit = '°C'
        elif self.tipo_sensor == 'Humidade':
             self.unit = '%'    
        super().save(*args, **kwargs)  

# Configurações de Irrigação = quando ligar 
class IrrigationConfig(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    temp_limit = models.FloatField(default=30.0, help_text="Temperatura máxima limite (°C)")
    hum_limit = models.FloatField(default=40.0, help_text="Umidade mínima limite (%)")
    auto_mode = models.BooleanField(default=False, help_text="Modo automático ligado/desligado")
    valve_is_on = models.BooleanField(default=False, help_text="Status atual da válvula")

    def __str__(self):
        return f"Config Irrigação - User: {self.user.username} (Auto: {self.auto_mode})"