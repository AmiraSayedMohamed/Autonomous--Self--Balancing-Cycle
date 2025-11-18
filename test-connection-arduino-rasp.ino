void setup() {
  Serial.begin(9600);      // Start serial at 9600 baud
  while (!Serial);         // Wait for Serial to initialize (important for Leonardo/Micro)
}

void loop() {
  // If Pi sends something
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    Serial.print("Arduino received: ");
    Serial.println(data);
  }

  // Periodic heartbeat message to Pi
  Serial.println("Arduino says hello!");
  delay(1000);
}
