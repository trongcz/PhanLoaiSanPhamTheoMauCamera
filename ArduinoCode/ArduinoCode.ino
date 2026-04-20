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
#define TO2     1000
#define POS0    90
#define POS1    40

LiquidCrystal_I2C lcd(0x27,16, 2);

int sensor[4] = {A0, A1, A2, A3};
String color[4] = {"RED", "GREEN", "YELLOW", "BLACK"};
int servo_pin[4] = {5, 6, 7, 8};
Servo servo[4];

String s;
unsigned long t1, t2;
bool received = 0;
bool programData = 0;
bool programColor = 0;
int colorX;
bool wait1 = 0;
bool wait2 = 0;

bool onDC = 0;

void setup()
{
  for(int i = 0; i<4; i++){
    pinMode(sensor[i], INPUT);
  }
  
  pinMode(BT1, INPUT_PULLUP);
  pinMode(BT2, INPUT_PULLUP);
  pinMode(BT3, INPUT_PULLUP);
  
  pinMode(DC, OUTPUT);

  digitalWrite(DC, LOW);

  Serial.begin(9600);
  Serial.println("Start...");
  lcd.init();
  lcd.backlight();
  
  for(int i = 0; i<4; i++){
    servo[i].attach(servo_pin[i]);
    servo[i].write(POS0);
  }

  Serial.println("Dang kiem tra ...");
  Test();
  Serial.println("Kiem tra xong ...");
  lcd.clear();
  lcd.setCursor(6,0);
  lcd.print("Hi!");
  delay(1000);
}


void loop()
{
  ControlDC();
  if (Serial.available()) {
    s = Serial.readStringUntil('\n');
    //lcd.setCursor(14,1);
    // lcd.print(programData);
    // lcd.print(programColor);
    if(!programColor){
      received = 1;
      programData = 1;
      t1 = millis() + TO1;
    }
    
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
      lcd.setCursor(0,1);
      lcd.print(s);

      for(int i=0; i<4; i++){
        if (s == color[i]) {
          Serial.println(i);
          // xử lý 
          colorX = i;
          //servo[colorX].write(POS1); 
        }
      }
      programColor = 1;
      programData = 0;
    }
    
    if(millis() > t1){
      received = 0;
      //lcd.clear();
      LcdClear();
    }
  }

  if(programColor){
    if(!wait1 && digitalRead(sensor[colorX]) == 0){
      wait1 = 1;
      
      t2 = millis() + TO1;
      delay(1500);
      servo[colorX].write(POS1);
    }
    if(wait1 && millis()>t2){
      servo[colorX].write(POS0);
      wait1 = 0;
      wait2 = 1;
      t2 = millis() + TO2;
    }
    if(wait2 && millis()>t2){
      wait2 = 0;
      programColor = 0;
    }
  }
}
void LcdClear(){
  lcd.setCursor(0,1);
  for(int i = 0; i<16; i++)
    lcd.print(" ");
}
void ControlDC(){
  if(!digitalRead(BT1)){
    if(onDC){
      onDC = 0;
      digitalWrite(DC, LOW);
    } else {
      onDC = 1;
      digitalWrite(DC, HIGH);
    }
    while (!digitalRead(BT1));
    delay(100);
  }
}
void Test(){
  lcd.clear();
  lcd.print("Test..");
  digitalWrite(DC, HIGH);
  delay(500);
  for(int i = 0; i<4; i++){
    lcd.print(i);
    servo[i].write(POS1);
    delay(1000);
    servo[i].write(POS0);
    delay(200);
  }

  lcd.print(".");
  for(int i = 0; i<4; i++){
    while(digitalRead(sensor[i]));
    lcd.print(i);  
  }
  digitalWrite(DC, LOW);
  lcd.setCursor(0,1);
  lcd.print("OK!");
  delay(1000);
}

