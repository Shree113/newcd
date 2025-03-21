// ... existing code ...

const express = require('express');
const cors = require('cors');
const app = express();

// Configure CORS
app.use(cors({
  origin: ['https://new-fd.vercel.app', 'http://localhost:3000'],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Make sure this is before any routes
app.use(express.json());

// ... rest of your server code ...