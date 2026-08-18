import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getBookingDetailsApi, cancelBookingApi, downloadTicketPdfApi } from '../services/api';
import { formatDate, formatCurrency } from '../services/flightService';
import { ArrowLeft, Ticket, FileText, Trash2, Calendar, ShieldCheck, User } from 'lucide-react';

export default function BookingDetails() {
  const { bookingId } = useParams<{ bookingId: string }>();
  const { userToken } = useAuth();
  const navigate = useNavigate();

  const [booking, setBooking] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    const fetchDetails = async () => {
      if (!userToken || !bookingId) return;
      setLoading(true);
      setError(null);
      try {
        const data = await getBookingDetailsApi(Number(bookingId), userToken);
        if (data.success) {
          setBooking(data);
        } else {
          setError(data.message || 'Failed to retrieve booking details.');
        }
      } catch (err: any) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Unable to connect to the server.');
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [bookingId, userToken]);

  const handleCancelBooking = async () => {
    if (!userToken || !booking) return;
    if (!window.confirm(`Are you sure you want to cancel booking ${booking.booking_reference}?`)) return;

    setCancelling(true);
    try {
      const res = await cancelBookingApi(booking.booking_id, userToken);
      if (res.success) {
        alert('Booking cancelled successfully.');
        setBooking({ ...booking, status: 'CANCELLED', computed_status: 'CANCELLED' });
      } else {
        alert(res.message || 'Failed to cancel booking.');
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : detail?.message || 'Failed to cancel booking.';
      alert(msg);
    } finally {
      setCancelling(false);
    }
  };

  const handleDownloadTicket = async () => {
    if (!userToken || !booking) return;
    try {
      const blob = await downloadTicketPdfApi(booking.booking_id, userToken);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ticket_${booking.booking_reference}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      alert('Failed to download PDF ticket.');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <div style={{ textAlign: 'center', color: '#64748b' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid #e2e8f0', borderTopColor: '#0ea5e9', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px auto' }} />
          <span>Loading booking details...</span>
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div style={{ maxWidth: '640px', margin: '0 auto', animation: 'fadeIn 0.4s ease both' }}>
        <div style={{ marginBottom: '24px' }}>
          <Link to="/my-bookings" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 600, color: '#64748b', textDecoration: 'none' }}>
            <ArrowLeft size={16} /> Back to My Bookings
          </Link>
        </div>
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '24px', borderRadius: '16px', textAlign: 'center' }}>
          <p style={{ fontWeight: 700, fontSize: '16px', marginBottom: '8px' }}>Error Loading Details</p>
          <p style={{ fontSize: '14px' }}>{error || 'Booking details could not be found.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', animation: 'fadeIn 0.4s ease both' }}>
      {/* Back Link */}
      <div style={{ marginBottom: '24px' }}>
        <Link to="/my-bookings" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 600, color: '#64748b', textDecoration: 'none' }}>
          <ArrowLeft size={16} /> Back to My Bookings
        </Link>
      </div>

      {/* Main Details Card */}
      <div
        style={{
          background: 'white',
          borderRadius: '24px',
          border: '1.5px solid #e2e8f0',
          boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
          overflow: 'hidden',
          marginBottom: '32px',
        }}
      >
        {/* Banner with Ref and Status */}
        <div
          style={{
            background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
            padding: '28px 32px',
            color: 'white',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', opacity: 0.8, letterSpacing: '0.5px' }}>
              Booking Reference
            </div>
            <div style={{ fontSize: '24px', fontWeight: 900, fontFamily: 'monospace', letterSpacing: '1px', marginTop: '4px' }}>
              {booking.booking_reference}
            </div>
          </div>
          <span
            style={{
              padding: '6px 16px',
              borderRadius: '20px',
              fontSize: '13px',
              fontWeight: 800,
              textTransform: 'uppercase',
              background: 'white',
              color:
                booking.computed_status === 'UPCOMING'
                  ? '#d97706'
                  : booking.computed_status === 'COMPLETED'
                  ? '#059669'
                  : '#dc2626',
            }}
          >
            {booking.computed_status}
          </span>
        </div>

        {/* Content Details */}
        <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {/* Flight Details Block */}
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', borderBottom: '1px solid #f1f5f9', paddingBottom: '10px' }}>
              <Calendar size={18} color="#0ea5e9" />
              Flight Details
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Airline & Flight ID</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginTop: '2px' }}>{booking.airline} ({booking.flight_id})</div>
              </div>

              <div>
                <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Route (Origin & Destination)</div>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                  {booking.origin} → {booking.destination}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Date & Flight Time</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginTop: '2px' }}>
                  {formatDate(booking.date)}
                </div>
                <div style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>
                  Departure: {booking.departure_time} | Arrival: {booking.arrival_time}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Travel Cabin Class</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginTop: '2px' }}>{booking.travel_class}</div>
              </div>
            </div>
          </div>

          {/* Passenger & Fare Details */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '32px' }}>
            {/* Passenger Info */}
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', borderBottom: '1px solid #f1f5f9', paddingBottom: '10px' }}>
                <User size={18} color="#0ea5e9" />
                Passenger Details
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '14px' }}>
                <div>
                  <span style={{ color: '#64748b', fontWeight: 600 }}>Name: </span>
                  <span style={{ fontWeight: 700, color: '#0f172a' }}>{booking.passenger_name || user?.name}</span>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontWeight: 600 }}>Email: </span>
                  <span style={{ color: '#0f172a' }}>{booking.passenger_email || user?.email}</span>
                </div>
                <div>
                  <span style={{ color: '#64748b', fontWeight: 600 }}>Mobile: </span>
                  <span style={{ color: '#0f172a' }}>{booking.passenger_mobile || user?.mobile_number || 'N/A'}</span>
                </div>
              </div>
            </div>

            {/* Fare Summary */}
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', borderBottom: '1px solid #f1f5f9', paddingBottom: '10px' }}>
                <ShieldCheck size={18} color="#10b981" />
                Payment Summary
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Reserved Seats:</span>
                  <span style={{ fontWeight: 700, color: '#0f172a' }}>{booking.number_of_seats} Seats</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1.5px solid #f1f5f9', paddingTop: '10px' }}>
                  <span style={{ fontWeight: 700, color: '#0f172a' }}>Total Amount Paid:</span>
                  <span style={{ fontWeight: 900, color: '#0284c7', fontSize: '18px' }}>
                    {formatCurrency(booking.total_price)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Panel */}
        <div
          style={{
            background: '#f8fafc',
            padding: '24px 32px',
            borderTop: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '12px',
            flexWrap: 'wrap',
          }}
        >
          <Link
            to={`/ticket/${booking.booking_id}`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              borderRadius: '12px',
              border: '1.5px solid #0284c7',
              background: 'white',
              color: '#0284c7',
              fontSize: '14px',
              fontWeight: 700,
              textDecoration: 'none',
              cursor: 'pointer',
            }}
          >
            <Ticket size={16} /> View Boarding Pass
          </Link>

          <button
            onClick={handleDownloadTicket}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              borderRadius: '12px',
              border: 'none',
              background: '#e0f2fe',
              color: '#0284c7',
              fontSize: '14px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            <FileText size={16} /> Download Ticket PDF
          </button>

          {booking.computed_status === 'UPCOMING' && (
            <button
              disabled={cancelling}
              onClick={handleCancelBooking}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 24px',
                borderRadius: '12px',
                border: 'none',
                background: '#fef2f2',
                color: '#ef4444',
                fontSize: '14px',
                fontWeight: 700,
                cursor: cancelling ? 'not-allowed' : 'pointer',
                opacity: cancelling ? 0.6 : 1,
              }}
            >
              <Trash2 size={16} />
              {cancelling ? 'Cancelling...' : 'Cancel Reservation'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
