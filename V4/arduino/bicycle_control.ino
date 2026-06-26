const int BACK_DIR_PIN   = 4;
const int BACK_PULSE_PIN = 5;
const int FRONT_DIR_PIN  = 2;
const int FRONT_PULSE_PIN= 3;

const long PROPULSION_DELAY = 350;   // أسرع شوية
const long STEERING_DELAY   = 2200;  // steering أبطأ

String currentCmd = "STOP";
unsigned long lastPropulse = 0;
unsigned long lastSteerPulse = 0;
bool propState = false;
bool steerState = false;

void setup() {
  pinMode(BACK_DIR_PIN, OUTPUT);
  pinMode(BACK_PULSE_PIN, OUTPUT);
  pinMode(FRONT_DIR_PIN, OUTPUT);
  pinMode(FRONT_PULSE_PIN, OUTPUT);

  Serial.begin(115200);        // ← غيرناه لـ 115200
  Serial.println("Arduino Ready");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.length() > 0) {
      currentCmd = cmd;
      Serial.println("OK:" + currentCmd);
    }
  }

  // Propulsion
  if (currentCmd == "FORWARD" || currentCmd == "LEFT" || currentCmd == "RIGHT") {
    digitalWrite(BACK_DIR_PIN, LOW);   // Forward
    pulsePropulsion();
  } 
  else if (currentCmd == "BACKWARD") {
    digitalWrite(BACK_DIR_PIN, HIGH);
    pulsePropulsion();
  }

  // Steering
  if (currentCmd == "LEFT") {
    digitalWrite(FRONT_DIR_PIN, HIGH);   // غيري HIGH/LOW لو الاتجاه معكوس
    pulseSteering();
  } 
  else if (currentCmd == "RIGHT") {
    digitalWrite(FRONT_DIR_PIN, LOW);
    pulseSteering();
  }
  // STRAIGHT / STOP → no steering pulse
}

void pulsePropulsion() {
  if (micros() - lastPropulse >= PROPULSION_DELAY) {
    propState = !propState;
    digitalWrite(BACK_PULSE_PIN, propState);
    lastPropulse = micros();
  }
}

void pulseSteering() {
  if (micros() - lastSteerPulse >= STEERING_DELAY) {
    steerState = !steerState;
    digitalWrite(FRONT_PULSE_PIN, steerState);
    lastSteerPulse = micros();
  }
}