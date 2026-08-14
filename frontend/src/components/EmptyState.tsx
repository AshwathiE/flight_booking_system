import React from 'react';
import { useNavigate } from 'react-router-dom';
import { SearchX } from 'lucide-react';
import type { FlightSearchRequest, SearchParameters } from '../types';
import { formatDate } from '../services/flightService';

interface Props {
  params: FlightSearchRequest | SearchParameters;
}

export default function EmptyState({ params }: Props) {
  const navigate = useNavigate();

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
      <div
        style={{
          width: '80px',
          height: '80px',
          background: 'linear-gradient(135deg, #f1f5f9, #e2e8f0)',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '24px',
        }}
      >
        <SearchX size={36} color="#94a3b8" />
      </div>

      <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', marginBottom: '12px' }}>
        No flights found
      </h2>
      <p style={{ fontSize: '15px', color: '#64748b', maxWidth: '420px', lineHeight: '1.7' }}>
        We couldn't find matching flights from{' '}
        <strong style={{ color: '#0f172a', textTransform: 'capitalize' }}>{params.origin}</strong>{' '}
        to{' '}
        <strong style={{ color: '#0f172a', textTransform: 'capitalize' }}>{params.destination}</strong>{' '}
        for {('total_seats' in params ? params.total_seats : (params.passengers || 1))} passenger{('total_seats' in params ? params.total_seats : (params.passengers || 1)) !== 1 ? 's' : ''} on{' '}
        <strong style={{ color: '#0f172a' }}>{formatDate(params.date)}</strong>.
      </p>

      <div style={{ display: 'flex', gap: '12px', marginTop: '32px', flexWrap: 'wrap', justifyContent: 'center' }}>
        <button
          id="empty-change-date-btn"
          className="btn-secondary"
          onClick={() => navigate('/')}
        >
          📅 Change Date
        </button>
        <button
          id="empty-edit-search-btn"
          className="btn-primary"
          onClick={() => navigate('/')}
        >
          Edit Search
        </button>
      </div>
    </div>
  );
}
