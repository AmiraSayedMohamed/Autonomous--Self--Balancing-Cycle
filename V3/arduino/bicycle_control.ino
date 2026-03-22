// FINAL Arduino Code for Bicycle – Fixed + Dashboard Ready
const int BACK_DIR_PIN   = 4;   // Propulsion motor direction
const int BACK_PULSE_PIN = 5;   // Propulsion motor pulse
const int FRONT_DIR_PIN  = 2;   // Steering motor direction
const int FRONT_PULSE_PIN= 3;   // Steering motor pulse

const long SPEED_DELAY = 400;   // Lower = faster (adjust 300-800)

String currentCmd = "STOP";

unsigned long lastBackPulse  = 0;
unsigned long lastFrontPulse = 0;
bool backState  = false;
bool frontState = false;

void setup() {
  pinMode(BACK_DIR_PIN, OUTPUT);
  pinMode(BACK_PULSE_PIN, OUTPUT);
  pinMode(FRONT_DIR_PIN, OUTPUT);
  pinMode(FRONT_PULSE_PIN, OUTPUT);

  digitalWrite(BACK_DIR_PIN, LOW);
  digitalWrite(FRONT_DIR_PIN, LOW);

  Serial.begin(9600);
  while (!Serial);
  Serial.println("Arduino Ready");
}

void loop() {
  // Read command from Flask dashboard
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.length() > 0) {
      currentCmd = (cmd == "STRAIGHT") ? "FORWARD" : cmd;  // Straight = Forward
      Serial.println("OK:" + currentCmd);
    }
  }

  // === PROPULSION MOTOR ===
  if (currentCmd == "FORWARD" || currentCmd == "LEFT" || currentCmd == "RIGHT") {
    digitalWrite(BACK_DIR_PIN, LOW);   // Forward
    pulseBack();
  }
  else if (currentCmd == "BACKWARD") {
    digitalWrite(BACK_DIR_PIN, HIGH);  // Backward
    pulseBack();
  }
  // else STOP → no pulses

  // === STEERING MOTOR ===
  if (currentCmd == "LEFT") {
    digitalWrite(FRONT_DIR_PIN, HIGH);   // Change if your motor turns the wrong way
    pulseFrontSlow();
  }
  else if (currentCmd == "RIGHT") {
    digitalWrite(FRONT_DIR_PIN, LOW);
    pulseFrontSlow();
  }
  // When STRAIGHT/FORWARD/BACKWARD/STOP → no steering pulses (holds position)
}

void pulseBack() {
  if (micros() - lastBackPulse >= SPEED_DELAY) {
    backState = !backState;
    digitalWrite(BACK_PULSE_PIN, backState);
    lastBackPulse = micros();
  }
}

void pulseFrontSlow() {
  if (micros() - lastFrontPulse >= SPEED_DELAY * 6) {  // 6× slower steering
    frontState = !frontState;
    digitalWrite(FRONT_PULSE_PIN, frontState);
    lastFrontPulse = micros();
  }
}