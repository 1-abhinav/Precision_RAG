import { useMemo, useState } from 'react';
import { Chat } from './components/Chat';
import { PDFUpload } from './components/PDFUpload';
import type { UploadResponse } from './types';

export function App() {
  const [showUpload, setShowUpload] = useState(false);
  const sessionInsights = useMemo(
    () => [
      {
        label: 'Knowledge Stack',
        value: 'Engineering PDFs',
        accent: 'accent-blue',
      },
      {
        label: 'Citation Density',
        value: 'Smart snippets',
        accent: 'accent-lime',
      },
      {
        label: 'Realtime Mode',
        value: 'Adaptive answers',
        accent: 'accent-purple',
      },
    ],
    []
  );

  return (
    <div className="app-shell">
      <div className="ambient-gradient" aria-hidden />
      <div className="ambient-grid" aria-hidden />
      <div className="app">
        <header className="app-header">
          <div className="header-content">
            <div>
              <span className="neon-pill">Contextual AI Workspace</span>
              <h1>Precision RAG</h1>
              <p className="subtitle">
                Conversational retrieval that keeps citations tidy and insight-rich.
              </p>
            </div>
            <div className="header-actions">
              <button
                className="toggle-upload-button"
                onClick={() => setShowUpload(!showUpload)}
              >
                {showUpload ? 'Hide Upload Panel' : 'Upload PDFs'}
              </button>
              <div className="ghost-button">
                <span className="dot" />
                Live Session
              </div>
            </div>
          </div>
          <div className="session-metrics">
            {sessionInsights.map((item) => (
              <div key={item.label} className={`metric-card ${item.accent}`}>
                <p>{item.label}</p>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </header>

        {showUpload && (
          <div className="upload-section elevated-card">
            <PDFUpload
              onUploadComplete={(response: UploadResponse) => {
                console.log('Upload complete:', response);
              }}
            />
          </div>
        )}

        <main className="app-main">
          <Chat />
        </main>
      </div>
    </div>
  );
}

