#include <Servo.h>

// Velocidad para las rectas
//        (afecta a los tres siguientes)
#define V_RR 90

// Tiempo de espera para la confirmación de
#define ESP_R 30                         // rayas
#define ESP_H 30                         // huecos
#define ESP_C 20                         // curvas

// Velocidad de salida de un bit
#define V_S 90

// Velocidad para las curvas
#define V_CC 85

// Salida en una bifurcación
//
//   Primer giro
#define V_B1 100
#define ESP_B1 700   // duración
//   Avance recto
#define V_B2 100
#define ESP_B2 450   // duración
//   Segundo giro
#define V_B3 100
//                      dura hasta encontrar la cinta

#define ENA 5
#define ENB 11

#define BITS 3  // longitud fija de las etiquetas
#define LT1 digitalRead(10)
#define LT2 digitalRead(4)
#define LT3 digitalRead(2)

Servo servoIzq;
Servo servoDer;

int pinServoDer = 9;
int pinServoIzq = 8;



void prepara() {
  pinMode(ENA, OUTPUT);
  pinMode(pinServoDer, INPUT);
  pinMode(pinServoIzq, INPUT);
  pinMode(ENB, OUTPUT);
  servoIzq.attach(pinServoIzq);
  servoDer.attach(pinServoDer);
  Serial.begin(9600);
}

void adelante() {
    servoIzq.write(0); 
    servoDer.write(180);    
}

void atras() {
      servoIzq.write(180); 
    servoDer.write(0);    
}

void izquierda() {
    servoIzq.write(180); 
    servoDer.write(180);    
}

void derecha() {
    servoIzq.write(0); 
    servoDer.write(0);    
}

void alto() {
    servoIzq.write(90); 
    servoDer.write(90);    
}


bool siguiente() {
  adelante();
  bool bit;
  bool sigo = true;
  byte lt1;
  byte lt2;
  byte lt3;
  for (int temp = 0; (temp<10) ; temp++) {
    lt1 = digitalRead(10);
    lt2 = digitalRead(4);
    lt3 = digitalRead(2);
    Serial.print(lt1);
    Serial.print(lt2);
    Serial.print(lt3);
    Serial.println("done");
    if (lt1) {
      izquierda();
    }
    else if (lt3)
      { derecha();
	Serial.println("derecha");
      }
    else if (lt2)
      {
	adelante();
	Serial.println("izquierda");
      }
    else
      {
	alto();
	Serial.println("alto");
	sigo = false;
      }

  }
  alto();
  return false;
}

void setup() {
  prepara();
  siguiente();
}

void loop()
{
  
}


