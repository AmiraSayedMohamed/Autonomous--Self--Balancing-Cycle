// Arduino Code for Dual Motor Control (Front Steering, Back Propulsion)
// Receives commands via Serial from Raspberry Pi

const int frontDirPin = 2;   // Front motor direction
const int frontPulsePin = 3; // Front motor pulse
const int backDirPin = 4;    // Back motor direction (as requested)
const int backPulsePin = 5;  // Back motor pulse (as requested)

const long pulsesPerRev = 1600;  // Adjust based on microstepping
int pulseDelay = 200;            // Speed control (lower = faster)

void setup() {
  pinMode(frontDirPin, OUTPUT);
  pinMode(frontPulsePin, OUTPUT);
  pinMode(backDirPin, OUTPUT);
  pinMode(backPulsePin, OUTPUT);
  
  digitalWrite(frontDirPin, LOW);
  digitalWrite(backDirPin, LOW);
  
  Serial.begin(9600);  // Serial comm with Pi
  Serial.println("Arduino Ready");  // Test message
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "FORWARD") {
      driveForward();
    } else if (command == "STOP") {
      stopMotors();
    } else if (command == "LEFT") {
      turnLeft();
    } else if (command == "RIGHT") {
      turnRight();
    } else if (command == "BACKWARD") {
      driveBackward();
    }
  }
}

// Function to drive forward (back motor forward, front straight)
void driveForward() {
  digitalWrite(backDirPin, LOW);  // Forward direction
  for (long i = 0; i < pulsesPerRev; i++) {  // One rev example; loop for continuous
    digitalWrite(backPulsePin, HIGH);
    delayMicroseconds(pulseDelay);
    digitalWrite(backPulsePin, LOW);
    delayMicroseconds(pulseDelay);
  }
  // Add loop for continuous forward if needed
}

// Function to drive backward
void driveBackward() {
  digitalWrite(backDirPin, HIGH);  // Backward direction
  for (long i = 0; i < pulsesPerRev; i++) {
    digitalWrite(backPulsePin, HIGH);
    delayMicroseconds(pulseDelay);
    digitalWrite(backPulsePin, LOW);
    delayMicroseconds(pulseDelay);
  }
}

// Function to stop both motors
void stopMotors() {
  // No pulses = stop (steppers hold position)
  delay(1000);  // Pause
}

// Function to turn left (front motor counterclockwise, then forward briefly)
void turnLeft() {
  digitalWrite(frontDirPin, HIGH);  // Counterclockwise for left (adjust if needed)
  for (long i = 0; i < pulsesPerRev / 4; i++) {  // 90 degrees turn; adjust
    digitalWrite(frontPulsePin, HIGH);
    delayMicroseconds(pulseDelay);
    digitalWrite(frontPulsePin, LOW);
    delayMicroseconds(pulseDelay);
  }
  driveForward();  // Move forward after turn
  resetSteering(); // Straighten front
}

// Function to turn right (front motor clockwise)
void turnRight() {
  digitalWrite(frontDirPin, LOW);  // Clockwise for right
  for (long i = 0; i < pulsesPerRev / 4; i++) {
    digitalWrite(frontPulsePin, HIGH);
    delayMicroseconds(pulseDelay);
    digitalWrite(frontPulsePin, LOW);
    delayMicroseconds(pulseDelay);
  }
  driveForward();  // Move forward after turn
  resetSteering(); // Straighten front
}

// Reset front steering to straight (reverse turn slightly if needed)
void resetSteering() {
  // Implement if steering doesn't self-center; e.g., small reverse pulses
}
