import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Booking } from '../types';
import { formatTime, formatDate, formatCurrency } from '../services/flightService';
import { Download, Eye, Home } from 'lucide-react';

interface Props {
  booking: Booking;
}

export default function BookingConfirmation({ booking }: Props) {
  const navigate = useNavigate();

  return (
    <div
      style={{
        maxWidth: '540px',
        margin: '0 auto',
        textAlign: 'center',
      }}
    >
      {/* Success icon */}
      <div
        style={{
          fontSize: '72px',
          marginBottom: '16px',
          animation: 'fadeIn 0.5s ease',
        }}
      >
        🎉
      </div>
      <h1 style={{ fontSize: '28px', fontWeight: 900, color: '#0f172a', marginBottom: '8px' }}>
        Booking Confirmed!
      </h1>
      <p style={{ color: '#64748b', marginBottom: '32px' }}>
        Your flight has been booked successfully. A confirmation will be sent to your email.
      </p>

      {/* Ticket card */}
      <div
        style={{
          background: 'white',
          borderRadius: '20px',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(15,23,42,0.12)',
          marginBottom: '28px',
          border: '1.5px solid #e2e8f0',
        }}
      >
        {/* Header */}
        <div
          style={{
            background: 'linear-gradient(135deg, #0f172a, #1e293b)',
            padding: '20px 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ color: 'white' }}>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '2px' }}>
              Booking ID
            </div>
            <div style={{ fontSize: '20px', fontWeight: 800, letterSpacing: '1px' }}>
              {booking.bookingId}
            </div>
          </div>
          <span
            style={{
              background: '#10b981',
              color: 'white',
              borderRadius: '999px',
              padding: '4px 14px',
              fontSize: '12px',
              fontWeight: 700,
            }}
          >
            ✓ Confirmed
          </span>
        </div>

        {/* Dashed divider */}
        <div
          style={{
            borderTop: '2px dashed #e2e8f0',
            margin: '0 24px',
            position: 'relative',
          }}
        >
          <div
            style={{
              position: 'absolute',
              left: '-36px',
              top: '-12px',
              width: '24px',
              height: '24px',
              background: '#f8fafc',
              borderRadius: '50%',
              border: '1.5px solid #e2e8f0',
            }}
          />
          <div
            style={{
              position: 'absolute',
              right: '-36px',
              top: '-12px',
              width: '24px',
              height: '24px',
              background: '#f8fafc',
              borderRadius: '50%',
              border: '1.5px solid #e2e8f0',
            }}
          />
        </div>

        {/* Flight details */}
        <div style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <div style={{ fontWeight: 800, fontSize: '18px', color: '#0f172a' }}>
                {booking.airline}
              </div>
              <div style={{ fontSize: '13px', color: '#64748b' }}>{booking.flightNumber}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontWeight: 600, fontSize: '14px', color: '#0f172a' }}>
                {booking.travelClass}
              </div>
            </div>
          </div>

          {/* Route */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '26px', fontWeight: 900 }}>{formatTime(booking.departureTime)}</div>
              <div style={{ fontSize: '13px', color: '#64748b' }}>{booking.origin}</div>
            </div>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ flex: 1, height: '1.5px', background: '#e2e8f0' }} />
              <span style={{ fontSize: '20px' }}>✈️</span>
              <div style={{ flex: 1, height: '1.5px', background: '#e2e8f0' }} />
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '26px', fontWeight: 900 }}>{formatTime(booking.arrivalTime)}</div>
              <div style={{ fontSize: '13px', color: '#64748b' }}>{booking.destination}</div>
            </div>
          </div>

          {/* Info grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '14px',
              background: '#f8fafc',
              borderRadius: '12px',
              padding: '16px',
            }}
          >
            {[
              { label: '📅 Date', value: formatDate(booking.date) },
              { label: '👥 Passengers', value: booking.passengers },
              { label: '💺 Class', value: booking.travelClass },
              { label: '💳 Total Paid', value: formatCurrency(booking.totalFare) },
            ].map(({ label, value }) => (
              <div key={label} style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600, marginBottom: '2px' }}>
                  {label}
                </div>
                <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>{value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
        <button
          id="view-booking-btn"
          className="btn-secondary"
          onClick={() => navigate('/my-bookings')}
        >
          <Eye size={15} /> View Booking
        </button>
        <button
          id="download-ticket-btn"
          className="btn-ghost"
          onClick={() => alert('Download feature coming soon!')}
        >
          <Download size={15} /> Download Ticket
        </button>
        <button
          id="back-home-btn"
          className="btn-primary"
          onClick={() => navigate('/')}
        >
          <Home size={15} /> Back to Home
        </button>
      </div>
    </div>
  );
}
