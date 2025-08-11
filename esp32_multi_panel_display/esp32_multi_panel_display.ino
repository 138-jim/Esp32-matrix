#include <FastLED.h>

// LED Matrix Configuration - Now Dynamic
#define LED_PIN     26        // GPIO pin connected to the LED data line
#define MAX_LEDS    2048      // Maximum supported LEDs (e.g., 64x32 or 32x64)
#define DEFAULT_BRIGHTNESS  50        // Default LED brightness (0-255)

// Default configuration - supports single 32x32 panel or 4x 16x16 panels in 2x2 grid
#define DEFAULT_WIDTH  32
#define DEFAULT_HEIGHT 32

// Display orientation settings for your specific LED panel wiring
#define FLIP_HORIZONTAL true  // Set to true if text appears mirror-flipped
#define FLIP_VERTICAL   false // Set to true if text appears upside-down
#define SERPENTINE_LAYOUT true // Set to false if your LEDs go row-by-row instead of zigzag

// NOTE: For 4x 16x16 panels in 2x2 grid:
// - All 1024 LEDs should be connected in a single data chain
// - The Python controller handles the logical panel mapping
// - This code treats it as one continuous 32x32 matrix

// Dynamic configuration variables
int MATRIX_WIDTH = DEFAULT_WIDTH;
int MATRIX_HEIGHT = DEFAULT_HEIGHT;
int NUM_LEDS = DEFAULT_WIDTH * DEFAULT_HEIGHT;
int current_brightness = DEFAULT_BRIGHTNESS;

CRGB leds[MAX_LEDS];

// Frame buffer for incoming data - now dynamic
uint8_t* frameBuffer = nullptr;
bool newFrameReady = false;
bool configurationValid = true;

// Configuration state
struct PanelConfig {
  int total_width;
  int total_height;
  int total_leds;
  bool configured;
} panelConfig = {DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_WIDTH * DEFAULT_HEIGHT, true};

// Memory management
void allocateFrameBuffer() {
  // Free existing buffer
  if (frameBuffer != nullptr) {
    free(frameBuffer);
    frameBuffer = nullptr;
  }
  
  // Allocate new buffer
  size_t bufferSize = NUM_LEDS * 3;
  frameBuffer = (uint8_t*)malloc(bufferSize);
  
  if (frameBuffer == nullptr) {
    Serial.println("ERROR: Failed to allocate frame buffer memory");
    configurationValid = false;
  } else {
    // Initialize buffer to black
    memset(frameBuffer, 0, bufferSize);
    configurationValid = true;
    Serial.print("Frame buffer allocated: ");
    Serial.print(bufferSize);
    Serial.println(" bytes");
  }
}

// Convert XY coordinates to LED index with dynamic dimensions
int XY(int x, int y) {
  // Bounds check
  if (x < 0 || x >= MATRIX_WIDTH || y < 0 || y >= MATRIX_HEIGHT) {
    return -1; // Invalid position
  }
  
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

// Parse configuration command: CONFIG:width,height
void parseConfigCommand(String command) {
  int commaIndex = command.indexOf(',');
  if (commaIndex == -1) {
    Serial.println("CONFIG_ERROR: Invalid format. Use CONFIG:width,height");
    return;
  }
  
  String widthStr = command.substring(7, commaIndex); // After "CONFIG:"
  String heightStr = command.substring(commaIndex + 1);
  
  int newWidth = widthStr.toInt();
  int newHeight = heightStr.toInt();
  
  // Validate dimensions
  if (newWidth <= 0 || newHeight <= 0) {
    Serial.println("CONFIG_ERROR: Invalid dimensions");
    return;
  }
  
  int newNumLeds = newWidth * newHeight;
  if (newNumLeds > MAX_LEDS) {
    Serial.print("CONFIG_ERROR: Too many LEDs. Max: ");
    Serial.println(MAX_LEDS);
    return;
  }
  
  // Update configuration
  MATRIX_WIDTH = newWidth;
  MATRIX_HEIGHT = newHeight;
  NUM_LEDS = newNumLeds;
  
  panelConfig.total_width = newWidth;
  panelConfig.total_height = newHeight;
  panelConfig.total_leds = newNumLeds;
  panelConfig.configured = true;
  
  // Reallocate frame buffer
  allocateFrameBuffer();
  
  if (configurationValid) {
    // Clear current display
    FastLED.clear();
    FastLED.show();
    
    Serial.print("CONFIG_OK: ");
    Serial.print(newWidth);
    Serial.print("x");
    Serial.print(newHeight);
    Serial.print(" (");
    Serial.print(newNumLeds);
    Serial.println(" LEDs)");
  }
}

// Enhanced protocol parser with variable frame sizes
void parseSerialData() {
  static String inputBuffer = "";
  
  while (Serial.available()) {
    char c = Serial.read();
    inputBuffer += c;
    
    // Check for configuration command
    if (inputBuffer.startsWith("CONFIG:") && c == '\n') {
      parseConfigCommand(inputBuffer.substring(0, inputBuffer.length() - 1));
      inputBuffer = "";
    }
    // Check for frame command with size: FRAME:size:<data>:END
    else if (inputBuffer.startsWith("FRAME:") && inputBuffer.indexOf(":END") != -1) {
      parseFrameCommand(inputBuffer);
      inputBuffer = "";
    }
    // Handle brightness command
    else if (inputBuffer.startsWith("BRIGHTNESS:") && c == '\n') {
      int brightness = inputBuffer.substring(11).toInt();
      if (brightness >= 0 && brightness <= 255) {
        current_brightness = brightness;
        FastLED.setBrightness(brightness);
        FastLED.show();
        Serial.println("BRIGHTNESS_OK");
      } else {
        Serial.println("BRIGHTNESS_ERROR");
      }
      inputBuffer = "";
    }
    // Handle clear command
    else if (inputBuffer.startsWith("CLEAR") && c == '\n') {
      FastLED.clear();
      FastLED.show();
      Serial.println("CLEAR_OK");
      inputBuffer = "";
    }
    // Handle status request
    else if (inputBuffer.startsWith("STATUS") && c == '\n') {
      Serial.print("STATUS: ");
      Serial.print(MATRIX_WIDTH);
      Serial.print("x");
      Serial.print(MATRIX_HEIGHT);
      Serial.print(" LEDs:");
      Serial.print(NUM_LEDS);
      Serial.print(" Brightness:");
      Serial.print(current_brightness);
      Serial.print(" Memory:");
      Serial.print(ESP.getFreeHeap());
      Serial.println();
      inputBuffer = "";
    }
    // Handle info request
    else if (inputBuffer.startsWith("INFO") && c == '\n') {
      Serial.println("ESP32 Multi-Panel LED Matrix Display");
      Serial.println("Commands:");
      Serial.println("  CONFIG:width,height - Configure display size");
      Serial.println("  FRAME:size:<data>:END - Send frame data");
      Serial.println("  BRIGHTNESS:0-255 - Set brightness");
      Serial.println("  CLEAR - Clear display");
      Serial.println("  STATUS - Show current status");
      Serial.println("  INFO - Show this help");
      inputBuffer = "";
    }
    // Reset buffer if it gets too long (prevents memory issues)
    else if (inputBuffer.length() > NUM_LEDS * 3 + 50) {
      Serial.println("BUFFER_ERROR: Command too long");
      inputBuffer = "";
    }
  }
}

// Parse frame command with variable size
void parseFrameCommand(String command) {
  if (!configurationValid || frameBuffer == nullptr) {
    Serial.println("FRAME_ERROR: Not configured or memory allocation failed");
    return;
  }
  
  // Find the size parameter: FRAME:size:<data>:END
  int firstColon = command.indexOf(':', 6); // After "FRAME:"
  int secondColon = command.indexOf(':', firstColon + 1);
  int endPos = command.lastIndexOf(":END");
  
  if (firstColon == -1 || secondColon == -1 || endPos == -1) {
    Serial.println("FRAME_ERROR: Invalid format. Use FRAME:size:<data>:END");
    return;
  }
  
  // Extract size
  String sizeStr = command.substring(6, firstColon);
  int expectedSize = sizeStr.toInt();
  
  // Validate size
  int requiredSize = NUM_LEDS * 3;
  if (expectedSize != requiredSize) {
    Serial.print("FRAME_ERROR: Size mismatch. Expected:");
    Serial.print(requiredSize);
    Serial.print(" Got:");
    Serial.println(expectedSize);
    return;
  }
  
  // Extract data
  int dataStart = secondColon + 1;
  int dataLength = endPos - dataStart;
  
  if (dataLength != expectedSize) {
    Serial.print("FRAME_ERROR: Data length mismatch. Expected:");
    Serial.print(expectedSize);
    Serial.print(" Got:");
    Serial.println(dataLength);
    return;
  }
  
  // Copy RGB data to frame buffer
  for (int i = 0; i < dataLength; i++) {
    frameBuffer[i] = command[dataStart + i];
  }
  
  newFrameReady = true;
  Serial.println("FRAME_OK");
}

void displayFrame() {
  if (!newFrameReady || !configurationValid || frameBuffer == nullptr) {
    return;
  }
  
  // Convert frame buffer to LED array
  for (int i = 0; i < NUM_LEDS; i++) {
    if (i < MAX_LEDS) {  // Safety check
      leds[i] = CRGB(
        frameBuffer[i * 3],     // R
        frameBuffer[i * 3 + 1], // G
        frameBuffer[i * 3 + 2]  // B
      );
    }
  }
  
  FastLED.show();
  newFrameReady = false;
}

// Test pattern functions
void showTestPattern(int pattern = 0) {
  FastLED.clear();
  
  switch (pattern) {
    case 0: // Rainbow gradient
      for (int i = 0; i < NUM_LEDS && i < MAX_LEDS; i++) {
        leds[i] = CHSV(i * 255 / NUM_LEDS, 255, 128);
      }
      break;
      
    case 1: // Checkerboard
      for (int y = 0; y < MATRIX_HEIGHT; y++) {
        for (int x = 0; x < MATRIX_WIDTH; x++) {
          int ledIndex = XY(x, y);
          if (ledIndex >= 0 && ledIndex < MAX_LEDS) {
            if ((x + y) % 2 == 0) {
              leds[ledIndex] = CRGB::Red;
            } else {
              leds[ledIndex] = CRGB::Blue;
            }
          }
        }
      }
      break;
      
    case 2: // Border
      for (int y = 0; y < MATRIX_HEIGHT; y++) {
        for (int x = 0; x < MATRIX_WIDTH; x++) {
          int ledIndex = XY(x, y);
          if (ledIndex >= 0 && ledIndex < MAX_LEDS) {
            if (x == 0 || x == MATRIX_WIDTH-1 || y == 0 || y == MATRIX_HEIGHT-1) {
              leds[ledIndex] = CRGB::White;
            }
          }
        }
      }
      break;
      
    case 3: // Center cross
      for (int y = 0; y < MATRIX_HEIGHT; y++) {
        for (int x = 0; x < MATRIX_WIDTH; x++) {
          int ledIndex = XY(x, y);
          if (ledIndex >= 0 && ledIndex < MAX_LEDS) {
            if (x == MATRIX_WIDTH/2 || y == MATRIX_HEIGHT/2) {
              leds[ledIndex] = CRGB::Green;
            }
          }
        }
      }
      break;
  }
  
  FastLED.show();
}

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("ESP32 Multi-Panel Frame Display Starting...");
  
  // Initialize FastLED with maximum LED count
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, MAX_LEDS);
  FastLED.setBrightness(current_brightness);
  FastLED.clear();
  FastLED.show();
  
  // Allocate initial frame buffer
  allocateFrameBuffer();
  
  Serial.println();
  Serial.println("=== ESP32 Multi-Panel LED Matrix ===");
  Serial.print("Default size: ");
  Serial.print(MATRIX_WIDTH);
  Serial.print("x");
  Serial.print(MATRIX_HEIGHT);
  Serial.print(" (");
  Serial.print(NUM_LEDS);
  Serial.println(" LEDs)");
  Serial.print("Max supported LEDs: ");
  Serial.println(MAX_LEDS);
  Serial.print("Available memory: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");
  Serial.println();
  Serial.println("Commands:");
  Serial.println("  CONFIG:width,height - Configure display size");
  Serial.println("  FRAME:size:<data>:END - Send frame data");
  Serial.println("  BRIGHTNESS:0-255 - Set brightness");
  Serial.println("  CLEAR - Clear display");
  Serial.println("  STATUS - Show status");
  Serial.println("  INFO - Show help");
  Serial.println();
  
  // Show startup test pattern
  Serial.println("Showing startup test pattern...");
  showTestPattern(0); // Rainbow
  delay(2000);
  showTestPattern(1); // Checkerboard
  delay(2000);
  showTestPattern(2); // Border
  delay(2000);
  showTestPattern(3); // Center cross
  delay(2000);
  FastLED.clear();
  FastLED.show();
  
  Serial.println("Ready for commands and frames!");
}

void loop() {
  parseSerialData();
  displayFrame();
  
  // Small delay to prevent overwhelming the system
  delayMicroseconds(100);
  
  // Watchdog pat (prevent reset on large displays)
  yield();
}

// Error handling and diagnostics
void printMemoryInfo() {
  Serial.print("Free heap: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");
  
  Serial.print("Frame buffer size: ");
  if (frameBuffer != nullptr) {
    Serial.print(NUM_LEDS * 3);
    Serial.println(" bytes (allocated)");
  } else {
    Serial.println("Not allocated");
  }
  
  Serial.print("LED array usage: ");
  Serial.print(NUM_LEDS);
  Serial.print("/");
  Serial.println(MAX_LEDS);
}