import { useState, useEffect } from 'react';

export default function Home() {
  const [currentMessage, setCurrentMessage] = useState('');
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState('');

  // Fetch current message
  const fetchCurrentMessage = async () => {
    try {
      const response = await fetch('/api/message');
      const data = await response.json();
      setCurrentMessage(data.message);
      setLastUpdated(new Date(data.timestamp).toLocaleString());
    } catch (error) {
      console.error('Error fetching message:', error);
    }
  };

  // Update message
  const updateMessage = async () => {
    if (!newMessage.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('/api/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: newMessage }),
      });
      
      if (response.ok) {
        setNewMessage('');
        fetchCurrentMessage();
      }
    } catch (error) {
      console.error('Error updating message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentMessage();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchCurrentMessage, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ 
      maxWidth: '600px', 
      margin: '0 auto', 
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>ESP32 LED Matrix Control</h1>
      
      <div style={{ 
        background: '#f5f5f5', 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h2>Current Message</h2>
        <p style={{ 
          fontSize: '18px', 
          fontWeight: 'bold',
          color: '#333'
        }}>
          "{currentMessage}"
        </p>
        <small style={{ color: '#666' }}>
          Last updated: {lastUpdated}
        </small>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>Update Message</h2>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Enter new message for LED display"
          style={{
            width: '100%',
            padding: '10px',
            fontSize: '16px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            marginBottom: '10px'
          }}
          onKeyPress={(e) => e.key === 'Enter' && updateMessage()}
        />
        <button
          onClick={updateMessage}
          disabled={isLoading || !newMessage.trim()}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: isLoading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'Updating...' : 'Update Display'}
        </button>
      </div>

      <div style={{ 
        background: '#e9f7ef', 
        padding: '15px', 
        borderRadius: '8px',
        marginTop: '20px'
      }}>
        <h3>Instructions</h3>
        <ol>
          <li>Update your ESP32 code with your WiFi credentials</li>
          <li>Replace the serverURL with your Vercel deployment URL</li>
          <li>Your ESP32 will fetch messages from this API every 30 seconds</li>
          <li>Use this web interface to update the message dynamically</li>
        </ol>
      </div>

      <div style={{ 
        background: '#fff3cd', 
        padding: '15px', 
        borderRadius: '8px',
        marginTop: '20px'
      }}>
        <h3>ESP32 Configuration</h3>
        <p>Make sure to update these values in your ESP32 code:</p>
        <pre style={{ 
          background: '#f8f9fa', 
          padding: '10px', 
          borderRadius: '4px',
          overflow: 'auto'
        }}>
{`const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverURL = "https://your-app.vercel.app/api/message";`}
        </pre>
      </div>
    </div>
  );
}