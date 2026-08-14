import React from 'react';
import { Plane, Brain, Shield, Zap } from 'lucide-react';

export default function About() {
  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', padding: '60px 24px' }}>
      <div style={{ maxWidth: '720px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '52px' }}>
          <div
            style={{
              width: '64px',
              height: '64px',
              background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
              borderRadius: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 20px',
              boxShadow: '0 8px 24px rgba(14,165,233,0.3)',
            }}
          >
            <Plane size={32} color="white" />
          </div>
          <h1 style={{ fontSize: '32px', fontWeight: 900, color: '#0f172a', marginBottom: '12px' }}>
            About AI Flight Booking
          </h1>
          <p style={{ color: '#64748b', fontSize: '16px', lineHeight: '1.7' }}>
            A next-generation flight search powered by AI. Simply describe your trip in plain English
            and our intelligent agent finds, evaluates, and recommends the best flights for you.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {[
            {
              icon: <Brain size={22} color="#0ea5e9" />,
              title: 'Natural Language Understanding',
              desc: 'Type your request the way you\'d say it. Our AI extracts origin, destination, dates, passengers and preferences automatically.',
            },
            {
              icon: <Zap size={22} color="#f59e0b" />,
              title: 'Instant Results',
              desc: 'Your request is processed through a high-performance backend and returns real-time flight availability and fares.',
            },
            {
              icon: <Shield size={22} color="#10b981" />,
              title: 'Secure & Private',
              desc: 'All payments are encrypted. We never store card details and your personal information is protected.',
            },
          ].map(({ icon, title, desc }) => (
            <div
              key={title}
              style={{
                background: 'white',
                borderRadius: '16px',
                padding: '24px',
                border: '1.5px solid #e2e8f0',
                display: 'flex',
                gap: '18px',
                alignItems: 'flex-start',
                boxShadow: '0 2px 12px rgba(15,23,42,0.05)',
              }}
            >
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  background: '#f0f9ff',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {icon}
              </div>
              <div>
                <h3 style={{ fontWeight: 700, fontSize: '16px', color: '#0f172a', marginBottom: '6px' }}>
                  {title}
                </h3>
                <p style={{ fontSize: '14px', color: '#64748b', lineHeight: '1.6' }}>{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
