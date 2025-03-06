#include <Wire.h>
#include "SparkFun_AS7265X.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
AS7265X sensor;

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }
  Serial.println("AS7265x Spectral Triad I2C Example on ESP8266");

  Wire.begin(D2, D1);  // SDA = GPIO 4, SCL = GPIO 5
  delay(100);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    while (1);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("AS7265X Ready"));
  display.display();

  if (sensor.begin() == false) {
    Serial.println("Sensor not detected!");
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println(F("Sensor Error"));
    display.display();
    while (1);
  }

  sensor.disableIndicator();
  Serial.println("A,B,C,D,E,F,G,H,R,I,S,J,T,U,V,W,K,L");
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    data.trim();
    Serial.println("Received: " + data);

    // Parse object name, brix, ripeness, freshness
    int firstComma = data.indexOf(',');
    int secondComma = data.indexOf(',', firstComma + 1);
    int thirdComma = data.indexOf(',', secondComma + 1);

    String objectName = data.substring(0, firstComma);
    String brix = data.substring(firstComma + 1, secondComma);
    String ripeness = data.substring(secondComma + 1, thirdComma);
    String freshness = data.substring(thirdComma + 1);

    // Update OLED
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("Object: " + objectName);
    display.println("Brix: " + brix);
    display.println("Ripeness: " + ripeness + "%");
    display.println("Freshness: " + freshness + "%");
    display.display();
  }

  sensor.takeMeasurementsWithBulb();
  Serial.print(sensor.getCalibratedA()); Serial.print(",");
  Serial.print(sensor.getCalibratedB()); Serial.print(",");
  Serial.print(sensor.getCalibratedC()); Serial.print(",");
  Serial.print(sensor.getCalibratedD()); Serial.print(",");
  Serial.print(sensor.getCalibratedE()); Serial.print(",");
  Serial.print(sensor.getCalibratedF()); Serial.print(",");
  Serial.print(sensor.getCalibratedG()); Serial.print(",");
  Serial.print(sensor.getCalibratedH()); Serial.print(",");
  Serial.print(sensor.getCalibratedR()); Serial.print(",");
  Serial.print(sensor.getCalibratedI()); Serial.print(",");
  Serial.print(sensor.getCalibratedS()); Serial.print(",");
  Serial.print(sensor.getCalibratedJ()); Serial.print(",");
  Serial.print(sensor.getCalibratedT()); Serial.print(",");
  Serial.print(sensor.getCalibratedU()); Serial.print(",");
  Serial.print(sensor.getCalibratedV()); Serial.print(",");
  Serial.print(sensor.getCalibratedW()); Serial.print(",");
  Serial.print(sensor.getCalibratedK()); Serial.print(",");
  Serial.print(sensor.getCalibratedL());
  Serial.println();

  delay(500);
}