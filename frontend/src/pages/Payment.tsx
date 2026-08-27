import { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  createPaymentApi,
  processPaymentApi,
  verifyPaymentApi,
  getPaymentApi,
  getPaymentByBookingApi,
  getBookingDetailsApi,
  downloadTicketPdfApi,
} from '../services/api';
import type { PaymentResponse, BookingResponse } from '../types';
import { formatCurrency } from '../services/flightService';
import {
  CreditCard,
  CheckCircle,
  AlertCircle,
  Loader2,
  ShieldCheck,
  ArrowLeft,
  Lock,
  Smartphone,
  Building2,
  Download,
  Ticket,
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface LocationState {
  booking?: BookingResponse;
  paymentId?: string;
}

type PayStep = 'IDLE' | 'LOADING' | 'CREATING' | 'PROCESSING' | 'SUCCESS' | 'FAILED';
type PayMethod = 'CARD' | 'UPI' | 'NET_BANKING';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const axiosErr = err as { response?: { data?: { detail?: string | { message?: string } } } };
    const detail = axiosErr.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (detail && typeof detail === 'object' && detail.message) return detail.message;
  }
  return fallback;
}

const METHOD_ICONS: Record<PayMethod, React.ElementType> = {
  CARD: CreditCard,
  UPI: Smartphone,
  NET_BANKING: Building2,
};

const METHOD_LABELS: Record<PayMethod, string> = {
  CARD: 'Credit / Debit Card',
  UPI: 'UPI',
  NET_BANKING: 'Net Banking',
};

// ─── Component ────────────────────────────────────────────────────────────────

export default function PaymentPage() {
  const { paymentId: routePaymentId } = useParams<{ paymentId?: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { userToken } = useAuth();

  const state = location.state as LocationState | null;

  // Data states
  const [booking, setBooking] = useState<BookingResponse | null>(state?.booking ?? null);
  const [payment, setPayment] = useState<PaymentResponse | null>(null);

  // Form states
  const [selectedMethod, setSelectedMethod] = useState<PayMethod>('CARD');
  const [cardNumber, setCardNumber] = useState('4111 1111 1111 1111');
  const [expiry, setExpiry] = useState('12/28');
  const [cvv, setCvv] = useState('123');
  const [upiId, setUpiId] = useState('user@upi');

  // Payment state machine
  const [step, setStep] = useState<PayStep>('IDLE');
  const [error, setError] = useState<string>('');

  // ── Load data when navigated via URL param ─────────────────────────────────
  const loadFromPaymentId = useCallback(async (pid: string) => {
    if (!userToken) return;
    setStep('LOADING');
    try {
      const paymentData = await getPaymentApi(pid, userToken);
      setPayment(paymentData);

      if (paymentData.status === 'SUCCESS') {
        setStep('SUCCESS');
      } else if (paymentData.status === 'FAILED') {
        setStep('FAILED');
      } else {
        setStep('IDLE');
      }

      // Fetch corresponding booking
      if (paymentData.booking_id) {
        try {
          const bookingData = await getBookingDetailsApi(paymentData.booking_id, userToken);
          if (bookingData.success) {
            setBooking(bookingData as unknown as BookingResponse);
          }
        } catch {
          /* booking fetch failed but payment is loaded – proceed */
        }
      }
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Could not load payment details. The payment ID may be invalid.'));
      setStep('FAILED');
    }
  }, [userToken]);

  // Load from URL param on mount
  useEffect(() => {
    if (routePaymentId) {
      loadFromPaymentId(routePaymentId);
    }
  }, [routePaymentId, loadFromPaymentId]);

  // Check existing payment for state-based booking
  const checkExistingPaymentForBooking = useCallback(async () => {
    if (!booking || !userToken || routePaymentId) return; // Don't double-load
    try {
      const existing = await getPaymentByBookingApi(booking.booking_id, userToken);
      if (existing && existing.payment_id) {
        setPayment(existing);
        if (existing.status === 'SUCCESS') setStep('SUCCESS');
        else if (existing.status === 'FAILED') setStep('FAILED');
      }
    } catch {
      /* No existing payment – fine, we'll create one */
    }
  }, [booking, userToken, routePaymentId]);

  useEffect(() => {
    checkExistingPaymentForBooking();
  }, [checkExistingPaymentForBooking]);

  // ── Redirect if no booking and no paymentId param ─────────────────────────
  useEffect(() => {
    if (!routePaymentId && !booking) {
      navigate('/my-bookings');
    }
  }, [routePaymentId, booking, navigate]);

  // ── Card number formatter ──────────────────────────────────────────────────
  const handleCardNumberChange = (val: string) => {
    const digits = val.replace(/\D/g, '').slice(0, 16);
    setCardNumber(digits.replace(/(.{4})/g, '$1 ').trim());
  };

  const handleExpiryChange = (val: string) => {
    const digits = val.replace(/\D/g, '').slice(0, 4);
    setExpiry(digits.length >= 3 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits);
  };

  // ── Main payment handler ───────────────────────────────────────────────────
  const handlePay = async () => {
    if (!userToken) {
      navigate('/login');
      return;
    }
    if (step === 'SUCCESS') return;

    setError('');

    // ── Step 1: Obtain a valid payment record ─────────────────────────────────
    let activePayment = payment;

    if (!activePayment || activePayment.status === 'FAILED') {
      if (!booking) {
        setError('Booking data is missing. Please navigate from My Bookings.');
        return;
      }
      setStep('CREATING');
      try {
        const created = await createPaymentApi(
          { booking_id: booking.booking_id, payment_method: selectedMethod, currency: 'INR' },
          userToken
        );
        activePayment = created;
        setPayment(created);
      } catch (err: unknown) {
        const msg = extractErrorMessage(err, 'Unable to initiate payment. Please try again.');
        // If DUPLICATE_PAYMENT, fetch the existing one
        const isDuplicate =
          err &&
          typeof err === 'object' &&
          'response' in err &&
          (err as { response?: { data?: { detail?: { error?: string } } } }).response?.data?.detail?.error === 'DUPLICATE_PAYMENT';

        if (isDuplicate && booking) {
          try {
            const existing = await getPaymentByBookingApi(booking.booking_id, userToken);
            if (existing && existing.payment_id) {
              activePayment = existing;
              setPayment(existing);
              if (existing.status === 'SUCCESS') { setStep('SUCCESS'); return; }
            } else {
              setError(msg); setStep('IDLE'); return;
            }
          } catch {
            setError(msg); setStep('IDLE'); return;
          }
        } else {
          setError(msg); setStep('IDLE'); return;
        }
      }
    }

    if (!activePayment) {
      setError('Unable to initiate payment. Please try again.');
      setStep('IDLE');
      return;
    }

    // ── Step 2: Process payment ───────────────────────────────────────────────
    setStep('PROCESSING');
    try {
      const processed = await processPaymentApi(
        activePayment.payment_id,
        selectedMethod,
        userToken
      );
      setPayment(processed);

      if (processed.status === 'SUCCESS') {
        try {
          const verified = await verifyPaymentApi(activePayment.payment_id, userToken);
          setPayment(verified);
          setStep(verified.status === 'SUCCESS' ? 'SUCCESS' : 'FAILED');
          if (verified.status !== 'SUCCESS') setError('Payment verification failed. Please contact support.');
        } catch {
          setStep('SUCCESS'); // process returned SUCCESS – trust it
        }
      } else {
        setStep('FAILED');
        setError(processed.failure_reason || 'Payment processing failed. Please try again.');
      }
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Payment processing failed. Please try again.'));
      setStep('FAILED');
    }
  };

  // ── Download ticket handler ────────────────────────────────────────────────
  const handleDownloadTicket = async () => {
    if (!userToken || !booking) return;
    try {
      const blob = await downloadTicketPdfApi((booking as any).booking_id, userToken);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.setAttribute('download', `ticket_${(booking as any).booking_reference || 'ticket'}.pdf`);
      document.body.appendChild(a);
      a.click();
      a.parentNode?.removeChild(a);
    } catch {
      alert('Failed to download PDF ticket.');
    }
  };

  // ─── Loading screen ────────────────────────────────────────────────────────
  if (step === 'LOADING') {
    return (
      <div style={{ minHeight: '100vh', background: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: '#64748b' }}>
          <Loader2 size={40} className="animate-spin" style={{ margin: '0 auto 16px' }} />
          <p style={{ fontWeight: 600, fontSize: '15px' }}>Loading payment details...</p>
        </div>
      </div>
    );
  }

  // ─── Success Screen ────────────────────────────────────────────────────────
  if (step === 'SUCCESS' && payment) {
    return (
      <div style={{ minHeight: '100vh', background: '#f8fafc', padding: '40px 20px' }}>
        <div style={{ maxWidth: '560px', margin: '0 auto' }}>
          <div
            style={{
              background: 'white',
              borderRadius: '24px',
              padding: '48px 36px',
              boxShadow: '0 10px 40px rgba(15,23,42,0.10)',
              border: '1.5px solid #e2e8f0',
              textAlign: 'center',
            }}
          >
            {/* Animated success ring */}
            <div
              style={{
                width: '88px',
                height: '88px',
                background: 'linear-gradient(135deg, #dcfce7, #bbf7d0)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 24px auto',
                boxShadow: '0 0 0 14px #f0fdf4',
                animation: 'pulse 2s infinite',
              }}
            >
              <CheckCircle size={46} color="#16a34a" />
            </div>

            <h1 style={{ fontSize: '28px', fontWeight: 900, color: '#0f172a', marginBottom: '8px' }}>
              Payment Successful!
            </h1>
            <p style={{ color: '#64748b', fontSize: '15px', marginBottom: '32px' }}>
              Your booking is confirmed. Tickets are ready.
            </p>

            {/* Details */}
            <div
              style={{
                background: '#f8fafc',
                border: '1.5px solid #e2e8f0',
                borderRadius: '16px',
                padding: '24px',
                textAlign: 'left',
                marginBottom: '28px',
              }}
            >
              {[
                booking && { label: 'Booking Reference', value: (booking as any).booking_reference, accent: true },
                { label: 'Amount Paid', value: formatCurrency(payment.amount) },
                { label: 'Status', value: 'CONFIRMED', badge: true },
                { label: 'Payment Method', value: payment.payment_method || selectedMethod },
                { label: 'Payment ID', value: payment.payment_id },
                { label: 'Transaction ID', value: payment.transaction_id || 'N/A' },
              ]
                .filter(Boolean)
                .map(({ label, value, accent, badge }: any) => (
                  <div
                    key={label}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '10px 0',
                      borderBottom: '1px solid #f1f5f9',
                    }}
                  >
                    <span style={{ fontSize: '13px', color: '#64748b', fontWeight: 600 }}>{label}</span>
                    {badge ? (
                      <span
                        style={{
                          background: '#dcfce7',
                          color: '#15803d',
                          padding: '3px 12px',
                          borderRadius: '999px',
                          fontSize: '12px',
                          fontWeight: 800,
                        }}
                      >
                        {value}
                      </span>
                    ) : (
                      <span
                        style={{
                          fontSize: '14px',
                          fontWeight: 700,
                          color: accent ? '#0284c7' : '#0f172a',
                          fontFamily: accent ? 'monospace' : undefined,
                        }}
                      >
                        {value}
                      </span>
                    )}
                  </div>
                ))}
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {booking && (
                <button
                  onClick={handleDownloadTicket}
                  className="btn-primary"
                  style={{
                    flex: 1,
                    padding: '14px',
                    fontSize: '15px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  <Download size={18} /> Download Ticket
                </button>
              )}
              <button
                onClick={() =>
                  booking
                    ? navigate(`/booking/${(booking as any).booking_id}`)
                    : navigate('/my-bookings')
                }
                className="btn-ghost"
                style={{
                  padding: '14px 20px',
                  fontSize: '15px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <Ticket size={18} /> View Booking
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ─── Payment Form ──────────────────────────────────────────────────────────
  const isProcessing = step === 'CREATING' || step === 'PROCESSING';
  const loadingLabel =
    step === 'CREATING'
      ? 'Initiating payment...'
      : step === 'PROCESSING'
      ? 'Processing payment...'
      : null;

  const totalAmount = payment?.amount ?? (booking as any)?.total_price ?? 0;

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', padding: '40px 20px' }}>
      <div style={{ maxWidth: '580px', margin: '0 auto' }}>

        {/* Back */}
        <button
          onClick={() => navigate(-1)}
          className="btn-ghost"
          style={{ marginBottom: '24px', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          disabled={isProcessing}
        >
          <ArrowLeft size={16} /> Back
        </button>

        <div
          style={{
            background: 'white',
            borderRadius: '24px',
            padding: '36px',
            boxShadow: '0 8px 30px rgba(15,23,42,0.07)',
            border: '1.5px solid #e2e8f0',
          }}
        >
          {/* Header */}
          <div style={{ marginBottom: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Lock size={20} color="white" />
              </div>
              <div>
                <h1 style={{ fontSize: '22px', fontWeight: 900, color: '#0f172a', margin: 0 }}>
                  Complete Payment
                </h1>
                <div style={{ fontSize: '13px', color: '#64748b' }}>Secure mock payment portal</div>
              </div>
            </div>

            <div
              style={{
                background: '#fefce8',
                border: '1.5px solid #fde68a',
                borderRadius: '12px',
                padding: '12px 16px',
                fontSize: '13px',
                color: '#854d0e',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginTop: '16px',
              }}
            >
              <ShieldCheck size={16} color="#ca8a04" />
              Demo Mode — No real money charged
            </div>
          </div>

          {/* Booking Summary */}
          {(booking || payment) && (
            <div
              style={{
                background: 'linear-gradient(135deg, #f0f9ff, #e0f2fe)',
                border: '1.5px solid #7dd3fc',
                borderRadius: '16px',
                padding: '20px',
                marginBottom: '28px',
              }}
            >
              <div style={{ fontSize: '13px', color: '#0284c7', fontWeight: 700, marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Booking Summary
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                {booking && (
                  <>
                    <div>
                      <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Reference</div>
                      <div style={{ fontSize: '14px', fontWeight: 800, color: '#0284c7', fontFamily: 'monospace' }}>
                        {(booking as any).booking_reference}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Flight</div>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>{(booking as any).flight_id}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Seats</div>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>{(booking as any).number_of_seats}</div>
                    </div>
                  </>
                )}
                {payment && (
                  <div>
                    <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Payment ID</div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a', fontFamily: 'monospace' }}>{payment.payment_id}</div>
                  </div>
                )}
                <div>
                  <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Amount Due</div>
                  <div style={{ fontSize: '20px', fontWeight: 900, color: '#0ea5e9' }}>
                    {formatCurrency(totalAmount)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Payment Method Selection */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginBottom: '12px' }}>
              Payment Method
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {(['CARD', 'UPI', 'NET_BANKING'] as PayMethod[]).map((method) => {
                const Icon = METHOD_ICONS[method];
                const isSelected = selectedMethod === method;
                return (
                  <button
                    key={method}
                    disabled={isProcessing}
                    onClick={() => setSelectedMethod(method)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '14px 16px',
                      borderRadius: '12px',
                      border: isSelected ? '2px solid #0ea5e9' : '2px solid #e2e8f0',
                      background: isSelected ? '#f0f9ff' : 'white',
                      cursor: isProcessing ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s',
                      textAlign: 'left',
                    }}
                  >
                    <div
                      style={{
                        width: '22px',
                        height: '22px',
                        borderRadius: '50%',
                        border: `2px solid ${isSelected ? '#0ea5e9' : '#cbd5e1'}`,
                        background: isSelected ? '#0ea5e9' : 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      {isSelected && <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'white' }} />}
                    </div>
                    <Icon size={18} color={isSelected ? '#0284c7' : '#64748b'} />
                    <span style={{ fontWeight: 700, color: isSelected ? '#0284c7' : '#475569', fontSize: '14px' }}>
                      {METHOD_LABELS[method]}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Method-specific inputs */}
          {selectedMethod === 'CARD' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
              <div>
                <label htmlFor="pay-card-number" style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '6px' }}>
                  Card Number
                </label>
                <input
                  id="pay-card-number"
                  type="text"
                  value={cardNumber}
                  onChange={(e) => handleCardNumberChange(e.target.value)}
                  placeholder="1234 5678 9012 3456"
                  maxLength={19}
                  disabled={isProcessing}
                  style={{
                    width: '100%', padding: '12px 14px', borderRadius: '12px', border: '1.5px solid #cbd5e1',
                    fontSize: '15px', fontWeight: 600, fontFamily: 'monospace', letterSpacing: '2px',
                    color: '#0f172a', background: isProcessing ? '#f8fafc' : 'white', boxSizing: 'border-box', outline: 'none',
                  }}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label htmlFor="pay-expiry" style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '6px' }}>
                    Expiry (MM/YY)
                  </label>
                  <input
                    id="pay-expiry"
                    type="text"
                    value={expiry}
                    onChange={(e) => handleExpiryChange(e.target.value)}
                    placeholder="MM/YY"
                    maxLength={5}
                    disabled={isProcessing}
                    style={{
                      width: '100%', padding: '12px 14px', borderRadius: '12px', border: '1.5px solid #cbd5e1',
                      fontSize: '15px', fontWeight: 600, fontFamily: 'monospace', color: '#0f172a',
                      background: isProcessing ? '#f8fafc' : 'white', boxSizing: 'border-box', outline: 'none',
                    }}
                  />
                </div>
                <div>
                  <label htmlFor="pay-cvv" style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '6px' }}>
                    CVV
                  </label>
                  <input
                    id="pay-cvv"
                    type="password"
                    value={cvv}
                    onChange={(e) => setCvv(e.target.value.replace(/\D/g, '').slice(0, 4))}
                    placeholder="•••"
                    maxLength={4}
                    disabled={isProcessing}
                    style={{
                      width: '100%', padding: '12px 14px', borderRadius: '12px', border: '1.5px solid #cbd5e1',
                      fontSize: '15px', fontWeight: 600, fontFamily: 'monospace', color: '#0f172a',
                      background: isProcessing ? '#f8fafc' : 'white', boxSizing: 'border-box', outline: 'none',
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {selectedMethod === 'UPI' && (
            <div style={{ marginBottom: '24px' }}>
              <label htmlFor="pay-upi" style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '6px' }}>
                UPI ID
              </label>
              <input
                id="pay-upi"
                type="text"
                value={upiId}
                onChange={(e) => setUpiId(e.target.value)}
                placeholder="yourname@upi"
                disabled={isProcessing}
                style={{
                  width: '100%', padding: '12px 14px', borderRadius: '12px', border: '1.5px solid #cbd5e1',
                  fontSize: '15px', fontWeight: 600, color: '#0f172a',
                  background: isProcessing ? '#f8fafc' : 'white', boxSizing: 'border-box', outline: 'none',
                }}
              />
            </div>
          )}

          {selectedMethod === 'NET_BANKING' && (
            <div style={{ marginBottom: '24px' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>Select Bank</div>
              <select
                disabled={isProcessing}
                style={{
                  width: '100%', padding: '12px 14px', borderRadius: '12px', border: '1.5px solid #cbd5e1',
                  fontSize: '15px', fontWeight: 600, color: '#0f172a', background: isProcessing ? '#f8fafc' : 'white',
                  boxSizing: 'border-box', outline: 'none',
                }}
              >
                {['HDFC Bank', 'ICICI Bank', 'SBI', 'Axis Bank', 'Kotak Bank'].map((bank) => (
                  <option key={bank}>{bank}</option>
                ))}
              </select>
            </div>
          )}

          {/* Payment status badge */}
          {payment && !isProcessing && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px', fontSize: '13px', color: '#64748b' }}>
              <span style={{ fontWeight: 600 }}>Payment Status:</span>
              <span
                style={{
                  padding: '3px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: 800,
                  background: payment.status === 'SUCCESS' ? '#dcfce7' : payment.status === 'FAILED' ? '#fef2f2' : '#fef9c3',
                  color: payment.status === 'SUCCESS' ? '#15803d' : payment.status === 'FAILED' ? '#dc2626' : '#854d0e',
                }}
              >
                {payment.status}
              </span>
            </div>
          )}

          {/* Error banner */}
          {error && !isProcessing && (
            <div
              style={{
                background: '#fef2f2', border: '1.5px solid #fecaca', borderRadius: '12px',
                padding: '12px 16px', color: '#dc2626', fontSize: '14px', fontWeight: 600,
                display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px',
              }}
            >
              <AlertCircle size={18} />
              {error}
            </div>
          )}

          {/* Loading state */}
          {isProcessing && (
            <div
              style={{
                background: '#f0f9ff', border: '1.5px solid #7dd3fc', borderRadius: '12px',
                padding: '12px 16px', color: '#0284c7', fontSize: '14px', fontWeight: 600,
                display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px',
              }}
            >
              <Loader2 size={18} className="animate-spin" />
              {loadingLabel}
            </div>
          )}

          {/* Security note */}
          <div
            style={{
              display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px',
              color: '#64748b', marginBottom: '20px', justifyContent: 'center',
            }}
          >
            <Lock size={14} color="#10b981" />
            <span>256-bit SSL encrypted · Demo mode · No real charges</span>
          </div>

          {/* Pay button */}
          <button
            id="pay-now-btn"
            onClick={handlePay}
            disabled={isProcessing || step === 'SUCCESS'}
            className="btn-primary"
            style={{
              width: '100%', padding: '16px', fontSize: '17px', fontWeight: 800,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
              opacity: isProcessing ? 0.7 : 1,
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              background: step === 'FAILED' ? 'linear-gradient(135deg, #ef4444, #dc2626)' : undefined,
            }}
          >
            {isProcessing ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                {step === 'CREATING' ? 'Initiating...' : 'Processing...'}
              </>
            ) : step === 'FAILED' ? (
              <>
                <CreditCard size={20} />
                Retry Payment · {formatCurrency(totalAmount)}
              </>
            ) : (
              <>
                <Lock size={20} />
                Pay {formatCurrency(totalAmount)} via {METHOD_LABELS[selectedMethod]}
              </>
            )}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 0 14px #f0fdf4; }
          50% { box-shadow: 0 0 0 20px #dcfce7; }
        }
      `}</style>
    </div>
  );
}
