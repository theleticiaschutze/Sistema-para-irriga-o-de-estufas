import paho.mqtt.client as mqtt
import requests
from .mqtt_session_adm import session_mqtt

# Configurações do broker
MQTT_BROKER = "broker.emqx.io"  # ou seu IP local
MQTT_PORT = 1883
MQTT_TOPIC = "topicEdilson_ifsc/#"

# URL da API Django para atualizar o valor do sensor
API_URL = "http://localhost:8000/iot/update_sensor/"

def on_connect(client, userdata, flags, rc):
    print("Conectado ao broker com código:", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(f"Mensagem recebida: {msg.topic} => {msg.payload.decode()}")

    try:

        # Extrai o ID do dispositivo do tópico e converte a mensagem para número
        # Exemplo de tópico: "topicEdilson_ifsc/sensor/1"
        # if not msg.topic.startswith("topicEdilson_ifsc/sensor/"):
        #     print("Tópico não corresponde ao padrão esperado.")
        #     return
        sensor_id = int(msg.topic.split("/")[-1])  # Extrai o ID do dispositivo
        payload_value = float(msg.payload.decode())  # Converte a mensagem para número


        
        response = requests.post(
            f"{API_URL}{sensor_id}/",
            data={"value": payload_value}
        )

        # response = session_mqtt().post(
        #     f"{API_URL}{sensor_id}/",
        #     data={"value": payload_value}
        # )
        
        # print("Status da atualização:", response.status_code)
    except Exception as e:
        print("Erro ao processar mensagem:", e)

def connect_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    return client

def publish_message(topic, message):
    client = connect_mqtt()
    client.publish(topic, message)
    client.disconnect()

connect_mqtt()