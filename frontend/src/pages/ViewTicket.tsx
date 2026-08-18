import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getBookingDetailsApi, downloadTicketPdfApi } from '../services/api';
import { formatDate } from '../services/flightService';
import { ArrowLeft, Download, Plane, User, Calendar, Armchair, ShieldCheck, Printer } from 'lucide-react';

export default function ViewTicket() {
  const { bookingId } = useParams<{ bookingId: string }>();
  const { user, userToken } = useAuth();

  const [booking, setBooking] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          setError(data.message || 'Failed to retrieve booking.');
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

  const getAirportCode = (city: string) => {
    if (!city) return '???';
    const map: Record<string, string> = {
      chennai: 'MAA',
      delhi: 'DEL',
      mumbai: 'BOM',
      bengaluru: 'BLR',
      bangalore: 'BLR',
      kolkata: 'CCU',
      hyderabad: 'HYD',
      coimbatore: 'CJB',
      kochi: 'COK',
      pune: 'PNQ',
    };
    return map[city.toLowerCase().trim()] || city.slice(0, 3).toUpperCase();
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <div style={{ textAlign: 'center', color: '#64748b' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid #e2e8f0', borderTopColor: '#0ea5e9', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px auto' }} />
          <span>Loading ticket...</span>
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div style={{ maxWidth: '640px', margin: '0 auto', padding: '20px' }}>
        <div style={{ marginBottom: '24px' }}>
          <Link to="/my-bookings" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 600, color: '#64748b', textDecoration: 'none' }}>
            <ArrowLeft size={16} /> Back to My Bookings
          </Link>
        </div>
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '24px', borderRadius: '16px', textAlign: 'center' }}>
          <p style={{ fontWeight: 700, fontSize: '16px', marginBottom: '8px' }}>Error Loading Ticket</p>
          <p style={{ fontSize: '14px' }}>{error || 'Flight ticket could not be found.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '780px', margin: '0 auto', animation: 'fadeIn 0.4s ease both' }}>
      {/* Header Panel */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <Link to="/my-bookings" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 600, color: '#64748b', textDecoration: 'none', marginBottom: '8px' }}>
            <ArrowLeft size={16} /> Back to My Bookings
          </Link>
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a' }}>View Boarding Pass</h1>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => window.print()}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 18px',
              borderRadius: '10px',
              border: '1.5px solid #cbd5e1',
              background: 'white',
              color: '#475569',
              fontSize: '13px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            <Printer size={16} /> Print Boarding Pass
          </button>
          <button
            onClick={handleDownloadTicket}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 18px',
              borderRadius: '10px',
              border: 'none',
              background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
              color: 'white',
              fontSize: '13px',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(14,165,233,0.3)',
            }}
          >
            <Download size={16} /> Download PDF
          </button>
        </div>
      </div>

      {/* Boarding Pass Layout */}
      <div
        style={{
          background: 'white',
          borderRadius: '24px',
          border: '2px solid #e2e8f0',
          boxShadow: '0 10px 30px rgba(0,0,0,0.04)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
        className="ticket-card"
      >
        {/* Boarding Pass Header banner */}
        <div
          style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%)',
            padding: '24px 32px',
            color: 'white',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '4px dashed #e2e8f0',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: '#0ea5e9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Plane size={18} color="white" />
            </div>
            <span style={{ fontWeight: 800, fontSize: '16px', letterSpacing: '0.5px' }}>{booking.airline}</span>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', tracking: '1px' }}>Boarding Pass</span>
            <div style={{ fontSize: '15px', fontWeight: 800, color: '#38bdf8' }}>Flight {booking.flight_id}</div>
          </div>
        </div>

        {/* Boarding Pass Body */}
        <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {/* Origin & Destination Codes */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative' }}>
            <div style={{ flex: 1 }}>
              <h2 style={{ fontSize: '48px', fontWeight: 900, color: '#0f172a', lineHeight: 1 }}>{getAirportCode(booking.origin)}</h2>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#64748b', marginTop: '4px' }}>{booking.origin}</div>
            </div>

            {/* Flight icon connector */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', flex: 1, padding: '0 20px' }}>
              <div style={{ width: '100%', height: '2px', background: '#cbd5e1', position: 'relative' }}>
                <Plane
                  size={16}
                  color="#94a3b8"
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%) rotate(90deg)',
                    background: 'white',
                    padding: '0 4px',
                  }}
                />
              </div>
              <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700 }}>NON-STOP</span>
            </div>

            <div style={{ flex: 1, textAlign: 'right' }}>
              <h2 style={{ fontSize: '48px', fontWeight: 900, color: '#0f172a', lineHeight: 1 }}>{getAirportCode(booking.destination)}</h2>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#64748b', marginTop: '4px' }}>{booking.destination}</div>
            </div>
          </div>

          {/* Passenger & Flight Details Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '24px 16px',
              background: '#f8fafc',
              borderRadius: '16px',
              padding: '24px',
              border: '1px solid #e2e8f0',
            }}
            className="ticket-grid"
          >
            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Passenger</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <User size={14} color="#64748b" /> {user?.name}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Date</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Calendar size={14} color="#64748b" /> {formatDate(booking.date)}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Departure Time</div>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#0ea5e9', marginTop: '4px' }}>{booking.departure_time}</div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Cabin Class</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>{booking.travel_class}</div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Seats count</div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Armchair size={14} color="#64748b" /> {booking.number_of_seats} Seats
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>PNR / Reference</div>
              <div style={{ fontSize: '14px', fontWeight: 800, color: '#0284c7', marginTop: '4px', fontFamily: 'monospace' }}>
                {booking.booking_reference}
              </div>
            </div>
          </div>

          {/* Barcode representation */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
              paddingTop: '20px',
              borderTop: '2px dashed #cbd5e1',
            }}
          >
            {/* Visual Simulated Barcode */}
            <div
              style={{
                width: '100%',
                maxWidth: '400px',
                height: '56px',
                background: 'repeating-linear-gradient(90deg, #000, #000 2px, #fff 2px, #fff 8px, #000 8px, #000 10px, #fff 10px, #fff 14px, #000 14px, #000 18px, #fff 18px, #fff 20px)',
                opacity: 0.85,
              }}
            />
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', letterSpacing: '2px', fontFamily: 'monospace' }}>
              {booking.booking_reference}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
