import React from 'react';
import { Plane, Users, IndianRupee } from 'lucide-react';
import type { Flight } from '../types';
import { formatTime, formatDate, formatCurrency } from '../services/flightService';

interface Props {
  flight: Flight;
  passengers: number;
}

export default function BookingSummary({ flight, passengers }: Props) {
  const tax = Math.round(flight.fare.total_fare * 0.05);
  const serviceFee = 499;
  const total = flight.fare.total_fare + tax + serviceFee;

  return (
    <div
      style={{
        background: 'white',
        border: '1.5px solid #e2e8f0',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 4px 20px rgba(15,23,42,0.06)',
        position: 'sticky',
        top: '84px',
      }}
    >
      <h3
        style={{
          fontWeight: 700,
          fontSize: '16px',
          color: '#0f172a',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        🎫 Booking Summary
      </h3>

      {/* Flight info */}
      <div
        style={{
          background: 'linear-gradient(135deg, #f0f9ff, #e0f2fe)',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Plane size={16} color="white" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
              {flight.airline}
            </div>
            <div style={{ fontSize: '12px', color: '#0284c7', fontWeight: 600 }}>
              {flight.flight_id}
            </div>
          </div>
        </div>
        <div style={{ fontSize: '13px', color: '#475569', lineHeight: '1.8' }}>
          <div>
            <strong>{flight.origin}</strong> → <strong>{flight.destination}</strong>
          </div>
          <div>📅 {formatDate(flight.date)}</div>
          <div>
            🕐 {formatTime(flight.departure_time)} → {formatTime(flight.arrival_time)}
          </div>
          <div>💺 {flight.travel_class}</div>
        </div>
      </div>

      {/* Passengers */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          paddingBottom: '16px',
          borderBottom: '1px solid #f1f5f9',
        }}
      >
        <span style={{ fontSize: '14px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Users size={14} /> Passengers
        </span>
        <span style={{ fontWeight: 700, color: '#0f172a' }}>{passengers}</span>
      </div>

      {/* Fare breakdown */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
        {[
          { label: 'Base fare', amount: flight.fare.total_fare },
          { label: 'Taxes (5%)', amount: tax },
          { label: 'Service fee', amount: serviceFee },
        ].map(({ label, amount }) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', color: '#64748b' }}>{label}</span>
            <span style={{ fontSize: '13px', color: '#0f172a', fontWeight: 500 }}>
              {formatCurrency(amount)}
            </span>
          </div>
        ))}
      </div>

      {/* Total */}
      <div
        style={{
          background: '#0f172a',
          borderRadius: '12px',
          padding: '14px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: '14px', color: 'white', fontWeight: 600 }}>Total</span>
        <span
          style={{
            fontSize: '20px',
            fontWeight: 900,
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            gap: '2px',
          }}
        >
          <IndianRupee size={16} />
          {total.toLocaleString('en-IN')}
        </span>
      </div>
    </div>
  );
}
