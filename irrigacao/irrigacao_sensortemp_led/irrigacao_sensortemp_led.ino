#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>


#define DHTPIN D4     
#define DHTTYPE DHT11 

DHT dht(DHTPIN, DHTTYPE); 

// WiFi settings
const char *ssid = "RAU-IOT";             
const char *password = "10Tr4uEnsino";

// MQTT Broker settings
const char *mqtt_broker = "broker.emqx.io";  // EMQX broker endpoint
const char *mqtt_username = "emqx";  // MQTT username for authentication
const char *mqtt_password = "public";  // MQTT password for authentication
const int mqtt_port = 1883;  // MQTT port (TCP)

const char *sensor_topic = "topicIrrigacao_ifsc/5";     // MQTT topic
const char *comando_topic = "topicIrrigacao_ifsc/6";     // MQTT topic
const char *umidade_topic = "topicIrrigacao_ifsc/7";
const char *status_topic  = "topicIrrigacao_ifsc/8"; // statudos do led

unsigned long ultimoEnvio = 0;

WiFiClient espClient;
PubSubClient mqtt_client(espClient);

void connectToWiFi();
void connectToMQTTBroker();
void mqttCallback(char *topic, byte *payload, unsigned int length);

void setup() {
    Serial.begin(115200);
    pinMode(D6, OUTPUT);
    digitalWrite(D6, LOW);
    
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
        //String client_id = "esp_" + String("_2ffb34ed");
        Serial.printf("Conectando ao MQTT Broker %s.....\n", client_id.c_str());
        if (mqtt_client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
            Serial.println("Conectado ao MQTT broker");
            mqtt_client.subscribe(comando_topic);
            mqtt_client.publish(sensor_topic, "Ola EMQX sou ESP8266 trabalhando para irrigar! ^^");
            mqtt_client.publish(status_topic, digitalRead(D6) == HIGH ? "1" : "0");
        } else {
            Serial.print("Falha ao conectar no MQTT broker, rc=");
            Serial.print(mqtt_client.state());
            Serial.println(" tentando novamente em 5 segundos");
            delay(5000);
        }
    }
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
    Serial.print("Mensagem recebida do tópico: ");
    Serial.println(topic);
    Serial.print("Mensagem: ");
    
    String message;
    
    for (unsigned int i = 0; i < length; i++) {
        Serial.print((char) payload[i]);
        message += (char) payload[i];
    }

    message.trim();
    
    Serial.println();
    Serial.print("Mensagem: ");
    Serial.println(message);
    Serial.println("-----------------------");

    
    
    if (message == "on") {
        digitalWrite(D6, HIGH);
        mqtt_client.publish(status_topic, "1");
        Serial.println("D6 Ligado!");
    } 
    else if (message == "off") {
        digitalWrite(D6, LOW);
        mqtt_client.publish(status_topic, "0");
        Serial.println("D6 Desligado!");
    }
}


//void publish_sensor_data(int id, float temp) {
//    String topic = "sensor/" + String(id);
//    mqtt_client.publish(topic.c_str(), String(temp).c_str());
//}

void loop() {
    if (!mqtt_client.connected()) {
        connectToMQTTBroker();
    }

    mqtt_client.loop(); 

    if (millis() - ultimoEnvio >= 5000) {
        ultimoEnvio = millis();

        float temperatura = dht.readTemperature();
        float umidade = dht.readHumidity();
        
       if (isnan(temperatura) || isnan(umidade)) {
       Serial.println("Falha ao ler dados do sensor DHT11!");
       return;
         }

        String payloadTemp = String(temperatura, 1);
        String payloadUmid = String(umidade, 1);
    
         mqtt_client.publish(sensor_topic, payloadTemp.c_str());
         mqtt_client.publish(umidade_topic, payloadUmid.c_str());
        Serial.print("Temp enviada: ");
        Serial.println(payloadTemp);
        Serial.print("Umi enviada: ");
        Serial.print(payloadUmid);
    }

    
}
