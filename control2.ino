// FINAL Arduino Code for Bicycle – Continuous Motion
const int BACK_DIR_PIN   = 4;   // Back motor direction
const int BACK_PULSE_PIN = 5;   // Back motor pulse
const int FRONT_DIR_PIN  = 2;   // Front steering direction
const int FRONT_PULSE_PIN= 3;   // Front steering pulse

const long PULSES_PER_REV = 1600;  // 1/16 microstepping → 200*16 = 3200 if different, change
int SPEED_DELAY = 400;             // 300-800 → adjust speed (lower = faster)

String currentCmd = "STOP";

// Timing variables for non-blocking pulse generation
unsigned long lastBackPulse = 0;
unsigned long lastFrontPulse = 0;
bool backState = false;
bool frontState = false;

void setup() {
  pinMode(BACK_DIR_PIN, OUTPUT);
  pinMode(BACK_PULSE_PIN, OUTPUT);
  pinMode(FRONT_DIR_PIN, OUTPUT);
  pinMode(FRONT_PULSE_PIN, OUTPUT);

  digitalWrite(BACK_DIR_PIN, LOW);   // Forward default
  digitalWrite(FRONT_DIR_PIN, LOW);

  Serial.begin(9600);
  while (!Serial); // Wait for serial
  Serial.println("Arduino Ready");
}

void loop() {
  // Read command from Raspberry Pi
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.length() > 0) {
      currentCmd = cmd;
      Serial.println("OK:" + currentCmd);  // Acknowledge
    }
  }

  // === BACK MOTOR - PROPULSION ===
  if (currentCmd == "FORWARD" || currentCmd == "LEFT" || currentCmd == "RIGHT") {
    digitalWrite(BACK_DIR_PIN, LOW);  // Forward
    pulseBack();
  }
  else if (currentCmd == "BACKWARD") {
    digitalWrite(BACK_DIR_PIN, HIGH); // Backward
    pulseBack();
  }
  else {
    // STOP → no pulses
  }

  // === FRONT MOTOR - STEERING ===
  if (currentCmd == "LEFT") {
    digitalWrite(FRONT_DIR_PIN, HIGH);   // Change if turns wrong way
    pulseFrontSlow();  // Turn slowly while moving
  }
  else if (currentCmd == "RIGHT") {
    digitalWrite(FRONT_DIR_PIN, LOW);
    pulseFrontSlow();
  }
  // When not LEFT/RIGHT → no steering pulses (wheels stay where they are)
}

void pulseBack() {
  if (micros() - lastBackPulse >= SPEED_DELAY) {
    backState = !backState;
    digitalWrite(BACK_PULSE_PIN, backState);
    lastBackPulse = micros();
  }
}

void pulseFrontSlow() {
  // Slower steering while moving
  if (micros() - lastFrontPulse >= SPEED_DELAY * 6) {  // 6× slower than drive
    frontState = !frontState;
    digitalWrite(FRONT_PULSE_PIN, frontState);
    lastFrontPulse = micros();
  }
}
