import React from 'react';
import { Plane, Star, ArrowRight, Users, Clock, MessageSquare } from 'lucide-react';
import type { Flight } from "../types";
import { formatTime, formatCurrency } from '../services/flightService';
import { calculateFlightDuration } from '../utils/flightUtils';

interface Props {
  flight: Flight;
  reason: string;
  totalPassengers: number;
  onSelect: (flight: Flight) => void;
}

export default function RecommendedFlightCard({ flight, reason, totalPassengers, onSelect }: Props) {
  const durationText = calculateFlightDuration(flight.departure_time, flight.arrival_time);

  return (
    <div
      className="animate-slide-up"
      style={{
        background: 'linear-gradient(135deg, #f0f9ff, #e0f2fe)',
        border: '2px solid #7dd3fc',
        borderRadius: '20px',
        padding: '24px',
        marginBottom: '20px',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(14,165,233,0.15)',
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: 'absolute',
          top: '-40px',
          right: '-40px',
          width: '160px',
          height: '160px',
          background: 'radial-gradient(circle, rgba(14,165,233,0.12), transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      {/* AI Recommended Badge */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          background: 'linear-gradient(135deg, #f59e0b, #d97706)',
          color: 'white',
          borderRadius: '999px',
          padding: '5px 14px',
          fontSize: '12px',
          fontWeight: 700,
          marginBottom: '18px',
          boxShadow: '0 2px 8px rgba(245,158,11,0.4)',
          letterSpacing: '0.3px',
        }}
      >
        <Star size={13} fill="white" />
        AI Recommended
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '20px',
        }}
      >
        {/* Left */}
        <div style={{ flex: 1, minWidth: '240px' }}>
          {/* Airline */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '18px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(14,165,233,0.3)',
                }}
              >
                <Plane size={20} color="white" />
              </div>
              <div>
                <div style={{ fontWeight: 800, fontSize: '17px', color: '#0f172a' }}>
                  {flight.airline}
                </div>
                <div
                  style={{
                    fontSize: '13px',
                    color: '#0284c7',
                    fontWeight: 700,
                    letterSpacing: '0.5px',
                  }}
                >
                  {flight.flight_id}
                </div>
              </div>
            </div>
            <span
              style={{
                background: '#0ea5e9',
                color: 'white',
                borderRadius: '999px',
                padding: '4px 12px',
                fontSize: '12px',
                fontWeight: 700,
              }}
            >
              {flight.travel_class}
            </span>
          </div>

          {/* Route */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div>
              <div style={{ fontSize: '28px', fontWeight: 900, color: '#0f172a', letterSpacing: '-1px' }}>
                {formatTime(flight.departure_time)}
              </div>
              <div style={{ fontSize: '14px', color: '#0284c7', fontWeight: 600 }}>
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
                  style={{
                    flex: 1,
                    height: '2px',
                    background: 'linear-gradient(90deg, #7dd3fc, #0ea5e9, #7dd3fc)',
                  }}
                />
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 10px rgba(14,165,233,0.35)',
                  }}
                >
                  <Plane size={16} color="white" />
                </div>
                <div
                  style={{
                    flex: 1,
                    height: '2px',
                    background: 'linear-gradient(90deg, #7dd3fc, #0ea5e9, #7dd3fc)',
                  }}
                />
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '28px', fontWeight: 900, color: '#0f172a', letterSpacing: '-1px' }}>
                {formatTime(flight.arrival_time)}
              </div>
              <div style={{ fontSize: '14px', color: '#0284c7', fontWeight: 600 }}>
                {flight.destination}
              </div>
            </div>
          </div>

          {/* Meta */}
          <div style={{ marginTop: '12px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '13px', color: '#475569' }}>
              <Users size={13} />
              {flight.available_seats} seats available
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '13px', color: '#475569' }}>
              <Clock size={13} />
              {flight.date}
            </span>
            {durationText && (
              <span style={{ fontSize: '13px', color: '#0284c7', fontWeight: 700 }}>
                • Duration: {durationText}
              </span>
            )}
          </div>

          {/* Reason */}
          {reason && (
            <div
              style={{
                marginTop: '14px',
                background: 'rgba(255,255,255,0.7)',
                borderRadius: '10px',
                padding: '10px 14px',
                display: 'flex',
                gap: '8px',
                alignItems: 'flex-start',
                border: '1px solid rgba(14,165,233,0.2)',
              }}
            >
              <MessageSquare size={14} color="#0ea5e9" style={{ marginTop: '1px', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#0ea5e9', marginBottom: '2px' }}>
                  Why this flight?
                </div>
                <div style={{ fontSize: '13px', color: '#475569', fontStyle: 'italic' }}>
                  "{reason}"
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: fare + button */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: '12px',
            minWidth: '180px',
          }}
        >
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', color: '#0284c7', fontWeight: 700, marginBottom: '4px' }}>
              Total fare for {totalPassengers} passenger{totalPassengers !== 1 ? 's' : ''}
            </div>
            <div
              style={{
                fontSize: '30px',
                fontWeight: 900,
                color: '#0f172a',
                letterSpacing: '-1px',
              }}
            >
              {formatCurrency(flight.fare.total_fare)}
            </div>
          </div>
          <button
            id={`select-recommended-${flight.flight_id}`}
            className="btn-primary"
            onClick={() => onSelect(flight)}
            style={{ fontSize: '14px', padding: '12px 22px', width: '100%' }}
          >
            Select Flight <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
