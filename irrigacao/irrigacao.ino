#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// WiFi settings
const char *ssid = "RAU-IOT";             
const char *password = "10Tr4uEnsino";

// MQTT Broker settings
const char *mqtt_broker = "broker.emqx.io";  // EMQX broker endpoint
//const char *mqtt_topic = "topicEdilson_ifsc/esp8266";     // MQTT topic
const char *mqtt_topic = "topicEdilson_ifsc/3";     // MQTT topic
const char *mqtt_username = "emqx";  // MQTT username for authentication
const char *mqtt_password = "public";  // MQTT password for authentication
const int mqtt_port = 1883;  // MQTT port (TCP)

WiFiClient espClient;
PubSubClient mqtt_client(espClient);


void connectToWiFi();

void connectToMQTTBroker();

void mqttCallback(char *topic, byte *payload, unsigned int length);

void setup() {
    Serial.begin(115200);
    connectToWiFi();
    mqtt_client.setServer(mqtt_broker, mqtt_port);
    mqtt_client.setCallback(mqttCallback);
    connectToMQTTBroker();
}

void connectToWiFi() {
    WiFi.begin(ssid, password);
    Serial.print("Conectando ao WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConectado a rede WiFi");
}

void connectToMQTTBroker() {
    while (!mqtt_client.connected()) {
        String client_id = "esp8266-client-" + String(WiFi.macAddress());
        Serial.printf("Conectando ao MQTT Broker %s.....\n", client_id.c_str());
        if (mqtt_client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
            Serial.println("Conectado ao MQTT broker");
            mqtt_client.subscribe(mqtt_topic);
            // Publish message upon successful connection
            mqtt_client.publish(mqtt_topic, "Ola EMQX sou ESP8266 ^^");
        } else {
            Serial.print("Falha ao contectar no MQTT broker, rc=");
            Serial.print(mqtt_client.state());
            Serial.println(" tentando novamente em 5 segundos");
            delay(5000);
        }
    }
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
    Serial.print("Mensagem recebido do tópico: ");
    Serial.println(topic);
    Serial.print("Mensagem:");
    for (unsigned int i = 0; i < length; i++) {
        Serial.print((char) payload[i]);
    }
    Serial.println();
    Serial.println("-----------------------");
}

void publish_sensor_data(int id, float temp) {
    String topic = "sensor/" + String(id);
    client.publish(topic.c_str(), String(temp).c_str());
}

void loop() {
    if (!mqtt_client.connected()) {
        connectToMQTTBroker();
    }

    int temperatura = analogRead(A0);

    String payload = String(temperatura); // Transforma a temperatura em string
    
    // Publica no tópico MQTT
    mqtt_client.publish(mqtt_topic, payload.c_str());

    mqtt_client.loop();

    delay(5000);
}
