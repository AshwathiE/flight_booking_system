import React from 'react';
import { Plane, Clock, Users, ArrowRight } from 'lucide-react';
import type { Flight } from "../types";
import { formatTime, formatCurrency } from '../services/flightService';
import { calculateFlightDuration } from '../utils/flightUtils';

interface Props {
  flight: Flight;
  totalPassengers: number;
  onSelect: (flight: Flight) => void;
}

export default function FlightCard({ flight, totalPassengers, onSelect }: Props) {
  const durationText = calculateFlightDuration(flight.departure_time, flight.arrival_time);

  return (
    <div
      className="animate-fade-in"
      style={{
        background: 'white',
        border: '1.5px solid #e2e8f0',
        borderRadius: '16px',
        padding: '20px 24px',
        boxShadow: '0 2px 12px rgba(15,23,42,0.05)',
        transition: 'all 0.2s ease',
        cursor: 'default',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = '#7dd3fc';
        (e.currentTarget as HTMLDivElement).style.boxShadow = '0 4px 20px rgba(14,165,233,0.12)';
        (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.borderColor = '#e2e8f0';
        (e.currentTarget as HTMLDivElement).style.boxShadow = '0 2px 12px rgba(15,23,42,0.05)';
        (e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        {/* Left: Airline + times */}
        <div style={{ flex: 1, minWidth: '240px' }}>
          {/* Airline row */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  background: 'linear-gradient(135deg, #f1f5f9, #e2e8f0)',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Plane size={18} color="#0ea5e9" />
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '15px', color: '#0f172a' }}>
                  {flight.airline}
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: '#94a3b8',
                    fontWeight: 600,
                    letterSpacing: '0.5px',
                  }}
                >
                  {flight.flight_id}
                </div>
              </div>
            </div>
            <span className="tag tag-sky">{flight.travel_class}</span>
          </div>

          {/* Route timeline */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div>
              <div style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a' }}>
                {formatTime(flight.departure_time)}
              </div>
              <div style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>
                {flight.origin}
              </div>
            </div>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
              {durationText && (
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: '#0284c7',
                    background: '#e0f2fe',
                    padding: '2px 8px',
                    borderRadius: '999px',
                  }}
                >
                  {durationText}
                </span>
              )}
              <div style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div
                  style={{ flex: 1, height: '1.5px', background: 'linear-gradient(90deg, #e2e8f0, #7dd3fc, #e2e8f0)' }}
                />
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    background: '#e0f2fe',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Plane size={14} color="#0284c7" />
                </div>
                <div
                  style={{ flex: 1, height: '1.5px', background: 'linear-gradient(90deg, #e2e8f0, #7dd3fc, #e2e8f0)' }}
                />
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a' }}>
                {formatTime(flight.arrival_time)}
              </div>
              <div style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>
                {flight.destination}
              </div>
            </div>
          </div>

          {/* Seats & Duration */}
          <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Users size={13} color="#94a3b8" />
            <span style={{ fontSize: '13px', color: '#64748b' }}>
              {flight.available_seats} seats available
            </span>
            <Clock size={13} color="#94a3b8" style={{ marginLeft: '8px' }} />
            <span style={{ fontSize: '13px', color: '#64748b' }}>{flight.date}</span>
            {durationText && (
              <span style={{ fontSize: '13px', color: '#0284c7', fontWeight: 600, marginLeft: '8px' }}>
                • Duration: {durationText}
              </span>
            )}
          </div>
        </div>

        {/* Right: Fare + button */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: '12px',
            minWidth: '160px',
          }}
        >
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, marginBottom: '2px' }}>
              Total fare for {totalPassengers} passenger{totalPassengers !== 1 ? 's' : ''}
            </div>
            <div
              style={{
                fontSize: '24px',
                fontWeight: 800,
                color: '#0f172a',
                letterSpacing: '-0.5px',
              }}
            >
              {formatCurrency(flight.fare.total_fare)}
            </div>
          </div>
          <button
            id={`select-flight-${flight.flight_id}`}
            className="btn-primary"
            onClick={() => onSelect(flight)}
            style={{ fontSize: '13px', padding: '10px 18px', width: '100%' }}
          >
            Select Flight <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
