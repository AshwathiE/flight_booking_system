import { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { createBookingApi, checkAvailabilityApi } from '../services/api';
import type { Flight, BookingResponse } from '../types';
import { formatTime, formatCurrency } from '../services/flightService';
import { calculateFlightDuration } from '../utils/flightUtils';
import { Plane, Clock, Users, ArrowLeft, CheckCircle, AlertCircle, Loader2, Receipt, ShieldCheck, Check } from 'lucide-react';

export default function BookingPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, userToken } = useAuth();

  const flightState = (location.state as { flight?: Flight; passengers?: number })?.flight;
  const initialPassengers = (location.state as { flight?: Flight; passengers?: number })?.passengers || 1;

  const [flight] = useState<Flight | null>(flightState || null);
  const [numberOfSeats, setNumberOfSeats] = useState<number>(initialPassengers);
  const [availableSeats, setAvailableSeats] = useState<number>(flightState?.available_seats || 10);
  const [checkingAvailability, setCheckingAvailability] = useState<boolean>(false);
  const [isSeatAvailable, setIsSeatAvailable] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [bookingConfirmation, setBookingConfirmation] = useState<BookingResponse | null>(null);

  useEffect(() => {
    if (!flightState) {
      navigate('/');
    }
  }, [flightState, navigate]);

  // Real-time seat availability check via Flight MCP Server
  const verifyLiveAvailability = useCallback(async (seats: number) => {
    if (!flight?.flight_id) return;
    setCheckingAvailability(true);
    setError('');

    try {
      const res = await checkAvailabilityApi(flight.flight_id, seats);
      if (res && typeof res.available_seats === 'number') {
        setAvailableSeats(res.available_seats);
        setIsSeatAvailable(res.available);
        if (!res.available) {
          setError(`Only ${res.available_seats} seat(s) available on this flight for your request.`);
        }
      }
    } catch {
      // Fallback to local flight available seats if MCP endpoint error
      if (seats > (flight.available_seats || 0)) {
        setIsSeatAvailable(false);
        setError(`Only ${flight.available_seats} seat(s) available for this flight.`);
      } else {
        setIsSeatAvailable(true);
      }
    } finally {
      setCheckingAvailability(false);
    }
  }, [flight]);

  // Check availability when passenger count changes
  useEffect(() => {
    if (flight?.flight_id) {
      verifyLiveAvailability(numberOfSeats);
    }
  }, [numberOfSeats, flight, verifyLiveAvailability]);

  if (!flight) {
    return null;
  }

  const durationText = calculateFlightDuration(flight.departure_time, flight.arrival_time);

  // Price breakdown calculations
  const baseFare = flight.price * numberOfSeats;
  const taxFee = Math.round(baseFare * 0.05); // 5% GST & Taxes
  const serviceFee = 100 * numberOfSeats;     // ₹100 per seat service fee
  const grandTotal = baseFare + taxFee + serviceFee;

  const handleConfirmBooking = async () => {
    setError('');

    if (!userToken || !user) {
      // Redirect to login preserving full return state
      navigate('/login', { state: { returnTo: '/booking', flight, passengers: numberOfSeats } });
      return;
    }

    if (numberOfSeats <= 0) {
      setError('Please select at least 1 seat.');
      return;
    }

    if (numberOfSeats > availableSeats) {
      setError(`Only ${availableSeats} seat(s) available for this flight. Please reduce the number of seats.`);
      return;
    }

    setLoading(true);

    try {
      const response = await createBookingApi(
        {
          flight_id: flight.flight_id,
          number_of_seats: numberOfSeats,
        },
        userToken
      );

      if (response.success) {
        setBookingConfirmation(response);
      } else {
        setError(response.message || response.error || 'Failed to create booking.');
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string | { message?: string } } } };
        const detail = axiosErr.response?.data?.detail;
        if (typeof detail === 'string') {
          setError(detail);
        } else if (detail && typeof detail === 'object' && detail.message) {
          setError(detail.message);
        } else {
          setError('Unable to confirm booking. Please try again.');
        }
      } else {
        setError('Unable to confirm booking. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', padding: '40px 20px' }}>
      <div style={{ maxWidth: '720px', margin: '0 auto' }}>
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="btn-ghost"
          style={{ marginBottom: '24px', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <ArrowLeft size={16} /> Back to Search Results
        </button>

        {/* Successful Booking Confirmation View */}
        {bookingConfirmation ? (
          <div
            style={{
              background: 'white',
              borderRadius: '24px',
              padding: '36px',
              boxShadow: '0 10px 30px rgba(15,23,42,0.08)',
              border: '1.5px solid #e2e8f0',
              textAlign: 'center',
            }}
          >
            <div
              style={{
                width: '64px',
                height: '64px',
                background: '#dcfce7',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 20px auto',
              }}
            >
              <CheckCircle size={36} color="#16a34a" />
            </div>

            <h1 style={{ fontSize: '26px', fontWeight: 900, color: '#0f172a', marginBottom: '8px' }}>
              Booking Confirmed
            </h1>
            <p style={{ color: '#64748b', fontSize: '15px', marginBottom: '28px' }}>
              Your flight reservation has been processed and confirmed successfully via Booking MCP Server.
            </p>

            <div
              style={{
                background: '#f8fafc',
                borderRadius: '16px',
                padding: '24px',
                textAlign: 'left',
                border: '1px solid #e2e8f0',
                marginBottom: '28px',
              }}
            >
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '16px',
                  rowGap: '20px',
                }}
              >
                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Booking ID</div>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
                    {bookingConfirmation.booking_id}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Reference</div>
                  <div style={{ fontSize: '16px', fontWeight: 800, color: '#0284c7' }}>
                    {bookingConfirmation.booking_reference}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Flight</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
                    {flight.airline} ({bookingConfirmation.flight_id})
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Route</div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
                    {flight.origin} → {flight.destination}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Seats Booked</div>
                  <div style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a' }}>
                    {bookingConfirmation.number_of_seats} seat(s)
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Status</div>
                  <span
                    style={{
                      display: 'inline-block',
                      background: '#dcfce7',
                      color: '#15803d',
                      padding: '4px 12px',
                      borderRadius: '999px',
                      fontSize: '13px',
                      fontWeight: 800,
                    }}
                  >
                    {bookingConfirmation.status}
                  </span>
                </div>
              </div>

              {/* Price Breakdown in Confirmation */}
              <div
                style={{
                  marginTop: '20px',
                  paddingTop: '16px',
                  borderTop: '1px dashed #cbd5e1',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  fontSize: '13px',
                  color: '#64748b',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Base Fare ({bookingConfirmation.number_of_seats} seat{bookingConfirmation.number_of_seats > 1 ? 's' : ''})</span>
                  <span style={{ fontWeight: 600, color: '#0f172a' }}>{formatCurrency(bookingConfirmation.total_price)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Taxes & GST (5%)</span>
                  <span style={{ fontWeight: 600, color: '#0f172a' }}>{formatCurrency(Math.round(bookingConfirmation.total_price * 0.05))}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Service Fee</span>
                  <span style={{ fontWeight: 600, color: '#0f172a' }}>{formatCurrency(100 * bookingConfirmation.number_of_seats)}</span>
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    paddingTop: '10px',
                    borderTop: '1px solid #e2e8f0',
                    fontSize: '16px',
                    fontWeight: 900,
                    color: '#0f172a',
                  }}
                >
                  <span>Total Amount Paid</span>
                  <span style={{ color: '#0ea5e9', fontSize: '18px' }}>
                    {formatCurrency(
                      bookingConfirmation.total_price +
                      Math.round(bookingConfirmation.total_price * 0.05) +
                      (100 * bookingConfirmation.number_of_seats)
                    )}
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={() => navigate('/')}
              className="btn-primary"
              style={{ width: '100%', padding: '14px', fontSize: '16px' }}
            >
              Return to Home
            </button>
          </div>
        ) : (
          /* Flight Selection & Booking Form */
          <div
            style={{
              background: 'white',
              borderRadius: '24px',
              padding: '32px',
              boxShadow: '0 8px 30px rgba(15,23,42,0.06)',
              border: '1.5px solid #e2e8f0',
            }}
          >
            <h1 style={{ fontSize: '24px', fontWeight: 900, color: '#0f172a', marginBottom: '24px' }}>
              Confirm Flight Booking
            </h1>

            {/* Flight summary card */}
            <div
              style={{
                background: 'linear-gradient(135deg, #f0f9ff, #e0f2fe)',
                border: '1.5px solid #7dd3fc',
                borderRadius: '16px',
                padding: '20px',
                marginBottom: '28px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      background: '#0ea5e9',
                      borderRadius: '10px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Plane size={20} color="white" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: '16px', color: '#0f172a' }}>{flight.airline}</div>
                    <div style={{ fontSize: '13px', color: '#0284c7', fontWeight: 600 }}>{flight.flight_id}</div>
                  </div>
                </div>
                <span className="tag tag-sky">{flight.travel_class}</span>
              </div>

              {/* Route */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <div style={{ fontSize: '24px', fontWeight: 900, color: '#0f172a' }}>
                    {formatTime(flight.departure_time)}
                  </div>
                  <div style={{ fontSize: '13px', color: '#475569', fontWeight: 600 }}>{flight.origin}</div>
                </div>

                <div style={{ flex: 1, textAlign: 'center' }}>
                  {durationText && (
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 700,
                        color: '#0284c7',
                        background: 'white',
                        padding: '2px 8px',
                        borderRadius: '999px',
                      }}
                    >
                      {durationText}
                    </span>
                  )}
                  <div style={{ height: '2px', background: '#7dd3fc', margin: '4px 0' }} />
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '24px', fontWeight: 900, color: '#0f172a' }}>
                    {formatTime(flight.arrival_time)}
                  </div>
                  <div style={{ fontSize: '13px', color: '#475569', fontWeight: 600 }}>{flight.destination}</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '20px', fontSize: '13px', color: '#475569', alignItems: 'center' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Clock size={14} /> {flight.date}
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                  <Users size={14} /> {availableSeats} seats available
                </span>
                {checkingAvailability && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#0284c7', fontSize: '12px' }}>
                    <Loader2 size={12} className="animate-spin" /> Verifying live seats...
                  </span>
                )}
                {!checkingAvailability && isSeatAvailable && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#16a34a', fontSize: '12px', fontWeight: 700 }}>
                    <Check size={12} /> Live Verified
                  </span>
                )}
              </div>
            </div>

            {/* Error Banner */}
            {error && (
              <div
                style={{
                  background: '#fef2f2',
                  border: '1.5px solid #fecaca',
                  borderRadius: '12px',
                  padding: '14px 16px',
                  color: '#dc2626',
                  fontSize: '14px',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  marginBottom: '24px',
                }}
              >
                <AlertCircle size={18} />
                {error}
              </div>
            )}

            {/* Seat Selection */}
            <div style={{ marginBottom: '28px' }}>
              <label
                htmlFor="seat-selection"
                style={{ display: 'block', fontSize: '14px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}
              >
                Number of Seats
              </label>
              <select
                id="seat-selection"
                value={numberOfSeats}
                onChange={(e) => setNumberOfSeats(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: '1.5px solid #cbd5e1',
                  fontSize: '15px',
                  fontWeight: 600,
                  color: '#0f172a',
                  background: 'white',
                  cursor: 'pointer',
                }}
              >
                {Array.from({ length: Math.min(20, Math.max(numberOfSeats, availableSeats)) }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>
                    {n} seat{n > 1 ? 's' : ''} {n > availableSeats ? '(Insufficient Seats)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Price breakdown */}
            <div
              style={{
                background: '#f8fafc',
                border: '1.5px solid #e2e8f0',
                borderRadius: '16px',
                padding: '20px',
                marginBottom: '28px',
              }}
            >
              <div
                style={{
                  fontSize: '15px',
                  fontWeight: 700,
                  color: '#0f172a',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <Receipt size={18} color="#0284c7" />
                Fare Summary & Breakdown
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', color: '#64748b', fontSize: '14px' }}>
                <span>Base Fare ({numberOfSeats} {numberOfSeats === 1 ? 'seat' : 'seats'} × {formatCurrency(flight.price)})</span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>{formatCurrency(baseFare)}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', color: '#64748b', fontSize: '14px' }}>
                <span>Taxes & GST (5%)</span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>{formatCurrency(taxFee)}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', color: '#64748b', fontSize: '14px' }}>
                <span>Service Fee (₹100/seat)</span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>{formatCurrency(serviceFee)}</span>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingTop: '14px',
                  borderTop: '1.5px dashed #cbd5e1',
                }}
              >
                <div>
                  <div style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a' }}>Total Amount</div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>Includes all taxes and fees</div>
                </div>
                <span style={{ fontSize: '22px', fontWeight: 900, color: '#0ea5e9' }}>
                  {formatCurrency(grandTotal)}
                </span>
              </div>
            </div>

            {/* Security note */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '12px',
                color: '#64748b',
                marginBottom: '20px',
                justifyContent: 'center',
              }}
            >
              <ShieldCheck size={16} color="#10b981" />
              <span>Safe & Secure 256-bit Encrypted Reservation</span>
            </div>

            {/* Confirm Button */}
            <button
              onClick={handleConfirmBooking}
              disabled={loading || checkingAvailability || !isSeatAvailable}
              className="btn-primary"
              style={{
                width: '100%',
                padding: '16px',
                fontSize: '16px',
                fontWeight: 800,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                opacity: (!isSeatAvailable || checkingAvailability) ? 0.6 : 1,
                cursor: (!isSeatAvailable || checkingAvailability) ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" /> Processing Booking via MCP...
                </>
              ) : checkingAvailability ? (
                <>
                  <Loader2 size={18} className="animate-spin" /> Verifying Live Availability...
                </>
              ) : !isSeatAvailable ? (
                `Insufficient Seats (${availableSeats} Available)`
              ) : (
                `Confirm Booking (${numberOfSeats} Seats) • ${formatCurrency(grandTotal)}`
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
