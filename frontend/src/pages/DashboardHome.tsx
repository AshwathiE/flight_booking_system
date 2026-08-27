import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getMyBookingsApi, downloadTicketPdfApi } from '../services/api';
import { formatDate, formatCurrency } from '../services/flightService';
import { Briefcase, Calendar, CheckCircle2, XCircle, ChevronRight, Search, FileText, CreditCard } from 'lucide-react';

export default function DashboardHome() {
  const { user, userToken } = useAuth();
  const navigate = useNavigate();
  const [bookings, setBookings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    upcoming: 0,
    completed: 0,
    cancelled: 0,
  });

  useEffect(() => {
    const fetchBookings = async () => {
      if (!userToken) return;
      try {
        const response = await getMyBookingsApi(userToken);
        if (response.success && response.bookings) {
          setBookings(response.bookings);
          
          // Calculate stats based on computed_status
          const total = response.bookings.length;
          const upcoming = response.bookings.filter((b: any) => b.computed_status === 'UPCOMING').length;
          const completed = response.bookings.filter((b: any) => b.computed_status === 'COMPLETED').length;
          const cancelled = response.bookings.filter((b: any) => b.computed_status === 'CANCELLED').length;
          
          setStats({ total, upcoming, completed, cancelled });
        }
      } catch (err) {
        console.error('Failed to fetch bookings for dashboard stats', err);
      } finally {
        setLoading(false);
      }
    };

    fetchBookings();
  }, [userToken]);

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
      alert('Failed to download PDF ticket. Please try again.');
    }
  };

  const statCards = [
    { title: 'Total Bookings', value: stats.total, color: '#0ea5e9', bg: '#f0f9ff', icon: Briefcase },
    { title: 'Upcoming Trips', value: stats.upcoming, color: '#f59e0b', bg: '#fffbeb', icon: Calendar },
    { title: 'Completed Flights', value: stats.completed, color: '#10b981', bg: '#ecfdf5', icon: CheckCircle2 },
    { title: 'Cancelled Bookings', value: stats.cancelled, color: '#ef4444', bg: '#fef2f2', icon: XCircle },
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <div style={{ textAlign: 'center', color: '#64748b' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid #e2e8f0', borderTopColor: '#0ea5e9', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px auto' }} />
          <span>Loading dashboard summary...</span>
        </div>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.4s ease both' }}>
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%)',
          borderRadius: '24px',
          padding: '40px',
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          marginBottom: '32px',
          boxShadow: '0 10px 30px rgba(15,23,42,0.08)',
        }}
      >
        <div style={{ position: 'relative', zIndex: 1, maxWidth: '600px' }}>
          <h1 style={{ fontSize: 'clamp(24px, 4vw, 32px)', fontWeight: 900, marginBottom: '8px', letterSpacing: '-0.5px' }}>
            Welcome back, {user?.name}!
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: '1.6', marginBottom: '24px' }}>
            Manage your itineraries, download boarding passes, or schedule your next destination using our AI assistant.
          </p>
          <Link
            to="/"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              background: 'linear-gradient(135deg, #38bdf8, #0ea5e9)',
              color: 'white',
              padding: '12px 24px',
              borderRadius: '12px',
              textDecoration: 'none',
              fontWeight: 700,
              fontSize: '14px',
              boxShadow: '0 4px 14px rgba(14,165,233,0.4)',
            }}
          >
            <Search size={16} />
            Search New Flights
          </Link>
        </div>
        {/* Background Plane Decoration */}
        <div style={{ position: 'absolute', right: '40px', bottom: '20px', fontSize: '120px', opacity: 0.05, userSelect: 'none' }}>
          ✈️
        </div>
      </div>

      {/* Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '40px' }}>
        {statCards.map((c) => {
          const Icon = c.icon;
          return (
            <div
              key={c.title}
              style={{
                background: 'white',
                borderRadius: '16px',
                padding: '24px',
                border: '1.5px solid #e2e8f0',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
              }}
            >
              <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: c.bg, display: 'flex', alignItems: 'center', justifyContext: 'center', justifyContent: 'center' }}>
                <Icon size={22} color={c.color} />
              </div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#64748b', marginBottom: '4px' }}>{c.title}</div>
                <div style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a' }}>{c.value}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Bookings Section */}
      <div style={{ background: 'white', borderRadius: '20px', border: '1.5px solid #e2e8f0', padding: '28px', boxShadow: '0 2px 12px rgba(0,0,0,0.02)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>Recent Bookings</h2>
          <Link
            to="/my-bookings"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '13px',
              fontWeight: 700,
              color: '#0284c7',
              textDecoration: 'none',
            }}
          >
            View All Bookings <ChevronRight size={16} />
          </Link>
        </div>

        {bookings.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b' }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>✈️</div>
            <p style={{ fontSize: '14px', marginBottom: '16px' }}>You haven't made any flight bookings yet.</p>
            <Link to="/" style={{ color: '#0ea5e9', fontWeight: 600, textDecoration: 'none' }}>
              Book your first flight →
            </Link>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {bookings.slice(0, 3).map((b) => (
              <div
                key={b.booking_id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '20px',
                  borderRadius: '14px',
                  border: '1px solid #e2e8f0',
                  background: '#f8fafc',
                }}
                className="booking-row"
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: '#64748b' }}>Ref:</span>
                    <span style={{ fontSize: '14px', fontWeight: 800, color: '#0284c7' }}>{b.booking_reference}</span>
                    <span
                      style={{
                        padding: '3px 10px',
                        borderRadius: '20px',
                        fontSize: '11px',
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
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
                    {b.origin} → {b.destination}
                  </div>
                  <div style={{ fontSize: '13px', color: '#64748b' }}>
                    {b.airline} ({b.flight_id}) • {formatDate(b.date)} • {b.departure_time}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', marginRight: '16px' }}>
                    {formatCurrency(b.total_price)}
                  </span>

                  <Link
                    to={`/booking/${b.booking_id}`}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '8px',
                      border: '1.5px solid #cbd5e1',
                      background: 'white',
                      color: '#475569',
                      fontSize: '13px',
                      fontWeight: 600,
                      textDecoration: 'none',
                      display: 'inline-flex',
                      alignItems: 'center',
                    }}
                  >
                    Details
                  </Link>

                  {/* Pay Now — only when payment pending */}
                  {b.status === 'PENDING_PAYMENT' && (
                    <Link
                      to={`/payment`}
                      state={{ booking: b }}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        border: 'none',
                        background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
                        color: 'white',
                        fontSize: '13px',
                        fontWeight: 600,
                        textDecoration: 'none',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <CreditCard size={14} /> Pay
                    </Link>
                  )}

                  {/* PDF Download — only when ticket is downloadable */}
                  {b.ticket_download_allowed && (
                    <button
                      onClick={() => handleDownloadTicket(b.booking_id, b.booking_reference)}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        border: 'none',
                        background: '#e0f2fe',
                        color: '#0284c7',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <FileText size={14} /> PDF
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style>{`
        @media (max-width: 768px) {
          .booking-row {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 16px !important;
          }
          .booking-row > div:last-child {
            width: 100% !important;
            justify-content: space-between !important;
          }
        }
      `}</style>
    </div>
  );
}
