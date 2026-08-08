# Stream-Deck
Fully DIY Stream Deck with python &amp; Arduino

# DIY Stream Deck with Auto-Handshake & OBS Integration

A fully custom, low-cost **DIY Stream Deck** powered by a microcontroller (ESP32/ESP32-S3/RP2040) and a Python background daemon. 

Unlike basic USB keyboard emulators, this system uses bidirectional **USB Serial communication** combined with an **intelligent handshake protocol** to automatically discover the device, control local applications (like Spotify), and interact directly with **OBS Studio** via WebSockets.

---

## 🚀 Features

* **Dynamic Port Detection (No Hardcoded COM Ports):** The Python daemon automatically scans and handshakes with connected serial ports. If you unplug the device, change USB ports, or restart your PC, it reconnects seamlessly without crashing.
* **OBS Studio Integration:** Control scene switching and microphone mute states via `obs-websocket`.
* **Application Automation:** Launch or control apps like Spotify and local scripts with a single button press.
* **Internal Pull-Up Logic:** Simple and safe hardware wiring requiring zero external resistors.

---

## 🛠️ Hardware Requirements & Components

### 1. Components List
* **Microcontroller:** ESP32-S3 (recommended due to native USB support), Raspberry Pi Pico, or Arduino Pro Micro (ATmega32u4).
* **Buttons:** 4x Momentary push buttons (tactile switches or mechanical keyboard switches like Cherry MX).
* **Breadboard & Wires:** Dupont jumper wires (Male-to-Male / Male-to-Female) and a standard breadboard.
* **USB Cable:** A high-quality **data** USB cable (ensure it's not a power-only cable).

### 2. Wiring & Pinout Guide
The firmware utilizes internal pull-up resistors (`INPUT_PULLUP`), meaning the digital pins remain **HIGH** by default and drop to **LOW** when pressed (connected to ground).

| Component / Button | Signal Pin (Microcontroller) | Ground Pin (GND) |
| :--- | :--- | :--- |
| **Button 1** (Spotify) | GPIO **4** | Common **GND** bus |
| **Button 2** (Mic Mute) | GPIO **5** | Common **GND** bus |
| **Button 3** (OBS Scene) | GPIO **6** | Common **GND** bus |
| **Button 4** (Launch App) | GPIO **7** | Common **GND** bus |

#### Step-by-Step Wiring:
1. Plug your microcontroller into the breadboard and connect it to your PC via USB.
2. Place your 4 push buttons on the breadboard.
3. Connect one side of each button to its respective GPIO pin (`4`, `5`, `6`, `7`).
4. Connect the other side of all buttons together onto a shared common ground line, and wire that line directly to any **GND** pin on the microcontroller.

---

## 💻 Software Setup

### Step 1: Install Python Dependencies
Make sure you have Python installed, then run the following command in your terminal to install the required libraries for serial communication and OBS integration:

```bash
pip install pyserial obs-websocket-py
