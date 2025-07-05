# Smart Fridge App

This is a proof-of-concept web application that lets users upload a photo of their fridge or cabinets. The backend uses Google Vision to detect ingredients, Google Gemini to generate recipe suggestions, and a Stable Diffusion-style API to mock up final dish images.

## Project Structure

```
food_recipie/
├── backend/
│   ├── main.py           # FastAPI server
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── public/
│   │   └── index.html    # Vite entry HTML
│   ├── src/
│   │   └── App.jsx       # React application
│   ├── package.json      # NPM manifest
│   └── vite.config.js    # Vite config
└── README.md             # This file
```

## Quickstart

0. Configure environment variables (PowerShell):
   ```pwsh
   $Env:GOOGLE_APPLICATION_CREDENTIALS="d:\path\to\your\service-account.json"
   $Env:GEMINI_KEY="YOUR_GEMINI_KEY"
   ```
   See the "API Keys" section below for instructions on how to obtain these.

1. Backend:
   ```pwsh
   cd backend
   pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```

2. Frontend:
   ```pwsh
   cd frontend
   npm install
   npm run dev
   ```

Browse the UI at http://localhost:5173 and upload a fridge photo.

## Next Steps

- Package with Tauri or Electron for Windows desktop
- Use Capacitor or React Native for Android
- Swap to on-device ML for offline support
- Secure API keys and add authentication

## API Keys

### Google Cloud Vision

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the **Cloud Vision API** for your project. You can find this in the "APIs & Services" > "Library" section.
4. Create a service account:
   - Go to "APIs & Services" > "Credentials".
   - Click "Create Credentials" and select "Service account".
   - Fill in the details and grant the "Cloud Vision API User" role.
   - Download the JSON key file. This is the file you'll point to with the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

### Google Gemini

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click "Get API key" to create a new API key.
4. Copy the generated key. This is the value for your `GEMINI_KEY` environment variable.
