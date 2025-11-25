// T6600 Stepper Driver Test
// Arduino Uno
// Direction: Pin 2
// Pulse: Pin 3

const int dirPin = 2;   // Direction pin
const int pulsePin = 3;  // Pulse Pin

// Ajustable parameters
const long pulsesPerRev = 1600;  // change if your microstepping setting changes
int pulseDelay = 200;            // Microseconds between pulses (speed control)

void setup() {
  pinMode(dirPin, OUTPUT);
  pinMode(pulsePin, OUTPUT);

  digitalWrite(dirPin, LOW); // Default direction
}


void loop() {
  // Rotate clockwise one revolution
  digitalWrite(dirPin, LOW); // Corrected: Added comma
  for (long i = 0; i < pulsesPerRev; i++) { // Corrected: Variable name
    digitalWrite(pulsePin, HIGH);
    delayMicroseconds(pulseDelay);
    digitalWrite(pulsePin, LOW);
    delayMicroseconds(pulseDelay);
  }
  delay(500);  // pause

  // Rotate counterclockwise one revolution
  digitalWrite(dirPin, HIGH);
  for (long i = 0; i < pulsesPerRev; i++) {
    digitalWrite(pulsePin, HIGH);
    delayMicroseconds(pulseDelay);
    digitalWrite(pulsePin, LOW);
    delayMicroseconds(pulseDelay);
  }

  delay(500);    // pause
}
