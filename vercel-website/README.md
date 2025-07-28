# ESP32 LED Matrix Control Website

This is a Vercel-hosted website that provides an API endpoint for your ESP32 LED matrix display to fetch messages dynamically.

## Features

- REST API endpoint at `/api/message`
- Web interface to view and update messages
- CORS enabled for ESP32 requests
- Environment variable support for default messages

## Deployment

1. Install Vercel CLI: `npm i -g vercel`
2. Deploy: `vercel --prod`
3. Note your deployment URL (e.g., `https://your-app.vercel.app`)

## API Endpoints

### GET /api/message
Returns the current message for the LED display.

Response:
```json
{
  "message": "Hello from Vercel!",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### POST /api/message
Updates the message (requires database integration for persistence).

Request body:
```json
{
  "message": "New message text"
}
```

## ESP32 Configuration

Update your ESP32 code with:
1. Your WiFi credentials
2. Your Vercel deployment URL
3. Install required libraries: WiFi, HTTPClient, ArduinoJson

## Environment Variables

Set `LED_MESSAGE` in Vercel dashboard or vercel.json for the default message.