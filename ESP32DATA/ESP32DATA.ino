#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

#include "FS.h"
#include "SD.h"
#include <SPI.h>

#include "MPU6050.h"

#define SEALEVELPRESSURE_HPA (1028.785)
#define select 10 // The ESP32 pin GPIO10
#define detect 5


Adafruit_BME280 bme;
MPU6050 imu;

String path = "/data.bin";

File file;

unsigned long t1;

struct datastore {
  float temp, hum, pres, alt;
  int16_t ax, ay, az, gx, gy, gz;
  unsigned long t;
};

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  delay(100);

  bme.begin(0x77);

  imu.initialize();

  pinMode(detect, INPUT);
  pinMode(select, OUTPUT);

  imu.setXAccelOffset(-2358);
  imu.setYAccelOffset(-3245);
  imu.setZAccelOffset(1574);
  imu.setXGyroOffset(11);
  imu.setYGyroOffset(31);
  imu.setZGyroOffset(17);

  while (!digitalRead(detect)){
    Serial.println("Nothing");
  }

  while(!SD.begin(select)) {
    Serial.println("There, but nothing");
  }

  file = SD.open(path, FILE_WRITE);

  t1 = millis();
}

void loop() {
  // put your main code here, to run repeatedly:
  struct datastore myData;

  myData.t = millis();
  myData.temp  = bme.readTemperature();
  myData.hum = bme.readHumidity();
  myData.pres = bme.readPressure() / 100.0F;
  myData.alt = bme.readAltitude(SEALEVELPRESSURE_HPA);

  imu.getMotion6(&myData.ax, &myData.ay, &myData.az, &myData.gx, &myData.gy, &myData.gz);

  digitalWrite(select, LOW);

  file.write((const uint8_t *)&myData, sizeof(myData));

  file.flush();

  if (myData.t > t1 + 50000) {
    file.close();
    t1 = myData.t;
    file = SD.open(path, FILE_WRITE);
  }
  
}


// void writeFile(fs::FS &fs, const char * path, const char * message) {
//   Serial.printf("Writing file: %s\n", path);

//   file = fs.open(path, FILE_WRITE);
//   if(!file) {
//     Serial.println("Failed to open file for writing");
//     return;
//   }
//   if(file.print(message)) {
//     Serial.println("File written");
//   } else {
//     Serial.println("Write failed");
//   }
//   file.flush();
// }

// void appendFile(fs::FS &fs, const char * path, const char * message) {
//   Serial.printf("Appending to file: %s\n", path);

//   File file = fs.open(path, FILE_APPEND);
//   if(!file) {
//     Serial.println("Failed to open file for appending");
//     return;
//   }
//   if(file.print(message)) {
//     Serial.println("Message appended");
//   } else {
//     Serial.println("Append failed");
//   }
//   file.flush();
// }


