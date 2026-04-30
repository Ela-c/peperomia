// Libraries
#include "SD.h"
#include <Wire.h>
#include "RTClib.h"
#include <DHT.h>
#include <ArduinoJson.h>

#define LOG_INTERVAL 1000 // (3 mintues) mills between entries. milliseconds before writing the logged data permanently to disk.
#define SYNC_INTERVAL 1000 // mills between calls to flush() - to write data to the card

#define ECHO_TO_SERIAL 1 // echo data to serial port.

#define SOIL_MOISTURE_PIN 0 // pin that will receive the output of the soil moisture sensor
#define DHT_PIN 2 // pin that will receive the output of the humidity and temperature sensor
#define DHT_TYPE DHT22  // DHT 22 (AM2302)

/* VARIABLES - SOIL MOISTURE SENSOR */
float analogSoilMoisture; // raw analog input of soil moisture level measured in volts
int soilMoistureLevel; // level of moisture from 1 to 10 (10 being the analog value of 831 volts and 1 being 0 volts)
char *soil_state; // state of the soil (dry, humid or in water)
const int maxMoistureLevel = 1024;

/* VARIABLES - HUMIDITY AND TEMPERATURE SENSOR */
DHT dht(DHT_PIN, DHT_TYPE); // dht object
float hum; // stores humidity value in %
float temp; // store temperature value in C°
float heatIndex; // stores the heat index in C°

/* DATA LOGGING SHIELD */
RTC_PCF8523 RTC; // define the Real Time Clock object
const int chipSelect = 10; // for the data logging shield, we use digital pin 10 for the SD cs line
// the logging file
File logfile;


/*

Soil moisture values for my specific sensor

  Air = 0
  Wet tissue = 560
  Cup of water = 831

*/


void setup()
{
  Serial.begin(9600);
  Serial.setTimeout(10);

  // initialize the SD card
  initSDcard();

  //connect to RTC
  initRTC();

  // initialize dht sensor
  initDHT();

  // create a new file
  createFile();

  //Print the header of the csv file
  logfile.println("datetime,raw_moisture_level,moisture_level,air_humidity (%),air_temperature (C°),feels_like (C°)");
}

void loop()
{
  DateTime now;
  String server_data;
  // delay for the amount of time we want between readings
  delay((LOG_INTERVAL - 1) - (millis() % LOG_INTERVAL));

  // fetch the time
  now = RTC.now();
  // log time
  logfile.print(now.year(), DEC);
  logfile.print("/");
  logfile.print(now.month(), DEC);
  logfile.print("/");
  logfile.print(now.day(), DEC);
  logfile.print(" ");
  logfile.print(now.hour(), DEC);
  logfile.print(":");
  logfile.print(now.minute(), DEC);
  logfile.print(":");
  logfile.print(now.second(), DEC);

  // Read data and store it to variable
  analogSoilMoisture = analogRead(SOIL_MOISTURE_PIN);
  // log RAW moisture level
  log(String(analogSoilMoisture));

  // log SCALED moisture level
  soilMoistureLevel = (int)((analogSoilMoisture*10)/maxMoistureLevel);
  log(String(soilMoistureLevel));

  log(String(soil_state));

  // Log air humidity
  hum = dht.readHumidity();
  log(String(hum));
  
  // Log air temperature
  temp = dht.readTemperature();
  log(String(temp));
  
  // Log heat index
  heatIndex = dht.computeHeatIndex(temp, hum, false);
  log(String(heatIndex));

  logfile.println();

  // send relevant data to the server
  String buffer = String(temp) + "," + String(hum) + "," + String(soilMoistureLevel);
  Serial.println(buffer);
  // write to SD card
  logfile.flush();
}

void log(String variable){
  logfile.print(", ");
  logfile.print(variable);
}

/**
   The error() function. Prints out the error to the Serial Monitor, and then sits in a while(1); loop forever, also known as a halt
*/
void error(char const *str)
{
  Serial.print("error: ");
  Serial.println(str);

  while (1)
    ;
}

void initSDcard()
{
  Serial.print("Initializing SD card...");
  // make sure that the default chip select pin is set to
  // output, even if you don't use it:
  pinMode(10, OUTPUT);

  // see if the card is present and can be initialized:
  if (!SD.begin(chipSelect))
  {
    Serial.println("Card failed, or not present");
    // don't do anything more:
    return;
  }
  Serial.println("card initialized.");
}

void createFile()
{
  // file name must be in 8.3 format (name length at most 8 characters, follwed by a '.' and then a three character extension.
  char filename[] = "FN00.CSV";
  for (uint8_t i = 0; i < 100; i++)
  {
    filename[4] = i / 10 + '0';
    filename[5] = i % 10 + '0';
    if (!SD.exists(filename))
    {
      // only open a new file if it doesn't exist
      logfile = SD.open(filename, FILE_WRITE);
      break; // leave the loop!
    }
  }

  if (!logfile)
  {
    error("couldnt create file");
  }

  Serial.print("Logging to: ");
  Serial.println(filename);
}

void initRTC()
{
  Wire.begin();
  if (!RTC.begin())
  {
    logfile.println("RTC failed");
#if ECHO_TO_SERIAL
    Serial.println("RTC failed");
#endif // ECHO_TO_SERIAL
  }

  // following line sets the RTC to the date & time this sketch was compiled
  RTC.adjust(DateTime(F(__DATE__), F(__TIME__)));
}
void initDHT()
{
  dht.begin();
}

