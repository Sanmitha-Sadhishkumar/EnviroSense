#include "DHT.h"
#define DHT22_PIN 3
DHT dht22(DHT22_PIN, DHT22);

const int sensor_pin = A0; 
const int air_quality_pin = A1; 
const int sound_pin = A2; 
const int csensor_pin = A3;

void setup() {
  pinMode (air_quality_pin, INPUT);
  Serial.begin(9600);
  dht22.begin(); 
}

void loop() {
  float moisture_percentage, air_quality, sound, cap_moisture;

  float humi  = dht22.readHumidity();
  // read temperature as Celsius
  float tempC = dht22.readTemperature();
  // read temperature as Fahrenheit
  float tempF = dht22.readTemperature(true);

  Serial.print("{'Humidity': ");
    Serial.print(humi);

    Serial.print(", "); 

    Serial.print("'Temperature': '");
    Serial.print(tempC);
    Serial.print(" ");
    Serial.print(tempF);
    Serial.print("', ");

  moisture_percentage = analogRead(sensor_pin);
  Serial.print("'Soil Moisture': ");
  Serial.print(moisture_percentage);
  Serial.print(", ");

  cap_moisture = analogRead(csensor_pin);
  Serial.print("'Cap Moisture': ");
  Serial.print(cap_moisture);
  Serial.print(", ");
  
  air_quality = analogRead(air_quality_pin);
  Serial.print("'Air Quality': ");
  Serial.print(air_quality);
  Serial.print(", ");

  sound = analogRead(sound_pin);
  Serial.print("'Sound': ");
  Serial.print(sound);
  Serial.print("} ");
  Serial.println();

  delay(1000);
}