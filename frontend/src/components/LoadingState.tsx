import React from 'react';

export default function LoadingState() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '80px 24px',
        textAlign: 'center',
      }}
    >
      {/* Animated plane */}
      <div style={{ position: 'relative', width: '120px', height: '80px', marginBottom: '32px' }}>
        <div
          style={{
            position: 'absolute',
            fontSize: '48px',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }}
          className="animate-plane-float"
        >
          ✈️
        </div>
        {/* Trail dots */}
        <div
          style={{
            position: 'absolute',
            bottom: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            gap: '6px',
          }}
        >
          <span className="dot-bounce" />
          <span className="dot-bounce" />
          <span className="dot-bounce" />
        </div>
      </div>

      <h2
        style={{
          fontSize: '22px',
          fontWeight: 700,
          color: '#0f172a',
          marginBottom: '10px',
        }}
      >
        Finding the best flights for you...
      </h2>
      <p style={{ fontSize: '15px', color: '#64748b', maxWidth: '360px' }}>
        Our AI is searching through thousands of options to find the perfect match for your trip.
      </p>

      {/* Skeleton cards */}
      <div style={{ width: '100%', maxWidth: '720px', marginTop: '40px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '20px 24px',
              border: '1.5px solid #e2e8f0',
            }}
          >
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              <div className="shimmer" style={{ width: '40px', height: '40px', borderRadius: '10px' }} />
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div className="shimmer" style={{ height: '16px', width: '60%' }} />
                <div className="shimmer" style={{ height: '12px', width: '40%' }} />
              </div>
              <div className="shimmer" style={{ width: '100px', height: '36px', borderRadius: '10px' }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
