/*
 * Quick ESP32 Test - White at 10% Brightness
 * Tests 4x 16x16 LED panels (1024 total LEDs)
 * Upload this to verify your hardware is working
 */

#include <FastLED.h>

// Configuration
#define LED_PIN     18        // GPIO pin connected to LED data line
#define NUM_LEDS    1024      // 4 panels × 16×16 = 1024 LEDs
#define BRIGHTNESS  10        // 10% brightness (255 × 0.1 = 25.5)

// LED array
CRGB leds[NUM_LEDS];

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("ESP32 LED Test Starting...");
  Serial.println("Configuration:");
  Serial.print("  LEDs: ");
  Serial.println(NUM_LEDS);
  Serial.print("  Pin: GPIO ");
  Serial.println(LED_PIN);
  Serial.print("  Brightness: ");
  Serial.println(BRIGHTNESS);

  // Initialize FastLED
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);

  Serial.println("FastLED initialized");

  // Set all LEDs to white
  fill_solid(leds, NUM_LEDS, CRGB::White);
  FastLED.show();

  Serial.println("All LEDs set to WHITE at 10% brightness");
  Serial.println("Test complete!");
}

void loop() {
  // Nothing to do - LEDs stay white
  delay(1000);
}
