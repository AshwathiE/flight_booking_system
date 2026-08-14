import React, { useState, FormEvent } from 'react';
import { Search, Sparkles } from 'lucide-react';

interface Props {
  onSearch: (message: string) => void;
  loading: boolean;
  initialValue?: string;
}

export default function NaturalLanguageSearch({ onSearch, loading, initialValue = '' }: Props) {
  const [value, setValue] = useState(initialValue);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (value.trim()) onSearch(value.trim());
  };

  const suggestions = [
    'Flight from Chennai to Delhi for 2 passengers on 20 August 2026',
    'Cheapest flight Mumbai to Bangalore tomorrow for 1 passenger',
    'Business class flight from Hyderabad to Kolkata next week',
  ];

  return (
    <div style={{ width: '100%' }}>
      <form onSubmit={handleSubmit}>
        <div
          style={{
            position: 'relative',
            background: 'white',
            borderRadius: '16px',
            boxShadow: '0 8px 40px rgba(14,165,233,0.15), 0 2px 8px rgba(0,0,0,0.06)',
            border: '2px solid transparent',
            transition: 'border-color 0.2s, box-shadow 0.2s',
          }}
          onFocus={() => {}}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '6px 6px 6px 20px',
              gap: '12px',
            }}
          >
            <Sparkles size={20} color="#0ea5e9" style={{ flexShrink: 0 }} />
            <textarea
              id="nl-search"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (value.trim()) onSearch(value.trim());
                }
              }}
              placeholder="Example: Flight from Chennai to Delhi for 2 passengers on 20 August 2026"
              rows={2}
              disabled={loading}
              style={{
                flex: 1,
                border: 'none',
                outline: 'none',
                resize: 'none',
                fontSize: '16px',
                fontFamily: 'inherit',
                color: '#0f172a',
                background: 'transparent',
                lineHeight: '1.5',
                padding: '8px 0',
              }}
            />
            <button
              id="search-submit-btn"
              type="submit"
              disabled={!value.trim() || loading}
              className="btn-primary"
              style={{
                borderRadius: '12px',
                padding: '14px 24px',
                flexShrink: 0,
                fontSize: '15px',
              }}
            >
              {loading ? (
                <>
                  <div
                    style={{
                      width: '18px',
                      height: '18px',
                      border: '2px solid rgba(255,255,255,0.4)',
                      borderTopColor: 'white',
                      borderRadius: '50%',
                      animation: 'spin-slow 0.8s linear infinite',
                    }}
                  />
                  Searching...
                </>
              ) : (
                <>
                  <Search size={16} />
                  Search Flights ✈️
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Quick suggestions */}
      <div style={{ marginTop: '16px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => setValue(s)}
            style={{
              background: 'rgba(255,255,255,0.7)',
              border: '1px solid #e2e8f0',
              borderRadius: '999px',
              padding: '6px 14px',
              fontSize: '12px',
              color: '#64748b',
              cursor: 'pointer',
              fontFamily: 'inherit',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = 'white';
              (e.currentTarget as HTMLButtonElement).style.color = '#0284c7';
              (e.currentTarget as HTMLButtonElement).style.borderColor = '#7dd3fc';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.7)';
              (e.currentTarget as HTMLButtonElement).style.color = '#64748b';
              (e.currentTarget as HTMLButtonElement).style.borderColor = '#e2e8f0';
            }}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
