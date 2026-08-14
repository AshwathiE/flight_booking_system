import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NaturalLanguageSearch from '../components/NaturalLanguageSearch';
import FlightSearchForm from '../components/FlightSearchForm';
import { searchFlightsService } from '../services/flightService';
import { Shield, Zap, Star } from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (message: string) => {
    setError('');
    setLoading(true);
    try {
      const response = await searchFlightsService(message);

      navigate('/results', {
        state: {
          searchResponse: response,
        },
      });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unable to search flights right now. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const features = [
    { icon: <Zap size={20} color="#0ea5e9" />, title: 'AI-Powered Search', desc: 'Natural language queries understood instantly' },
    { icon: <Star size={20} color="#f59e0b" />, title: 'Smart Recommendations', desc: 'AI picks the best flight for your needs' },
    { icon: <Shield size={20} color="#10b981" />, title: 'Secure Booking', desc: 'Encrypted, safe payments every time' },
  ];

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-surface)' }}>
      {/* Hero */}
      <div
        style={{
          background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0c4a6e 100%)',
          position: 'relative',
          overflow: 'hidden',
          padding: '80px 24px 60px',
        }}
      >
        {/* Background decoration */}
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden' }}>
          <div
            style={{
              position: 'absolute',
              top: '-80px',
              right: '-80px',
              width: '400px',
              height: '400px',
              background: 'radial-gradient(circle, rgba(14,165,233,0.15), transparent 70%)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: '-60px',
              left: '-60px',
              width: '300px',
              height: '300px',
              background: 'radial-gradient(circle, rgba(14,165,233,0.08), transparent 70%)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              top: '40px',
              left: '10%',
              fontSize: '40px',
              opacity: 0.12,
            }}
            className="animate-plane-float"
          >
            ✈️
          </div>
          <div
            style={{
              position: 'absolute',
              top: '70px',
              right: '15%',
              fontSize: '24px',
              opacity: 0.08,
            }}
          >
            ✈️
          </div>
        </div>

        <div style={{ maxWidth: '800px', margin: '0 auto', position: 'relative' }}>
          {/* Badge */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(14,165,233,0.15)',
              border: '1px solid rgba(14,165,233,0.3)',
              borderRadius: '999px',
              padding: '5px 16px',
              marginBottom: '20px',
              color: '#7dd3fc',
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            ✨ AI-Powered Flight Search
          </div>

          <h1
            style={{
              fontSize: 'clamp(32px, 5vw, 52px)',
              fontWeight: 900,
              color: 'white',
              marginBottom: '16px',
              lineHeight: '1.15',
              letterSpacing: '-1px',
            }}
          >
            Find Your Perfect
            <br />
            <span
              style={{
                background: 'linear-gradient(135deg, #38bdf8, #0ea5e9)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Flight ✈️
            </span>
          </h1>
          <p
            style={{
              color: '#94a3b8',
              fontSize: '17px',
              marginBottom: '40px',
              lineHeight: '1.6',
            }}
          >
            Search flights using natural language or enter your travel details.
            <br />
            Our AI finds and recommends the best options for you.
          </p>

          {/* Search box */}
          <NaturalLanguageSearch onSearch={handleSearch} loading={loading} />
          <FlightSearchForm onSearch={handleSearch} loading={loading} />

          {error && (
            <div
              style={{
                marginTop: '16px',
                background: 'rgba(239,68,68,0.12)',
                border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: '12px',
                padding: '12px 16px',
                color: '#fca5a5',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              ⚠️ {error}
            </div>
          )}
        </div>
      </div>

      {/* Features */}
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '60px 24px' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', marginBottom: '8px' }}>
            Why Book With Us?
          </h2>
          <p style={{ color: '#64748b', fontSize: '15px' }}>
            The smartest way to book your next flight
          </p>
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '20px',
          }}
        >
          {features.map(({ icon, title, desc }) => (
            <div
              key={title}
              style={{
                background: 'white',
                borderRadius: '16px',
                padding: '24px',
                border: '1.5px solid #e2e8f0',
                boxShadow: '0 2px 12px rgba(15,23,42,0.05)',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-4px)';
                (e.currentTarget as HTMLDivElement).style.boxShadow = '0 8px 28px rgba(15,23,42,0.1)';
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
                (e.currentTarget as HTMLDivElement).style.boxShadow = '0 2px 12px rgba(15,23,42,0.05)';
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
                  marginBottom: '14px',
                }}
              >
                {icon}
              </div>
              <h3 style={{ fontWeight: 700, fontSize: '16px', color: '#0f172a', marginBottom: '6px' }}>
                {title}
              </h3>
              <p style={{ fontSize: '14px', color: '#64748b', lineHeight: '1.6' }}>{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
