from django.db import models
from django.contrib.auth.models import User

#aqui são os dispositivos atuadores (a valvula)
class CommandDevice(models.Model): 
    name = models.CharField(max_length=100)
    topic = models.CharField(max_length=200, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# aqui dispositivos de leitura (os sensores)
class SensorDevice(models.Model):
    name = models.CharField(max_length=100)
    topic = models.CharField(max_length=200, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    current_value = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=10, default="°C")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.current_value or 'N/D'} {self.unit})"