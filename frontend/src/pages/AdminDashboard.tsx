import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getAdminStatsApi, getAllBookingsApi } from "../services/api";
import type {
  AdminStats,
  BookingRecord,
} from "../services/api";
import { ShieldCheck, Users, Plane, Database, Server, LogOut, CheckCircle, BookOpen } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function AdminDashboard() {
  const { admin, adminToken, logoutAdmin } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // ── Bookings state ──────────────────────────────────────
  const [showBookings, setShowBookings] = useState(false);
  const [bookings, setBookings] = useState<BookingRecord[]>([]);
  const [loadingBookings, setLoadingBookings] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingsFetched, setBookingsFetched] = useState(false);

  // ── Fetch dashboard stats on mount ──────────────────────
  useEffect(() => {
    const fetchStats = async () => {
      if (!adminToken) return;
      try {
        const data = await getAdminStatsApi(adminToken);
        setStats(data);
      } catch (err: any) {
        setError('Failed to load admin dashboard statistics.');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [adminToken]);

  const handleLogout = () => {
    logoutAdmin();
    navigate('/admin/login');
  };

  // ── Bookings helpers ─────────────────────────────────────
  const fetchBookings = async () => {
    if (!adminToken) return;
    setLoadingBookings(true);
    setBookingError('');
    try {
      const data = await getAllBookingsApi(adminToken);
      setBookings(data.bookings);
      setBookingsFetched(true);
    } catch (err: any) {
      setBookingError('Failed to load bookings.');
    } finally {
      setLoadingBookings(false);
    }
  };

  const handleToggleBookings = () => {
    if (showBookings) {
      // Simply hide — do NOT re-fetch
      setShowBookings(false);
    } else {
      setShowBookings(true);
      // Only call the API if data has not been loaded yet
      if (!bookingsFetched) {
        fetchBookings();
      }
    }
  };

  const handleRetryBookings = () => {
    setBookingsFetched(false);
    fetchBookings();
  };

  // ── Render ───────────────────────────────────────────────
  return (
    <div
      style={{
        minHeight: 'calc(100vh - 64px)',
        background: '#f8fafc',
        padding: '32px 24px',
      }}
    >
      <div style={{ maxWidth: '1100px', margin: '0 auto' }}>

        {/* ── Dashboard Header ── */}
        <div
          style={{
            background: 'linear-gradient(135deg, #0f172a, #1e293b)',
            borderRadius: '20px',
            padding: '28px 32px',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '32px',
            boxShadow: '0 8px 24px rgba(15,23,42,0.15)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div
              style={{
                width: '52px',
                height: '52px',
                background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                borderRadius: '16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ShieldCheck size={28} color="white" />
            </div>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: 800, margin: 0 }}>
                Admin Control Panel
              </h1>
              <p style={{ color: '#94a3b8', fontSize: '14px', marginTop: '4px', margin: 0 }}>
                Welcome back, {admin?.name || 'Administrator'} ({admin?.email})
              </p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 18px',
              borderRadius: '12px',
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid #ef4444',
              color: '#fca5a5',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <LogOut size={16} />
            Logout Admin
          </button>
        </div>

        {/* ── Stats error ── */}
        {error && (
          <div
            style={{
              padding: '16px',
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#dc2626',
              borderRadius: '12px',
              marginBottom: '24px',
            }}
          >
            {error}
          </div>
        )}

        {/* ── Stats Grid ── */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '20px',
            marginBottom: '32px',
          }}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#64748b' }}>Registered Users</span>
              <div style={{ width: '36px', height: '36px', background: '#e0f2fe', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Users size={20} color="#0284c7" />
              </div>
            </div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#0f172a' }}>
              {loading ? '...' : stats?.total_users || 0}
            </div>
          </div>

          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#64748b' }}>System Administrators</span>
              <div style={{ width: '36px', height: '36px', background: '#e0e7ff', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <ShieldCheck size={20} color="#4f46e5" />
              </div>
            </div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#0f172a' }}>
              {loading ? '...' : stats?.total_admins || 0}
            </div>
          </div>

          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#64748b' }}>Active Flights</span>
              <div style={{ width: '36px', height: '36px', background: '#f0fdf4', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Plane size={20} color="#16a34a" />
              </div>
            </div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#0f172a' }}>
              {loading ? '...' : stats?.total_flights || 0}
            </div>
          </div>

          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#64748b' }}>MCP Server Status</span>
              <div style={{ width: '36px', height: '36px', background: '#fef3c7', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Server size={20} color="#d97706" />
              </div>
            </div>
            <div style={{ fontSize: '18px', fontWeight: 800, color: '#16a34a', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={18} color="#16a34a" />
              {loading ? '...' : stats?.mcp_server || 'Connected'}
            </div>
          </div>
        </div>

        {/* ── Show / Hide Bookings Button ── */}
        <div style={{ marginBottom: '24px' }}>
          <button
            id="show-bookings-btn"
            onClick={handleToggleBookings}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              borderRadius: '12px',
              background: showBookings
                ? 'linear-gradient(135deg, #7c3aed, #6d28d9)'
                : 'linear-gradient(135deg, #0ea5e9, #0284c7)',
              border: 'none',
              color: 'white',
              fontWeight: 700,
              fontSize: '15px',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(14,165,233,0.3)',
              transition: 'all 0.2s',
            }}
          >
            <BookOpen size={18} />
            {showBookings ? 'Hide Bookings' : 'Show Bookings'}
          </button>
        </div>

        {/* ── Bookings Section ── */}
        {showBookings && (
          <div
            style={{
              background: 'white',
              borderRadius: '20px',
              padding: '28px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
              marginBottom: '32px',
            }}
          >
            <h3
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: '#0f172a',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <BookOpen size={20} color="#0ea5e9" />
              All Bookings
            </h3>

            {/* Loading indicator */}
            {loadingBookings && (
              <div
                style={{
                  padding: '32px',
                  textAlign: 'center',
                  color: '#64748b',
                  fontSize: '15px',
                  fontWeight: 500,
                }}
              >
                ⏳ Loading bookings…
              </div>
            )}

            {/* Error with Retry */}
            {!loadingBookings && bookingError && (
              <div
                style={{
                  padding: '16px',
                  background: '#fef2f2',
                  border: '1px solid #fecaca',
                  color: '#dc2626',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span>{bookingError}</span>
                <button
                  onClick={handleRetryBookings}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '8px',
                    background: '#dc2626',
                    color: 'white',
                    border: 'none',
                    fontWeight: 600,
                    fontSize: '13px',
                    cursor: 'pointer',
                  }}
                >
                  Retry
                </button>
              </div>
            )}

            {/* Empty state */}
            {!loadingBookings && !bookingError && bookings.length === 0 && (
              <div
                style={{
                  padding: '32px',
                  textAlign: 'center',
                  color: '#64748b',
                  fontSize: '15px',
                }}
              >
                No bookings found.
              </div>
            )}

            {/* Bookings table */}
            {!loadingBookings && !bookingError && bookings.length > 0 && (
              <div style={{ overflowX: 'auto' }}>
                <table
                  style={{
                    width: '100%',
                    borderCollapse: 'collapse',
                    fontSize: '14px',
                  }}
                >
                  <thead>
                    <tr
                      style={{
                        background: '#f1f5f9',
                        borderBottom: '2px solid #e2e8f0',
                      }}
                    >
                      {[
                        'Reference',
                        'User ID',
                        'Flight ID',
                        'Seats',
                        'Total Price',
                        'Status',
                        'Booking Date',
                      ].map((col) => (
                        <th
                          key={col}
                          style={{
                            padding: '12px 16px',
                            textAlign: 'left',
                            fontWeight: 700,
                            color: '#475569',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {bookings.map((b) => (
                      <tr
                        key={b.booking_id}
                        style={{
                          borderBottom: '1px solid #f1f5f9',
                          transition: 'background 0.15s',
                        }}
                        onMouseEnter={(e) =>
                          ((e.currentTarget as HTMLTableRowElement).style.background = '#f8fafc')
                        }
                        onMouseLeave={(e) =>
                          ((e.currentTarget as HTMLTableRowElement).style.background = 'transparent')
                        }
                      >
                        <td
                          style={{
                            padding: '12px 16px',
                            fontFamily: 'monospace',
                            fontWeight: 600,
                            color: '#0f172a',
                          }}
                        >
                          {b.booking_reference}
                        </td>
                        <td style={{ padding: '12px 16px', color: '#334155' }}>{b.user_id}</td>
                        <td style={{ padding: '12px 16px', color: '#334155', fontWeight: 600 }}>
                          {b.flight_id}
                        </td>
                        <td style={{ padding: '12px 16px', color: '#334155' }}>{b.number_of_seats}</td>
                        <td style={{ padding: '12px 16px', color: '#334155', fontWeight: 600 }}>
                          ₹{b.total_price.toLocaleString('en-IN')}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <span
                            style={{
                              padding: '4px 10px',
                              borderRadius: '20px',
                              fontSize: '12px',
                              fontWeight: 700,
                              background:
                                b.status === 'CONFIRMED'
                                  ? '#dcfce7'
                                  : b.status === 'CANCELLED'
                                  ? '#fef2f2'
                                  : '#f1f5f9',
                              color:
                                b.status === 'CONFIRMED'
                                  ? '#16a34a'
                                  : b.status === 'CANCELLED'
                                  ? '#dc2626'
                                  : '#64748b',
                            }}
                          >
                            {b.status}
                          </span>
                        </td>
                        <td style={{ padding: '12px 16px', color: '#64748b', whiteSpace: 'nowrap' }}>
                          {b.created_at}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── System Overview Card ── */}
        <div
          style={{
            background: 'white',
            borderRadius: '20px',
            padding: '28px',
            border: '1px solid #e2e8f0',
            boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
          }}
        >
          <h3
            style={{
              fontSize: '18px',
              fontWeight: 700,
              color: '#0f172a',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <Database size={20} color="#0ea5e9" /> System Integration Architecture
          </h3>

          <div
            style={{
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              padding: '20px',
              fontFamily: 'monospace',
              fontSize: '13px',
              lineHeight: '1.6',
              color: '#334155',
            }}
          >
            <div>✓ FastAPI Backend API running</div>
            <div>✓ JWT Admin Authorization middleware active</div>
            <div>✓ PostgreSQL Database / SQLAlchemy Models connected</div>
            <div>✓ Model Context Protocol (MCP) Server bridge active</div>
            <div>✓ AI Natural Language Flight Search Agent active</div>
          </div>
        </div>

      </div>
    </div>
  );
}
