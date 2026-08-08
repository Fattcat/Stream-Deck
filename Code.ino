#include <Arduino.h>

// Definícia pinov, na ktorých sú pripojené tlačidlá (upravte podľa vlastného zapojenia)
const int buttonPins[] = {4, 5, 6, 7};

// Príkazy, ktoré sa pošlú cez USB Serial pri stlačení príslušného tlačidla
const char* buttonCommands[] = {
  "CMD_SPOTIFY", 
  "CMD_MIC_MUTE", 
  "CMD_OBS_SCENE2", 
  "CMD_LAUNCH_APP"
};

const int numButtons = 4;

// Uchovávanie predchádzajúceho stavu pre detekciu stlačenia a ošetrenie zákmisu (debounce)
bool lastState[4] = {HIGH, HIGH, HIGH, HIGH};
unsigned long lastDebounceTime[4] = {0, 0, 0, 0};
const unsigned long debounceDelay = 50; // milisekundy

void setup() {
  // Inicializácia sériovej komunikácie (rýchlosť musí sedieť s Pythonom)
  Serial.begin(115200);
  
  // Počkanie na otvorenie sériového portu (užitočné pre dosky s natívnym USB ako ESP32-S3 / RP2040)
  while (!Serial) {
    delay(10);
  }

  // Nastavenie pinov ako vstupy s vnútorným pull-up rezistorom (tlačidlo spína na GND)
  for (int i = 0; i < numButtons; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
  }
}

void loop() {
  // 1. Spracovanie požiadaviek na identifikáciu od Pythonu (Handshake)
  if (Serial.available() > 0) {
    String incoming = Serial.readStringUntil('\n');
    incoming.trim();
    
    // Ak sa Python opýta "Kto si?", mikrokontrolér odpovie dohodnutým heslom
    if (incoming == "WHO_ARE_YOU") {
      Serial.println("STREAM_DECK_OK");
    }
  }

  // 2. Čítanie fyzických tlačidiel
  for (int i = 0; i < numButtons; i++) {
    bool currentState = digitalRead(buttonPins[i]);

    // Ak sa stav tlačidla zmenil
    if (currentState != lastState[i]) {
      // Skontrolujeme debounce limit
      if (millis() - lastDebounceTime[i] > debounceDelay) {
        lastDebounceTime[i] = millis();

        // Pri zapojenom INPUT_PULLUP znamená LOW stlačenie tlačidla
        if (currentState == LOW) {
          Serial.println(buttonCommands[i]);
        }
      }
    }
    lastState[i] = currentState;
  }
}
