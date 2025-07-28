#include <FastLED.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// LED Matrix Configuration
#define LED_PIN     26        // GPIO pin connected to the LED data line
#define MATRIX_WIDTH  16     // Number of LEDs horizontally
#define MATRIX_HEIGHT 16      // Number of LEDs vertically
#define NUM_LEDS (MATRIX_WIDTH * MATRIX_HEIGHT)
#define BRIGHTNESS  50       // LED brightness (0-255)

// Display orientation settings
#define FLIP_HORIZONTAL true  // Set to true if text appears mirror-flipped
#define FLIP_VERTICAL   false  // Set to true if text appears upside-down
#define REVERSE_SCROLL  true  // Set to true to scroll right-to-left instead
#define SERPENTINE_LAYOUT true // Set to false if your LEDs go row-by-row instead of zigzag

// Display Configuration
#define SCROLL_SPEED 100     // Milliseconds between scroll steps
#define TEXT_COLOR CRGB::Red // Text color

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Web Server Configuration
const char* serverURL = "https://your-vercel-app.vercel.app/api/message";
#define UPDATE_INTERVAL 30000  // Update message every 30 seconds

CRGB leds[NUM_LEDS];

// 5x7 font definition for basic ASCII characters
const uint8_t font5x7[96][5] = {
  {0x00, 0x00, 0x00, 0x00, 0x00}, // Space
  {0x00, 0x00, 0x5F, 0x00, 0x00}, // !
  {0x00, 0x07, 0x00, 0x07, 0x00}, // "
  {0x14, 0x7F, 0x14, 0x7F, 0x14}, // #
  {0x24, 0x2A, 0x7F, 0x2A, 0x12}, // $
  {0x23, 0x13, 0x08, 0x64, 0x62}, // %
  {0x36, 0x49, 0x56, 0x20, 0x50}, // &
  {0x00, 0x08, 0x07, 0x03, 0x00}, // '
  {0x00, 0x1C, 0x22, 0x41, 0x00}, // (
  {0x00, 0x41, 0x22, 0x1C, 0x00}, // )
  {0x2A, 0x1C, 0x7F, 0x1C, 0x2A}, // *
  {0x08, 0x08, 0x3E, 0x08, 0x08}, // +
  {0x00, 0x80, 0x70, 0x30, 0x00}, // ,
  {0x08, 0x08, 0x08, 0x08, 0x08}, // -
  {0x00, 0x00, 0x60, 0x60, 0x00}, // .
  {0x20, 0x10, 0x08, 0x04, 0x02}, // /
  {0x3E, 0x51, 0x49, 0x45, 0x3E}, // 0
  {0x00, 0x42, 0x7F, 0x40, 0x00}, // 1
  {0x72, 0x49, 0x49, 0x49, 0x46}, // 2
  {0x21, 0x41, 0x49, 0x4D, 0x33}, // 3
  {0x18, 0x14, 0x12, 0x7F, 0x10}, // 4
  {0x27, 0x45, 0x45, 0x45, 0x39}, // 5
  {0x3C, 0x4A, 0x49, 0x49, 0x31}, // 6
  {0x41, 0x21, 0x11, 0x09, 0x07}, // 7
  {0x36, 0x49, 0x49, 0x49, 0x36}, // 8
  {0x46, 0x49, 0x49, 0x29, 0x1E}, // 9
  {0x00, 0x00, 0x14, 0x00, 0x00}, // :
  {0x00, 0x40, 0x34, 0x00, 0x00}, // ;
  {0x00, 0x08, 0x14, 0x22, 0x41}, // <
  {0x14, 0x14, 0x14, 0x14, 0x14}, // =
  {0x00, 0x41, 0x22, 0x14, 0x08}, // >
  {0x02, 0x01, 0x59, 0x09, 0x06}, // ?
  {0x3E, 0x41, 0x5D, 0x59, 0x4E}, // @
  {0x7C, 0x12, 0x11, 0x12, 0x7C}, // A
  {0x7F, 0x49, 0x49, 0x49, 0x36}, // B
  {0x3E, 0x41, 0x41, 0x41, 0x22}, // C
  {0x7F, 0x41, 0x41, 0x41, 0x3E}, // D
  {0x7F, 0x49, 0x49, 0x49, 0x41}, // E
  {0x7F, 0x09, 0x09, 0x09, 0x01}, // F
  {0x3E, 0x41, 0x41, 0x51, 0x73}, // G
  {0x7F, 0x08, 0x08, 0x08, 0x7F}, // H
  {0x00, 0x41, 0x7F, 0x41, 0x00}, // I
  {0x20, 0x40, 0x41, 0x3F, 0x01}, // J
  {0x7F, 0x08, 0x14, 0x22, 0x41}, // K
  {0x7F, 0x40, 0x40, 0x40, 0x40}, // L
  {0x7F, 0x02, 0x1C, 0x02, 0x7F}, // M
  {0x7F, 0x04, 0x08, 0x10, 0x7F}, // N
  {0x3E, 0x41, 0x41, 0x41, 0x3E}, // O
  {0x7F, 0x09, 0x09, 0x09, 0x06}, // P
  {0x3E, 0x41, 0x51, 0x21, 0x5E}, // Q
  {0x7F, 0x09, 0x19, 0x29, 0x46}, // R
  {0x26, 0x49, 0x49, 0x49, 0x32}, // S
  {0x03, 0x01, 0x7F, 0x01, 0x03}, // T
  {0x3F, 0x40, 0x40, 0x40, 0x3F}, // U
  {0x1F, 0x20, 0x40, 0x20, 0x1F}, // V
  {0x3F, 0x40, 0x38, 0x40, 0x3F}, // W
  {0x63, 0x14, 0x08, 0x14, 0x63}, // X
  {0x03, 0x04, 0x78, 0x04, 0x03}, // Y
  {0x61, 0x59, 0x49, 0x4D, 0x43}, // Z
  {0x00, 0x7F, 0x41, 0x41, 0x41}, // [
  {0x02, 0x04, 0x08, 0x10, 0x20}, // backslash
  {0x41, 0x41, 0x41, 0x7F, 0x00}, // ]
  {0x04, 0x02, 0x01, 0x02, 0x04}, // ^
  {0x40, 0x40, 0x40, 0x40, 0x40}, // _
  {0x00, 0x03, 0x07, 0x08, 0x00}, // `
  {0x20, 0x54, 0x54, 0x78, 0x40}, // a
  {0x7F, 0x28, 0x44, 0x44, 0x38}, // b
  {0x38, 0x44, 0x44, 0x44, 0x28}, // c
  {0x38, 0x44, 0x44, 0x28, 0x7F}, // d
  {0x38, 0x54, 0x54, 0x54, 0x18}, // e
  {0x00, 0x08, 0x7E, 0x09, 0x02}, // f
  {0x18, 0xA4, 0xA4, 0x9C, 0x78}, // g
  {0x7F, 0x08, 0x04, 0x04, 0x78}, // h
  {0x00, 0x44, 0x7D, 0x40, 0x00}, // i
  {0x20, 0x40, 0x40, 0x3D, 0x00}, // j
  {0x7F, 0x10, 0x28, 0x44, 0x00}, // k
  {0x00, 0x41, 0x7F, 0x40, 0x00}, // l
  {0x7C, 0x04, 0x78, 0x04, 0x78}, // m
  {0x7C, 0x08, 0x04, 0x04, 0x78}, // n
  {0x38, 0x44, 0x44, 0x44, 0x38}, // o
  {0xFC, 0x18, 0x24, 0x24, 0x18}, // p
  {0x18, 0x24, 0x24, 0x18, 0xFC}, // q
  {0x7C, 0x08, 0x04, 0x04, 0x08}, // r
  {0x48, 0x54, 0x54, 0x54, 0x24}, // s
  {0x04, 0x04, 0x3F, 0x44, 0x24}, // t
  {0x3C, 0x40, 0x40, 0x20, 0x7C}, // u
  {0x1C, 0x20, 0x40, 0x20, 0x1C}, // v
  {0x3C, 0x40, 0x30, 0x40, 0x3C}, // w
  {0x44, 0x28, 0x10, 0x28, 0x44}, // x
  {0x4C, 0x90, 0x90, 0x90, 0x7C}, // y
  {0x44, 0x64, 0x54, 0x4C, 0x44}, // z
  {0x00, 0x08, 0x36, 0x41, 0x00}, // {
  {0x00, 0x00, 0x77, 0x00, 0x00}, // |
  {0x00, 0x41, 0x36, 0x08, 0x00}, // }
  {0x02, 0x01, 0x02, 0x04, 0x02}, // ~
  {0x3C, 0x26, 0x23, 0x26, 0x3C}  // DEL
};

String message = "CONNECTING... ";
int scrollPosition = 0;
unsigned long lastScrollTime = 0;
unsigned long lastUpdateTime = 0;

// Convert XY coordinates to LED index
int XY(int x, int y) {
  // Apply horizontal flip if needed
  if (FLIP_HORIZONTAL) {
    x = MATRIX_WIDTH - 1 - x;
  }
  
  // Apply vertical flip if needed
  if (FLIP_VERTICAL) {
    y = MATRIX_HEIGHT - 1 - y;
  }
  
  if (SERPENTINE_LAYOUT) {
    // Serpentine layout (zigzag)
    if (y & 0x01) {
      // Odd rows run backwards
      return (y + 1) * MATRIX_WIDTH - 1 - x;
    } else {
      // Even rows run forwards
      return y * MATRIX_WIDTH + x;
    }
  } else {
    // Simple row-by-row layout
    return y * MATRIX_WIDTH + x;
  }
}

// Draw a character at the specified position
void drawChar(int x, int y, char c, CRGB color) {
  if (c < 32 || c > 127) return; // Skip non-printable characters
  
  int charIndex = c - 32;
  
  for (int col = 0; col < 5; col++) {
    uint8_t columnData = font5x7[charIndex][col];
    
    for (int row = 0; row < 7; row++) {
      if (columnData & (1 << row)) {
        int pixelX = x + col;
        int pixelY = y + row;
        
        // Check bounds
        if (pixelX >= 0 && pixelX < MATRIX_WIDTH && pixelY >= 0 && pixelY < MATRIX_HEIGHT) {
          leds[XY(pixelX, pixelY)] = color;
        }
      }
    }
  }
}

// Draw text string
void drawText(int x, int y, String text, CRGB color) {
  int currentX = x;
  
  for (int i = 0; i < text.length(); i++) {
    drawChar(currentX, y, text[i], color);
    currentX += 6; // 5 pixels for char + 1 pixel spacing
  }
}

// Get text width in pixels
int getTextWidth(String text) {
  return text.length() * 6 - 1; // 6 pixels per char minus 1 for last spacing
}

// Scroll text across the display
void scrollText() {
  // Clear display
  FastLED.clear();
  
  // Draw text at current scroll position
  if (REVERSE_SCROLL) {
    // Scroll from left to right
    drawText(scrollPosition - getTextWidth(message), 0, message, TEXT_COLOR);
  } else {
    // Scroll from right to left (default)
    drawText(-scrollPosition, 0, message, TEXT_COLOR);
  }
  
  // Update display
  FastLED.show();
  
  // Move scroll position
  scrollPosition++;
  
  // Reset scroll position when text has completely scrolled off
  int textWidth = getTextWidth(message);
  if (scrollPosition > textWidth + MATRIX_WIDTH) {
    scrollPosition = 0;
  }
}

// Connect to WiFi
void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  message = "WIFI CONNECTED! ";
  scrollPosition = 0;
}

// Fetch message from web server
void fetchMessage() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return;
  }
  
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("HTTP Response: " + response);
    
    // Parse JSON response
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, response);
    
    if (doc.containsKey("message")) {
      String newMessage = doc["message"].as<String>();
      if (newMessage != message) {
        message = newMessage + " ";
        scrollPosition = 0;
        Serial.println("New message received: " + message);
      }
    }
  } else {
    Serial.println("Error in HTTP request: " + String(httpResponseCode));
  }
  
  http.end();
}

void setup() {
  Serial.begin(115200);
  Serial.println("WS2812B LED Matrix Display Starting...");
  
  // Initialize FastLED
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear();
  FastLED.show();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Fetch initial message
  fetchMessage();
  
  Serial.println("Ready to display message!");
}

void loop() {
  // Check if it's time to scroll
  if (millis() - lastScrollTime >= SCROLL_SPEED) {
    lastScrollTime = millis();
    scrollText();
  }
  
  // Check if it's time to update message from server
  if (millis() - lastUpdateTime >= UPDATE_INTERVAL) {
    lastUpdateTime = millis();
    fetchMessage();
  }
  
  // Keep WiFi connection alive
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    connectToWiFi();
  }
  
  // You can still add Serial input handling here to change the message manually
  if (Serial.available()) {
    message = Serial.readStringUntil('\n');
    message += " "; // Add space for better scrolling
    scrollPosition = 0; // Reset scroll position
    Serial.println("Manual message: " + message);
  }
}