#include <Wire.h>  // Include Wire library for I2C
#include "SparkFun_AS7265X.h" // SparkFun AS7265X library

AS7265X sensor;

void setup()
{
  Serial.begin(115200);
  Serial.println("AS7265x Spectral Triad I2C Example");

  Wire.begin();  // Initialize I2C
  delay(100);    // Allow I2C bus to stabilize

  if (sensor.begin() == false)
  {
    Serial.println("Sensor not detected! Check wiring.");
    while (1); // Halt if the sensor is not found
  }

  sensor.disableIndicator(); // Turn off the status LED

  Serial.println("A,B,C,D,E,F,G,H,R,I,S,J,T,U,V,W,K,L");
}

void loop()
{
  sensor.takeMeasurementsWithBulb(); // Take readings from all 18 channels

  Serial.print(sensor.getCalibratedA()); // 410nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedB()); // 435nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedC()); // 460nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedD()); // 485nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedE()); // 510nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedF()); // 535nm
  Serial.print(",");

  Serial.print(sensor.getCalibratedG()); // 560nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedH()); // 585nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedR()); // 610nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedI()); // 645nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedS()); // 680nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedJ()); // 705nm
  Serial.print(",");

  Serial.print(sensor.getCalibratedT()); // 730nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedU()); // 760nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedV()); // 810nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedW()); // 860nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedK()); // 900nm
  Serial.print(",");
  Serial.print(sensor.getCalibratedL()); // 940nm
  Serial.println();

  delay(1000); // Delay to reduce excessive serial output
}
