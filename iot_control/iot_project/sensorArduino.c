#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "SEU_WIFI";
const char* password = "SENHA_WIFI";
const char* mqtt_server = "broker.emqx.io";

WiFiClient wifiClient;
PubSubClient client(wifiClient);

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Conectando ao Wi-Fi...");
    }

    client.setServer(mqtt_server, 1883);
    while (!client.connect("esp8266")) {
        delay(1000);
        Serial.println("Conectando ao MQTT...");
    }

    client.subscribe("dispositivo/meu_topico"); // Substitua pelo tópico que cadastrar no Django
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    if (Serial.available()) {
        String command = Serial.readString();
        if (command == "on") {
            digitalWrite(D1, HIGH);  // Liga o dispositivo
        } else if (command == "off") {
            digitalWrite(D1, LOW);   // Desliga o dispositivo
        }
    }
}

void reconnect() {
    while (!client.connect("esp8266")) {
        delay(1000);
        Serial.println("Reconectando...");
    }
}