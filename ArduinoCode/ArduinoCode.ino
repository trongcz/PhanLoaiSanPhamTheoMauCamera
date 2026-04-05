#include <Wire.h> 
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

#define CB1     A0
#define CB2     A1
#define CB3     A2
#define CB4     A3

#define SV1     5
#define SV2     6
#define SV3     7
#define SV4     8

#define BT1     10
#define BT2     11
#define BT3     12

#define DC      4

#define TO1     2000
#define POS0    0
#define POS1    90

LiquidCrystal_I2C lcd(0x27,16, 2);

int sensor[4] = {A0, A1, A2, A3};
String color[4] = {"RED", "GREEN", "YELLOW", "BLACK"};
int servo_pin[4] = {5, 6, 7, 8};
Servo servo[4];

String s;
unsigned long t1;
bool received = 0;
bool programData = 0;
bool programColor = 0;
int colorX;

void setup()
{
  pinMode(CB1, INPUT);
  pinMode(CB1, INPUT);
  pinMode(CB1, INPUT);
  pinMode(CB1, INPUT);
  
  pinMode(BT1, INPUT_PULLUP);
  pinMode(BT2, INPUT_PULLUP);
  pinMode(BT3, INPUT_PULLUP);
  
  pinMode(DC, OUTPUT);

  digitalWrite(DC, HIGH);

  Serial.begin(9600);
  Serial.println("Start...");
  lcd.init();
  lcd.backlight();
  lcd.setCursor(6,0);
  lcd.print("Hi!");

  for(int i=0; i<4; i++){
    servo[i].attach(servo_pin[i]);
    servo[i].write(POS0); 
  }

  delay(1000);
}


void loop()
{
  if (Serial.available()) {
    s = Serial.readStringUntil('\n');
    received = 1;
    programData = 1;
    t1 = millis() + TO1;
  }

  if(received){
    if(programData){
      Serial.print("A: ");
      Serial.println(s);
      // for (int i = 0; i < s.length(); i++) {
      //   // Print each character as a HEX value
      //   Serial.print(s[i], HEX);
      //   Serial.print(" "); // Add a space for readability
      // }
      //lcd.clear();
      LcdClear();
      lcd.print(s);

      for(int i=0; i<4; i++){
        if (s == color[i]) {
          Serial.println(i);
          // xử lý 
          colorX = i;
          servo[colorX].write(POS1); 
        }
      }
      programData = 0;
      programColor = 1;

    }
    
    if(millis() > t1){
      received = 0;
      //lcd.clear();
      LcdClear();
    }
  }

  if(programColor){
    if(digitalRead(sensor[colorX]) == 0){
      servo[colorX].write(POS0);
      programColor = 0;
    }
  }
}
void LcdClear(){
  lcd.setCursor(0,1);
  for(int i = 0; i<16; i++)
  lcd.print(" ");
}