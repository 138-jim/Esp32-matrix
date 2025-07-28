export default function handler(req, res) {
  // Set CORS headers to allow requests from any origin
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // Handle preflight OPTIONS request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method === 'GET') {
    // Return the current message
    const message = process.env.LED_MESSAGE || "Hello from Vercel!";
    res.status(200).json({ 
      message: message,
      timestamp: new Date().toISOString()
    });
  } else if (req.method === 'POST') {
    // Update the message (for future enhancement)
    const { message } = req.body;
    if (message) {
      // In a real application, you'd store this in a database
      // For now, we'll just echo it back
      res.status(200).json({ 
        success: true, 
        message: message,
        note: "Message received but not persisted (add database integration)"
      });
    } else {
      res.status(400).json({ error: "Message is required" });
    }
  } else {
    res.setHeader('Allow', ['GET', 'POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}