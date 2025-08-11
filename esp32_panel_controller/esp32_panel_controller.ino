/*
 * ESP32 Panel Controller Firmware
 * 
 * Clean, simple firmware designed to work with the Python PanelController system.
 * Receives RGB frame data via serial and displays on LED matrix.
 * 
 * Supports dynamic display sizing and provides reliable serial communication.
 */

#include <FastLED.h>

// Hardware Configuration
#define LED_PIN           26        // GPIO pin for LED data
#define MAX_LEDS          2048      // Maximum LEDs supported (64x32)
#define DEFAULT_BRIGHTNESS 50       // Default brightness (0-255)

// Default Display Configuration  
#define DEFAULT_WIDTH     32        // Default display width
#define DEFAULT_HEIGHT    32        // Default display height

// LED Strip Configuration
#define FLIP_HORIZONTAL   false     // Flip display horizontally if needed
#define FLIP_VERTICAL     false     // Flip display vertically if needed  
#define SERPENTINE_LAYOUT true      // True for zigzag wiring, false for row-by-row

// Global Variables
int display_width = DEFAULT_WIDTH;
int display_height = DEFAULT_HEIGHT;
int num_leds = DEFAULT_WIDTH * DEFAULT_HEIGHT;
int current_brightness = DEFAULT_BRIGHTNESS;

CRGB leds[MAX_LEDS];
uint8_t* frame_buffer = nullptr;
bool frame_ready = false;
bool display_configured = false;

// Serial Communication State
enum ParseState {
  WAITING_FOR_COMMAND,
  RECEIVING_FRAME_DATA
};

ParseState parse_state = WAITING_FOR_COMMAND;
String command_buffer = "";
int expected_frame_size = 0;
int received_frame_bytes = 0;

/*
 * Initialize frame buffer for current display size
 */
bool allocate_frame_buffer() {
  // Free existing buffer
  if (frame_buffer != nullptr) {
    free(frame_buffer);
    frame_buffer = nullptr;
  }
  
  // Calculate required size
  size_t buffer_size = num_leds * 3;
  
  // Allocate new buffer
  frame_buffer = (uint8_t*)malloc(buffer_size);
  
  if (frame_buffer == nullptr) {
    Serial.println("ERROR: Failed to allocate frame buffer");
    display_configured = false;
    return false;
  }
  
  // Initialize to black
  memset(frame_buffer, 0, buffer_size);
  display_configured = true;
  
  Serial.print("BUFFER_ALLOCATED: ");
  Serial.print(buffer_size);
  Serial.println(" bytes");
  
  return true;
}

/*
 * Convert X,Y coordinates to LED strip index
 */
int xy_to_index(int x, int y) {
  // Bounds check
  if (x < 0 || x >= display_width || y < 0 || y >= display_height) {
    return -1;
  }
  
  // Apply orientation flips
  if (FLIP_HORIZONTAL) {
    x = display_width - 1 - x;
  }
  if (FLIP_VERTICAL) {
    y = display_height - 1 - y;
  }
  
  // Calculate index based on layout
  if (SERPENTINE_LAYOUT) {
    // Zigzag pattern - odd rows run backwards
    if (y % 2 == 0) {
      // Even rows: left to right
      return y * display_width + x;
    } else {
      // Odd rows: right to left
      return y * display_width + (display_width - 1 - x);
    }
  } else {
    // Simple row-by-row pattern
    return y * display_width + x;
  }
}

/*
 * Configure display dimensions
 */
bool configure_display(int width, int height) {
  // Validate dimensions
  if (width <= 0 || height <= 0) {
    Serial.println("CONFIG_ERROR: Invalid dimensions");
    return false;
  }
  
  int total_leds = width * height;
  if (total_leds > MAX_LEDS) {
    Serial.print("CONFIG_ERROR: Too many LEDs. Max: ");
    Serial.println(MAX_LEDS);
    return false;
  }
  
  // Update configuration
  display_width = width;
  display_height = height;
  num_leds = total_leds;
  
  // Reallocate frame buffer
  if (!allocate_frame_buffer()) {
    return false;
  }
  
  // Clear display
  FastLED.clear();
  FastLED.show();
  
  Serial.print("CONFIG_OK: ");
  Serial.print(width);
  Serial.print("x");
  Serial.print(height);
  Serial.print(" (");
  Serial.print(total_leds);
  Serial.println(" LEDs)");
  
  return true;
}

/*
 * Display current frame buffer on LEDs
 */
void display_frame() {
  if (!display_configured || frame_buffer == nullptr || !frame_ready) {
    return;
  }
  
  // Copy frame buffer to LED array
  for (int i = 0; i < num_leds && i < MAX_LEDS; i++) {
    leds[i] = CRGB(
      frame_buffer[i * 3],     // Red
      frame_buffer[i * 3 + 1], // Green
      frame_buffer[i * 3 + 2]  // Blue
    );
  }
  
  FastLED.show();
  frame_ready = false;
}

/*
 * Show test pattern for debugging
 */
void show_test_pattern(int pattern) {
  if (!display_configured) {
    return;
  }
  
  FastLED.clear();
  
  switch (pattern) {
    case 0: // Corner markers
      {
        int top_left = xy_to_index(0, 0);
        int top_right = xy_to_index(display_width - 1, 0);
        int bottom_left = xy_to_index(0, display_height - 1);
        int bottom_right = xy_to_index(display_width - 1, display_height - 1);
        
        if (top_left >= 0) leds[top_left] = CRGB::Red;
        if (top_right >= 0) leds[top_right] = CRGB::Green;
        if (bottom_left >= 0) leds[bottom_left] = CRGB::Blue;
        if (bottom_right >= 0) leds[bottom_right] = CRGB::Yellow;
      }
      break;
      
    case 1: // Border outline
      for (int x = 0; x < display_width; x++) {
        int top = xy_to_index(x, 0);
        int bottom = xy_to_index(x, display_height - 1);
        if (top >= 0) leds[top] = CRGB::White;
        if (bottom >= 0) leds[bottom] = CRGB::White;
      }
      for (int y = 0; y < display_height; y++) {
        int left = xy_to_index(0, y);
        int right = xy_to_index(display_width - 1, y);
        if (left >= 0) leds[left] = CRGB::White;
        if (right >= 0) leds[right] = CRGB::White;
      }
      break;
      
    case 2: // Center cross
      {
        int center_x = display_width / 2;
        int center_y = display_height / 2;
        
        // Vertical line
        for (int y = 0; y < display_height; y++) {
          int idx = xy_to_index(center_x, y);
          if (idx >= 0) leds[idx] = CRGB::Cyan;
        }
        
        // Horizontal line
        for (int x = 0; x < display_width; x++) {
          int idx = xy_to_index(x, center_y);
          if (idx >= 0) leds[idx] = CRGB::Cyan;
        }
      }
      break;
      
    default: // Rainbow gradient
      for (int i = 0; i < num_leds && i < MAX_LEDS; i++) {
        leds[i] = CHSV(i * 255 / num_leds, 255, 128);
      }
      break;
  }
  
  FastLED.show();
}

/*
 * Process incoming serial data
 */
void process_serial_data() {
  while (Serial.available()) {
    char c = Serial.read();
    
    if (parse_state == WAITING_FOR_COMMAND) {
      command_buffer += c;
      
      // Check for complete commands
      if (c == '\n') {
        process_command(command_buffer);
        command_buffer = "";
      }
      // Check for frame command start
      else if (command_buffer.startsWith("FRAME:") && command_buffer.indexOf(':', 6) != -1 && c == ':') {
        // Extract frame size from FRAME:size:
        int colon_pos = command_buffer.indexOf(':', 6);
        String size_str = command_buffer.substring(6, colon_pos);
        expected_frame_size = size_str.toInt();
        
        // Validate frame size
        int required_size = num_leds * 3;
        if (expected_frame_size != required_size) {
          Serial.print("FRAME_ERROR: Size mismatch. Expected ");
          Serial.print(required_size);
          Serial.print(", got ");
          Serial.println(expected_frame_size);
          command_buffer = "";
          continue;
        }
        
        if (!display_configured || frame_buffer == nullptr) {
          Serial.println("FRAME_ERROR: Display not configured");
          command_buffer = "";
          continue;
        }
        
        // Switch to frame data reception mode
        parse_state = RECEIVING_FRAME_DATA;
        received_frame_bytes = 0;
        command_buffer = "";
      }
      // Prevent command buffer overflow
      else if (command_buffer.length() > 100) {
        Serial.println("COMMAND_ERROR: Command too long");
        command_buffer = "";
      }
    }
    else if (parse_state == RECEIVING_FRAME_DATA) {
      // Receiving binary frame data
      if (received_frame_bytes < expected_frame_size) {
        frame_buffer[received_frame_bytes] = c;
        received_frame_bytes++;
      } else {
        // Looking for :END marker
        command_buffer += c;
        if (command_buffer.endsWith(":END")) {
          // Frame complete
          frame_ready = true;
          Serial.println("FRAME_OK");
          parse_state = WAITING_FOR_COMMAND;
          command_buffer = "";
        } else if (command_buffer.length() > 10) {
          // Invalid end marker
          Serial.println("FRAME_ERROR: Invalid end marker");
          parse_state = WAITING_FOR_COMMAND;
          command_buffer = "";
        }
      }
    }
  }
}

/*
 * Process text commands
 */
void process_command(String cmd) {
  cmd.trim();
  
  if (cmd.startsWith("CONFIG:")) {
    // Parse CONFIG:width,height
    int comma_pos = cmd.indexOf(',');
    if (comma_pos == -1) {
      Serial.println("CONFIG_ERROR: Invalid format. Use CONFIG:width,height");
      return;
    }
    
    String width_str = cmd.substring(7, comma_pos);
    String height_str = cmd.substring(comma_pos + 1);
    
    int width = width_str.toInt();
    int height = height_str.toInt();
    
    configure_display(width, height);
  }
  else if (cmd.startsWith("BRIGHTNESS:")) {
    int brightness = cmd.substring(11).toInt();
    if (brightness >= 0 && brightness <= 255) {
      current_brightness = brightness;
      FastLED.setBrightness(brightness);
      FastLED.show();
      Serial.println("BRIGHTNESS_OK");
    } else {
      Serial.println("BRIGHTNESS_ERROR: Value must be 0-255");
    }
  }
  else if (cmd == "CLEAR") {
    FastLED.clear();
    FastLED.show();
    Serial.println("CLEAR_OK");
  }
  else if (cmd == "STATUS") {
    Serial.print("STATUS: ");
    Serial.print(display_width);
    Serial.print("x");
    Serial.print(display_height);
    Serial.print(" LEDs:");
    Serial.print(num_leds);
    Serial.print(" Brightness:");
    Serial.print(current_brightness);
    Serial.print(" Memory:");
    Serial.print(ESP.getFreeHeap());
    Serial.print(" Configured:");
    Serial.println(display_configured ? "YES" : "NO");
  }
  else if (cmd == "INFO") {
    Serial.println("ESP32 Panel Controller v1.0");
    Serial.println("Commands:");
    Serial.println("  CONFIG:width,height  - Configure display size");
    Serial.println("  FRAME:size:<data>:END - Send RGB frame data");
    Serial.println("  BRIGHTNESS:0-255     - Set LED brightness");
    Serial.println("  CLEAR                - Clear display");
    Serial.println("  STATUS               - Show status");
    Serial.println("  TEST:0-3             - Show test pattern");
    Serial.println("  INFO                 - Show this help");
  }
  else if (cmd.startsWith("TEST:")) {
    int pattern = cmd.substring(5).toInt();
    show_test_pattern(pattern);
    Serial.print("TEST_OK: Pattern ");
    Serial.println(pattern);
  }
  else if (cmd.length() > 0) {
    Serial.print("UNKNOWN_COMMAND: ");
    Serial.println(cmd);
  }
}

/*
 * Arduino setup function
 */
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println();
  Serial.println("=== ESP32 Panel Controller v1.0 ===");
  Serial.print("Default: ");
  Serial.print(DEFAULT_WIDTH);
  Serial.print("x");
  Serial.print(DEFAULT_HEIGHT);
  Serial.print(" (");
  Serial.print(DEFAULT_WIDTH * DEFAULT_HEIGHT);
  Serial.println(" LEDs)");
  Serial.print("Max supported: ");
  Serial.print(MAX_LEDS);
  Serial.println(" LEDs");
  Serial.print("Free memory: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");
  
  // Initialize FastLED
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, MAX_LEDS);
  FastLED.setBrightness(current_brightness);
  FastLED.clear();
  FastLED.show();
  
  // Configure default display
  if (configure_display(DEFAULT_WIDTH, DEFAULT_HEIGHT)) {
    Serial.println();
    Serial.println("=== STARTUP TEST SEQUENCE ===");
    
    // Show startup test patterns
    Serial.println("Test 0: Corner markers (R/G/B/Y)");
    show_test_pattern(0);
    delay(2000);
    
    Serial.println("Test 1: Border outline");
    show_test_pattern(1);
    delay(2000);
    
    Serial.println("Test 2: Center cross");
    show_test_pattern(2);
    delay(2000);
    
    Serial.println("Test 3: Rainbow gradient");
    show_test_pattern(3);
    delay(2000);
    
    FastLED.clear();
    FastLED.show();
    
    Serial.println("=== READY FOR COMMANDS ===");
    Serial.println("Send 'INFO' for command list");
  } else {
    Serial.println("ERROR: Failed to initialize display");
  }
  
  Serial.println();
}

/*
 * Arduino main loop
 */
void loop() {
  process_serial_data();
  display_frame();
  
  // Small delay to prevent overwhelming the system
  delayMicroseconds(100);
  
  // Keep watchdog happy
  yield();
}