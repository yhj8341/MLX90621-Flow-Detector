/*
* A class for interfacing the Melexis 90621 Sensor from a Uno
* Modified from the code "readTemperatures" for Arduino Teensy by Robin van Emden:https://github.com/robinvanemden/MLX90621_Arduino_Processing
* This code is in the public domain.
*
 *  Created on: 4.24.2016
 *      Author: Max Yu
 */

#include <Arduino.h>
#include <Wire.h>
#include <stdarg.h>
#include "MLX90621.h"

MLX90621 sensor; // create an instance of the Sensor class

void setup(){
  Serial.begin(115200);
  Serial.println("trying to initialize sensor...");
  pinMode(D1, OUTPUT);
  digitalWrite(D1, HIGH);
  Wire.begin(D2, D3);
  sensor.initialise(16); // start the thermo cam with 8 frames per second
  Serial.println("sensor initialized!");
}

void loop(){
  sensor.measure(true); //get new readings from the sensor

  Serial.print("!{");
  for(int y=0;y<4;y++){ //go through all the rows
    Serial.print("\"row");
    Serial.print(y);
    Serial.print("\":[");

    for(int x=0;x<16;x++){ //go through all the columns
      double tempAtXY = sensor.getTemperature(y+x*4); // extract the temperature at position x/y
      Serial.print(tempAtXY);

      if (x<15) Serial.print(",");
    }
    Serial.print("]");
    if (y<3) Serial.print(",");
    //if (y<3)Serial.print("~");
      }
  Serial.print("}\n\n");

};
