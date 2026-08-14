import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorMessage({
  message = "We're having trouble finding flights right now. Please try again.",
  onRetry,
}: Props) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 24px',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          width: '72px',
          height: '72px',
          background: '#fff1f2',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '20px',
          border: '2px solid #fecdd3',
        }}
      >
        <AlertTriangle size={32} color="#ef4444" />
      </div>

      <h3 style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a', marginBottom: '10px' }}>
        Something went wrong
      </h3>
      <p style={{ fontSize: '14px', color: '#64748b', maxWidth: '400px', lineHeight: '1.7' }}>
        {message}
      </p>

      {onRetry && (
        <button
          id="error-retry-btn"
          className="btn-primary"
          onClick={onRetry}
          style={{ marginTop: '24px' }}
        >
          <RefreshCw size={15} />
          Try Again
        </button>
      )}
    </div>
  );
}
