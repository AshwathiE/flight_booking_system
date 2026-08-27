import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getMyBookingsApi, cancelBookingApi, downloadTicketPdfApi } from '../services/api';
import { formatDate, formatCurrency } from '../services/flightService';
import { Search, Calendar, Check, X, FileText, ExternalLink, Ticket, Trash2, CreditCard } from 'lucide-react';

type FilterType = 'ALL' | 'UPCOMING' | 'COMPLETED' | 'CANCELLED';

export default function MyBookings() {
  const { userToken } = useAuth();
  const [bookings, setBookings] = useState<any[]>([]);
  const [filteredBookings, setFilteredBookings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<FilterType>('ALL');
  const [cancellingId, setCancellingId] = useState<number | null>(null);

  const fetchBookings = async () => {
    if (!userToken) return;
    setLoading(true);
    try {
      const response = await getMyBookingsApi(userToken);
      if (response.success && response.bookings) {
        setBookings(response.bookings);
      }
    } catch (err) {
      console.error('Failed to load user bookings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, [userToken]);

  useEffect(() => {
    if (activeFilter === 'ALL') {
      setFilteredBookings(bookings);
    } else {
      setFilteredBookings(bookings.filter((b) => b.computed_status === activeFilter));
    }
  }, [activeFilter, bookings]);

  const handleCancelBooking = async (bookingId: number, ref: string) => {
    if (!userToken) return;
    if (!window.confirm(`Are you sure you want to cancel booking ${ref}?`)) return;

    setCancellingId(bookingId);
    try {
      const res = await cancelBookingApi(bookingId, userToken);
      if (res.success) {
        alert('Booking cancelled successfully. Refund is being processed.');
        // Refresh bookings
        await fetchBookings();
      } else {
        alert(res.message || 'Failed to cancel booking.');
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : detail?.message || 'Failed to cancel booking.';
      alert(msg);
    } finally {
      setCancellingId(null);
    }
  };

  const handleDownloadTicket = async (bookingId: number, ref: string) => {
    if (!userToken) return;
    try {
      const blob = await downloadTicketPdfApi(bookingId, userToken);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ticket_${ref}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      alert('Failed to download PDF ticket.');
    }
  };

  const filterTabs: { type: FilterType; label: string }[] = [
    { type: 'ALL', label: 'All Bookings' },
    { type: 'UPCOMING', label: 'Upcoming' },
    { type: 'COMPLETED', label: 'Completed' },
    { type: 'CANCELLED', label: 'Cancelled' },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <div style={{ textAlign: 'center', color: '#64748b' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid #e2e8f0', borderTopColor: '#0ea5e9', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px auto' }} />
          <span>Loading bookings...</span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.4s ease both' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a' }}>My Bookings</h1>
          <p style={{ color: '#64748b', fontSize: '14px', marginTop: '4px' }}>
            View details, print tickets, or cancel your flight plans.
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '2px solid #e2e8f0',
          gap: '24px',
          marginBottom: '32px',
        }}
      >
        {filterTabs.map((tab) => (
          <button
            key={tab.type}
            onClick={() => setActiveFilter(tab.type)}
            style={{
              padding: '12px 4px',
              border: 'none',
              background: 'transparent',
              fontSize: '14px',
              fontWeight: 700,
              color: activeFilter === tab.type ? '#0284c7' : '#64748b',
              borderBottom: activeFilter === tab.type ? '3px solid #0284c7' : '3px solid transparent',
              cursor: 'pointer',
              marginBottom: '-2px',
              transition: 'all 0.2s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Bookings List */}
      {filteredBookings.length === 0 ? (
        <div
          style={{
            background: 'white',
            borderRadius: '20px',
            border: '1.5px solid #e2e8f0',
            padding: '60px 24px',
            textAlign: 'center',
            boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
          }}
        >
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📂</div>
          <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#334155', marginBottom: '8px' }}>No bookings found</h3>
          <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '24px' }}>
            {activeFilter === 'ALL'
              ? "You haven't made any flight bookings yet."
              : `You do not have any ${activeFilter.toLowerCase()} bookings.`}
          </p>
          <Link
            to="/"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
              color: 'white',
              padding: '12px 24px',
              borderRadius: '10px',
              textDecoration: 'none',
              fontWeight: 700,
              fontSize: '14px',
            }}
          >
            Book Flights Now
          </Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {filteredBookings.map((b) => (
            <div
              key={b.booking_id}
              style={{
                background: 'white',
                borderRadius: '20px',
                border: '1.5px solid #e2e8f0',
                padding: '24px',
                boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
              }}
            >
              {/* Top Row: Ref and Status */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingBottom: '16px',
                  borderBottom: '1px solid #f1f5f9',
                  marginBottom: '16px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#64748b' }}>Booking Reference:</span>
                  <span style={{ fontSize: '16px', fontWeight: 800, color: '#0284c7', fontFamily: 'monospace', letterSpacing: '0.5px' }}>
                    {b.booking_reference}
                  </span>
                </div>
                <span
                  style={{
                    padding: '4px 12px',
                    borderRadius: '20px',
                    fontSize: '12px',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    background:
                      b.computed_status === 'UPCOMING'
                        ? '#fffbeb'
                        : b.computed_status === 'COMPLETED'
                        ? '#ecfdf5'
                        : '#fef2f2',
                    color:
                      b.computed_status === 'UPCOMING'
                        ? '#b45309'
                        : b.computed_status === 'COMPLETED'
                        ? '#047857'
                        : '#b91c1c',
                  }}
                >
                  {b.computed_status}
                </span>
              </div>

              {/* Middle Row: Flight Info */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '20px',
                  marginBottom: '24px',
                }}
              >
                <div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>Airline & Flight</div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>{b.airline}</div>
                  <div style={{ fontSize: '13px', color: '#64748b' }}>Flight Number: {b.flight_id}</div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>Route</div>
                  <div style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a' }}>
                    {b.origin} → {b.destination}
                  </div>
                  <div style={{ fontSize: '13px', color: '#64748b' }}>Class: {b.travel_class}</div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>Date & Time</div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>{formatDate(b.date)}</div>
                  <div style={{ fontSize: '13px', color: '#64748b' }}>
                    {b.departure_time} - {b.arrival_time}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>Seats & Price</div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>{b.number_of_seats} Seats</div>
                  <div style={{ fontSize: '16px', fontWeight: 800, color: '#0284c7' }}>
                    {formatCurrency(b.total_price)}
                  </div>
                </div>
              </div>

              {/* Bottom Row: Actions */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  flexWrap: 'wrap',
                  gap: '10px',
                  paddingTop: '16px',
                  borderTop: '1px solid #f1f5f9',
                }}
              >
                <Link
                  to={`/booking/${b.booking_id}`}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '10px 16px',
                    borderRadius: '10px',
                    border: '1.5px solid #cbd5e1',
                    background: 'white',
                    color: '#475569',
                    fontSize: '13px',
                    fontWeight: 700,
                    textDecoration: 'none',
                    cursor: 'pointer',
                  }}
                >
                  <ExternalLink size={14} /> View Details
                </Link>

                {/* Pay Now — only for PENDING_PAYMENT */}
                {b.status === 'PENDING_PAYMENT' && (
                  <Link
                    to={`/payment`}
                    state={{ booking: b }}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '10px 16px',
                      borderRadius: '10px',
                      border: 'none',
                      background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
                      color: 'white',
                      fontSize: '13px',
                      fontWeight: 700,
                      textDecoration: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    <CreditCard size={14} /> Pay Now
                  </Link>
                )}

                {/* View Ticket — only after payment confirmed */}
                {b.ticket_download_allowed && (
                  <Link
                    to={`/ticket/${b.booking_id}`}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '10px 16px',
                      borderRadius: '10px',
                      border: '1.5px solid #0284c7',
                      background: 'white',
                      color: '#0284c7',
                      fontSize: '13px',
                      fontWeight: 700,
                      textDecoration: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    <Ticket size={14} /> View Ticket
                  </Link>
                )}

                {/* Download Ticket — only after payment confirmed */}
                {b.ticket_download_allowed && (
                  <button
                    onClick={() => handleDownloadTicket(b.booking_id, b.booking_reference)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '10px 16px',
                      borderRadius: '10px',
                      border: 'none',
                      background: '#e0f2fe',
                      color: '#0284c7',
                      fontSize: '13px',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    <FileText size={14} /> Download Ticket
                  </button>
                )}

                {b.computed_status === 'UPCOMING' && (
                  <button
                    disabled={cancellingId === b.booking_id}
                    onClick={() => handleCancelBooking(b.booking_id, b.booking_reference)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '10px 16px',
                      borderRadius: '10px',
                      border: 'none',
                      background: '#fef2f2',
                      color: '#ef4444',
                      fontSize: '13px',
                      fontWeight: 700,
                      cursor: cancellingId === b.booking_id ? 'not-allowed' : 'pointer',
                      opacity: cancellingId === b.booking_id ? 0.6 : 1,
                    }}
                  >
                    <Trash2 size={14} />
                    {cancellingId === b.booking_id ? 'Cancelling...' : 'Cancel Booking'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
