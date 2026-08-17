import React, { useEffect, useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  getAdminStatsApi,
  getAllBookingsApi,
  adminUploadCsvApi,
  adminUploadExcelApi,
  adminCreateFlightApi,
} from "../services/api";
import type {
  AdminStats,
  BookingRecord,
  ImportSummary,
  ManualFlightData,
} from "../services/api";
import { ShieldCheck, Users, Plane, Database, Server, LogOut, CheckCircle, BookOpen, Upload, PlusCircle, FileText, FileSpreadsheet, AlertCircle, CheckCircle2 } from 'lucide-react';
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

  // ── Flight Data Management state ─────────────────────────
  const [showFlightMgmt, setShowFlightMgmt] = useState(false);
  // tabs: 'csv' | 'excel' | 'manual'
  const [flightMgmtTab, setFlightMgmtTab] = useState<'csv' | 'excel' | 'manual'>('csv');

  // CSV upload
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvUploading, setCsvUploading] = useState(false);
  const [csvResult, setCsvResult] = useState<ImportSummary | null>(null);
  const [csvError, setCsvError] = useState('');
  const csvInputRef = useRef<HTMLInputElement>(null);

  // Excel upload
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [excelUploading, setExcelUploading] = useState(false);
  const [excelResult, setExcelResult] = useState<ImportSummary | null>(null);
  const [excelError, setExcelError] = useState('');
  const excelInputRef = useRef<HTMLInputElement>(null);

  // Manual form
  const emptyManualForm: ManualFlightData = {
    flight_id: '', airline: '', origin: '', destination: '',
    date: '', departure_time: '', arrival_time: '',
    price: 0, travel_class: 'Economy', available_seats: 0, total_seats: 180,
  };
  const [manualForm, setManualForm] = useState<ManualFlightData>(emptyManualForm);
  const [manualSubmitting, setManualSubmitting] = useState(false);
  const [manualSuccess, setManualSuccess] = useState('');
  const [manualError, setManualError] = useState('');

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

  // ── Flight management handlers ───────────────────────────

  const handleCsvUpload = async () => {
    if (!csvFile || !adminToken) return;
    setCsvUploading(true);
    setCsvResult(null);
    setCsvError('');
    try {
      const result = await adminUploadCsvApi(csvFile, adminToken);
      setCsvResult(result);
      // Refresh stats so the Active Flights counter updates
      const newStats = await getAdminStatsApi(adminToken);
      setStats(newStats);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'CSV upload failed. Please check your file.';
      setCsvError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setCsvUploading(false);
    }
  };

  const handleExcelUpload = async () => {
    if (!excelFile || !adminToken) return;
    setExcelUploading(true);
    setExcelResult(null);
    setExcelError('');
    try {
      const result = await adminUploadExcelApi(excelFile, adminToken);
      setExcelResult(result);
      const newStats = await getAdminStatsApi(adminToken);
      setStats(newStats);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Excel upload failed. Please check your file.';
      setExcelError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setExcelUploading(false);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminToken) return;
    setManualSubmitting(true);
    setManualSuccess('');
    setManualError('');
    try {
      const result = await adminCreateFlightApi(manualForm, adminToken);
      setManualSuccess(`✓ ${result.message}`);
      setManualForm(emptyManualForm);
      const newStats = await getAdminStatsApi(adminToken);
      setStats(newStats);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (Array.isArray(detail)) {
        setManualError(detail.map((d: any) => d.msg || JSON.stringify(d)).join('; '));
      } else {
        setManualError(typeof detail === 'string' ? detail : 'Failed to create flight.');
      }
    } finally {
      setManualSubmitting(false);
    }
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

        {/* ── Action Buttons ── */}
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '24px' }}>
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

          <button
            id="flight-mgmt-btn"
            onClick={() => setShowFlightMgmt(!showFlightMgmt)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              borderRadius: '12px',
              background: showFlightMgmt
                ? 'linear-gradient(135deg, #059669, #047857)'
                : 'linear-gradient(135deg, #10b981, #059669)',
              border: 'none',
              color: 'white',
              fontWeight: 700,
              fontSize: '15px',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(16,185,129,0.3)',
              transition: 'all 0.2s',
            }}
          >
            <Plane size={18} />
            {showFlightMgmt ? 'Hide Flight Management' : 'Flight Data Management'}
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

        {/* ── Flight Data Management Section ── */}
        {showFlightMgmt && (
          <div
            id="flight-management-section"
            style={{
              background: 'white',
              borderRadius: '20px',
              padding: '28px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
              marginBottom: '32px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
              <h3
                style={{
                  fontSize: '18px',
                  fontWeight: 700,
                  color: '#0f172a',
                  margin: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <Plane size={20} color="#10b981" />
                Flight Data Management
              </h3>

              {/* Tabs */}
              <div
                style={{
                  display: 'flex',
                  gap: '8px',
                  background: '#f1f5f9',
                  padding: '4px',
                  borderRadius: '12px',
                }}
              >
                <button
                  type="button"
                  id="tab-csv"
                  onClick={() => setFlightMgmtTab('csv')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: flightMgmtTab === 'csv' ? 'white' : 'transparent',
                    color: flightMgmtTab === 'csv' ? '#0f172a' : '#64748b',
                    boxShadow: flightMgmtTab === 'csv' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                    transition: 'all 0.15s',
                  }}
                >
                  <FileText size={16} color={flightMgmtTab === 'csv' ? '#0284c7' : '#64748b'} />
                  Upload CSV
                </button>

                <button
                  type="button"
                  id="tab-excel"
                  onClick={() => setFlightMgmtTab('excel')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: flightMgmtTab === 'excel' ? 'white' : 'transparent',
                    color: flightMgmtTab === 'excel' ? '#0f172a' : '#64748b',
                    boxShadow: flightMgmtTab === 'excel' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                    transition: 'all 0.15s',
                  }}
                >
                  <FileSpreadsheet size={16} color={flightMgmtTab === 'excel' ? '#16a34a' : '#64748b'} />
                  Upload Excel (.xlsx/.xls)
                </button>

                <button
                  type="button"
                  id="tab-manual"
                  onClick={() => setFlightMgmtTab('manual')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: flightMgmtTab === 'manual' ? 'white' : 'transparent',
                    color: flightMgmtTab === 'manual' ? '#0f172a' : '#64748b',
                    boxShadow: flightMgmtTab === 'manual' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                    transition: 'all 0.15s',
                  }}
                >
                  <PlusCircle size={16} color={flightMgmtTab === 'manual' ? '#7c3aed' : '#64748b'} />
                  Add Flight Manually
                </button>
              </div>
            </div>

            {/* ── TAB 1: CSV UPLOAD ── */}
            {flightMgmtTab === 'csv' && (
              <div>
                <div
                  style={{
                    border: '2px dashed #cbd5e1',
                    borderRadius: '16px',
                    padding: '32px 20px',
                    textAlign: 'center',
                    background: '#f8fafc',
                    marginBottom: '20px',
                  }}
                >
                  <FileText size={40} color="#0284c7" style={{ marginBottom: '12px' }} />
                  <p style={{ margin: '0 0 8px 0', fontSize: '15px', fontWeight: 600, color: '#1e293b' }}>
                    Select a CSV flight dataset file
                  </p>
                  <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: '#64748b' }}>
                    Supported format: <code>.csv</code> (UTF-8 encoded)
                  </p>

                  <input
                    ref={csvInputRef}
                    id="csv-file-input"
                    type="file"
                    accept=".csv"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setCsvFile(e.target.files[0]);
                        setCsvResult(null);
                        setCsvError('');
                      }
                    }}
                    style={{ display: 'none' }}
                  />

                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', alignItems: 'center' }}>
                    <button
                      type="button"
                      id="select-csv-btn"
                      onClick={() => csvInputRef.current?.click()}
                      style={{
                        padding: '10px 20px',
                        borderRadius: '10px',
                        background: '#e0f2fe',
                        border: '1px solid #bae6fd',
                        color: '#0284c7',
                        fontWeight: 600,
                        fontSize: '14px',
                        cursor: 'pointer',
                      }}
                    >
                      {csvFile ? 'Change File' : 'Browse CSV File'}
                    </button>

                    {csvFile && (
                      <button
                        type="button"
                        id="upload-csv-btn"
                        onClick={handleCsvUpload}
                        disabled={csvUploading}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '10px 20px',
                          borderRadius: '10px',
                          background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                          border: 'none',
                          color: 'white',
                          fontWeight: 700,
                          fontSize: '14px',
                          cursor: csvUploading ? 'not-allowed' : 'pointer',
                          opacity: csvUploading ? 0.7 : 1,
                        }}
                      >
                        <Upload size={16} />
                        {csvUploading ? 'Importing CSV...' : 'Import CSV Data'}
                      </button>
                    )}
                  </div>

                  {csvFile && (
                    <div style={{ marginTop: '12px', fontSize: '13px', color: '#0f172a', fontWeight: 600 }}>
                      Selected: <span style={{ color: '#0284c7' }}>{csvFile.name}</span> ({(csvFile.size / 1024).toFixed(1)} KB)
                    </div>
                  )}
                </div>

                {/* CSV Format helper */}
                <div
                  style={{
                    background: '#f8fafc',
                    borderRadius: '12px',
                    padding: '14px 18px',
                    border: '1px solid #e2e8f0',
                    fontSize: '12px',
                    color: '#475569',
                    marginBottom: '20px',
                  }}
                >
                  <strong style={{ color: '#0f172a' }}>Expected Columns:</strong> flight_id, airline, origin, destination, date, departure_time, arrival_time, price, travel_class, available_seats, total_seats (optional)
                </div>

                {/* CSV Error */}
                {csvError && (
                  <div
                    style={{
                      padding: '16px',
                      background: '#fef2f2',
                      border: '1px solid #fecaca',
                      color: '#dc2626',
                      borderRadius: '12px',
                      marginBottom: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '14px',
                    }}
                  >
                    <AlertCircle size={18} />
                    <span>{csvError}</span>
                  </div>
                )}

                {/* CSV Result */}
                {csvResult && <ImportResultView result={csvResult} />}
              </div>
            )}

            {/* ── TAB 2: EXCEL UPLOAD ── */}
            {flightMgmtTab === 'excel' && (
              <div>
                <div
                  style={{
                    border: '2px dashed #cbd5e1',
                    borderRadius: '16px',
                    padding: '32px 20px',
                    textAlign: 'center',
                    background: '#f8fafc',
                    marginBottom: '20px',
                  }}
                >
                  <FileSpreadsheet size={40} color="#16a34a" style={{ marginBottom: '12px' }} />
                  <p style={{ margin: '0 0 8px 0', fontSize: '15px', fontWeight: 600, color: '#1e293b' }}>
                    Select an Excel flight dataset file
                  </p>
                  <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: '#64748b' }}>
                    Supported formats: <code>.xlsx</code>, <code>.xls</code>
                  </p>

                  <input
                    ref={excelInputRef}
                    id="excel-file-input"
                    type="file"
                    accept=".xlsx, .xls"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setExcelFile(e.target.files[0]);
                        setExcelResult(null);
                        setExcelError('');
                      }
                    }}
                    style={{ display: 'none' }}
                  />

                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', alignItems: 'center' }}>
                    <button
                      type="button"
                      id="select-excel-btn"
                      onClick={() => excelInputRef.current?.click()}
                      style={{
                        padding: '10px 20px',
                        borderRadius: '10px',
                        background: '#dcfce7',
                        border: '1px solid #bbf7d0',
                        color: '#16a34a',
                        fontWeight: 600,
                        fontSize: '14px',
                        cursor: 'pointer',
                      }}
                    >
                      {excelFile ? 'Change File' : 'Browse Excel File'}
                    </button>

                    {excelFile && (
                      <button
                        type="button"
                        id="upload-excel-btn"
                        onClick={handleExcelUpload}
                        disabled={excelUploading}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '10px 20px',
                          borderRadius: '10px',
                          background: 'linear-gradient(135deg, #16a34a, #15803d)',
                          border: 'none',
                          color: 'white',
                          fontWeight: 700,
                          fontSize: '14px',
                          cursor: excelUploading ? 'not-allowed' : 'pointer',
                          opacity: excelUploading ? 0.7 : 1,
                        }}
                      >
                        <Upload size={16} />
                        {excelUploading ? 'Importing Excel...' : 'Import Excel Data'}
                      </button>
                    )}
                  </div>

                  {excelFile && (
                    <div style={{ marginTop: '12px', fontSize: '13px', color: '#0f172a', fontWeight: 600 }}>
                      Selected: <span style={{ color: '#16a34a' }}>{excelFile.name}</span> ({(excelFile.size / 1024).toFixed(1)} KB)
                    </div>
                  )}
                </div>

                {/* Excel Format helper */}
                <div
                  style={{
                    background: '#f8fafc',
                    borderRadius: '12px',
                    padding: '14px 18px',
                    border: '1px solid #e2e8f0',
                    fontSize: '12px',
                    color: '#475569',
                    marginBottom: '20px',
                  }}
                >
                  <strong style={{ color: '#0f172a' }}>Expected Columns:</strong> flight_id, airline, origin, destination, date, departure_time, arrival_time, price, travel_class, available_seats, total_seats (optional)
                </div>

                {/* Excel Error */}
                {excelError && (
                  <div
                    style={{
                      padding: '16px',
                      background: '#fef2f2',
                      border: '1px solid #fecaca',
                      color: '#dc2626',
                      borderRadius: '12px',
                      marginBottom: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '14px',
                    }}
                  >
                    <AlertCircle size={18} />
                    <span>{excelError}</span>
                  </div>
                )}

                {/* Excel Result */}
                {excelResult && <ImportResultView result={excelResult} />}
              </div>
            )}

            {/* ── TAB 3: MANUAL FLIGHT ENTRY ── */}
            {flightMgmtTab === 'manual' && (
              <form onSubmit={handleManualSubmit}>
                {manualSuccess && (
                  <div
                    style={{
                      padding: '14px 18px',
                      background: '#ecfdf5',
                      border: '1px solid #a7f3d0',
                      color: '#059669',
                      borderRadius: '12px',
                      marginBottom: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontWeight: 600,
                      fontSize: '14px',
                    }}
                  >
                    <CheckCircle2 size={18} />
                    <span>{manualSuccess}</span>
                  </div>
                )}

                {manualError && (
                  <div
                    style={{
                      padding: '14px 18px',
                      background: '#fef2f2',
                      border: '1px solid #fecaca',
                      color: '#dc2626',
                      borderRadius: '12px',
                      marginBottom: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '14px',
                    }}
                  >
                    <AlertCircle size={18} />
                    <span>{manualError}</span>
                  </div>
                )}

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '16px',
                    marginBottom: '24px',
                  }}
                >
                  {/* Flight ID */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Flight ID *
                    </label>
                    <input
                      id="manual-flight-id"
                      type="text"
                      placeholder="e.g. AI101"
                      required
                      value={manualForm.flight_id}
                      onChange={(e) => setManualForm({ ...manualForm, flight_id: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  {/* Airline */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Airline *
                    </label>
                    <input
                      id="manual-airline"
                      type="text"
                      placeholder="e.g. Air India"
                      required
                      value={manualForm.airline}
                      onChange={(e) => setManualForm({ ...manualForm, airline: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  {/* Origin */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Origin *
                    </label>
                    <input
                      id="manual-origin"
                      type="text"
                      placeholder="e.g. Chennai"
                      required
                      value={manualForm.origin}
                      onChange={(e) => setManualForm({ ...manualForm, origin: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  {/* Destination */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Destination *
                    </label>
                    <input
                      id="manual-destination"
                      type="text"
                      placeholder="e.g. Delhi"
                      required
                      value={manualForm.destination}
                      onChange={(e) => setManualForm({ ...manualForm, destination: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  {/* Date */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Date (YYYY-MM-DD) *
                    </label>
                    <input
                      id="manual-date"
                      type="date"
                      required
                      value={manualForm.date}
                      onChange={(e) => setManualForm({ ...manualForm, date: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  {/* Departure Time */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Departure Time (HH:MM) *
                    </label>
                    <input
                      id="manual-departure-time"
                      type="text"
                      placeholder="06:00"
                      required
                      value={manualForm.departure_time}
                      onChange={(e) => setManualForm({ ...manualForm, departure_time: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  {/* Arrival Time */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Arrival Time (HH:MM) *
                    </label>
                    <input
                      id="manual-arrival-time"
                      type="text"
                      placeholder="09:00"
                      required
                      value={manualForm.arrival_time}
                      onChange={(e) => setManualForm({ ...manualForm, arrival_time: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  {/* Price */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Price (INR) *
                    </label>
                    <input
                      id="manual-price"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="5500"
                      required
                      value={manualForm.price || ''}
                      onChange={(e) => setManualForm({ ...manualForm, price: parseFloat(e.target.value) || 0 })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  {/* Travel Class */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Travel Class *
                    </label>
                    <select
                      id="manual-travel-class"
                      value={manualForm.travel_class}
                      onChange={(e) => setManualForm({ ...manualForm, travel_class: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        background: 'white',
                        boxSizing: 'border-box',
                      }}
                    >
                      <option value="Economy">Economy</option>
                      <option value="Business">Business</option>
                      <option value="First">First</option>
                    </select>
                  </div>

                  {/* Available Seats */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Available Seats *
                    </label>
                    <input
                      id="manual-available-seats"
                      type="number"
                      min="0"
                      placeholder="180"
                      required
                      value={manualForm.available_seats || ''}
                      onChange={(e) => setManualForm({ ...manualForm, available_seats: parseInt(e.target.value, 10) || 0 })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>

                  {/* Total Seats */}
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
                      Total Seats (Optional)
                    </label>
                    <input
                      id="manual-total-seats"
                      type="number"
                      min="0"
                      placeholder="180"
                      value={manualForm.total_seats ?? 180}
                      onChange={(e) => setManualForm({ ...manualForm, total_seats: parseInt(e.target.value, 10) || 180 })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        border: '1px solid #cbd5e1',
                        fontSize: '14px',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  id="submit-flight-btn"
                  disabled={manualSubmitting}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '12px 28px',
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, #7c3aed, #6d28d9)',
                    border: 'none',
                    color: 'white',
                    fontWeight: 700,
                    fontSize: '15px',
                    cursor: manualSubmitting ? 'not-allowed' : 'pointer',
                    boxShadow: '0 4px 14px rgba(124,58,237,0.3)',
                    opacity: manualSubmitting ? 0.7 : 1,
                  }}
                >
                  <PlusCircle size={18} />
                  {manualSubmitting ? 'Adding Flight...' : 'Add Flight Record'}
                </button>
              </form>
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

// ── Helper Component for Displaying Import Results ─────────────────────────

function ImportResultView({ result }: { result: ImportSummary }) {
  return (
    <div
      id="import-result-view"
      style={{
        background: '#f8fafc',
        borderRadius: '16px',
        padding: '24px',
        border: '1px solid #e2e8f0',
        marginTop: '16px',
      }}
    >
      <h4
        style={{
          margin: '0 0 16px 0',
          fontSize: '16px',
          fontWeight: 700,
          color: '#0f172a',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <CheckCircle size={18} color="#0284c7" />
        Import Result Summary
      </h4>

      {/* Stats pills */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '12px',
          marginBottom: '20px',
        }}
      >
        <div
          style={{
            background: 'white',
            padding: '12px 16px',
            borderRadius: '12px',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748b' }}>Total Rows</div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a' }}>{result.total_rows}</div>
        </div>

        <div
          style={{
            background: 'white',
            padding: '12px 16px',
            borderRadius: '12px',
            border: '1px solid #bbf7d0',
          }}
        >
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#16a34a' }}>Successfully Imported</div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#16a34a' }}>{result.imported}</div>
        </div>

        <div
          style={{
            background: 'white',
            padding: '12px 16px',
            borderRadius: '12px',
            border: '1px solid #fecaca',
          }}
        >
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#dc2626' }}>Failed Records</div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#dc2626' }}>{result.failed}</div>
        </div>
      </div>

      {/* Row-by-row errors */}
      {result.errors && result.errors.length > 0 && (
        <div style={{ marginTop: '16px' }}>
          <h5 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 700, color: '#dc2626' }}>
            Failed Row Details ({result.errors.length}):
          </h5>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '260px', overflowY: 'auto' }}>
            {result.errors.map((err, idx) => (
              <div
                key={idx}
                style={{
                  background: '#fef2f2',
                  border: '1px solid #fecaca',
                  borderRadius: '10px',
                  padding: '10px 14px',
                  fontSize: '13px',
                }}
              >
                <strong style={{ color: '#991b1b' }}>Row {err.row}:</strong>
                <ul style={{ margin: '4px 0 0 0', paddingLeft: '20px', color: '#b91c1c' }}>
                  {err.errors.map((msg, mIdx) => (
                    <li key={mIdx}>{msg}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

