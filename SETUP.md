# Quick Setup Guide

## ✅ Pre-Flight Checklist

### Backend Setup (One-time)

1. **Install Python dependencies:**
   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create `.env` file in project root:**
   ```powershell
   cd ..
   copy env.sample .env
   # Then edit .env and add your GEMINI_API_KEY
   ```

3. **Start backend server:**
   ```powershell
   cd backend
   .venv\Scripts\activate
   flask --app app run --debug
   ```
   Backend will run on `http://127.0.0.1:5000`

### Frontend Setup (One-time)

1. **Install Node dependencies:**
   ```powershell
   cd frontend
   npm install
   ```

2. **Optional: Create `.env` file in frontend directory:**
   ```
   VITE_API_BASE_URL=http://127.0.0.1:5000
   ```
   (This is optional - defaults to this URL if not set)

3. **Start frontend dev server:**
   ```powershell
   npm run dev -- --host
   ```
   Frontend will run on `http://localhost:5173` (or another port if 5173 is busy)

## 🚀 Testing

1. **Open browser:** Navigate to `http://localhost:5173`
2. **Upload a PDF:** Click "Upload PDF" button and select an engineering PDF
3. **Ask questions:** Type questions in the chat interface

## ⚠️ Troubleshooting

- **Backend not connecting?** Check that Flask is running on port 5000
- **"GEMINI_API_KEY is not set" warning?** The backend will still start, but queries will fail. Make sure `.env` is in the project root (same level as `env.sample`)
- **CORS errors?** Make sure backend Flask server is running and CORS is enabled (it is by default)

