import { useState, ChangeEvent, DragEvent } from 'react';
import { uploadPDF } from '../api';
import type { UploadResponse } from '../types';

interface PDFUploadProps {
  onUploadComplete?: (response: UploadResponse) => void;
}

export function PDFUpload({ onUploadComplete }: PDFUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported.');
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await uploadPDF(file);
      setSuccess(
        `Successfully uploaded! Pages: ${response.stats.pages}, Chunks added: ${response.stats.chunks_added}`
      );
      onUploadComplete?.(response);
      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  return (
    <div className="pdf-upload">
      <div
        className={`upload-area ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <input
          type="file"
          id="pdf-input"
          accept=".pdf"
          onChange={handleFileSelect}
          disabled={isUploading}
          style={{ display: 'none' }}
        />
        <label htmlFor="pdf-input" className="upload-label">
          {isUploading ? (
            <span>Uploading...</span>
          ) : (
            <>
              <span className="upload-icon">📄</span>
              <span>Drop PDF here or click to browse</span>
            </>
          )}
        </label>
      </div>
      {error && <div className="upload-error">{error}</div>}
      {success && <div className="upload-success">{success}</div>}
    </div>
  );
}

