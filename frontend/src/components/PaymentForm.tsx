import React, { useState, FormEvent } from 'react';
import { CreditCard, Smartphone, Building2, Lock } from 'lucide-react';
import { Flight } from '../types';
import { formatCurrency } from '../services/flightService';

type Method = 'card' | 'upi' | 'netbanking';

interface Props {
  flight: Flight;
  passengers: number;
  onPay: () => void;
  paying: boolean;
}

export default function PaymentForm({ flight, passengers, onPay, paying }: Props) {
  const [method, setMethod] = useState<Method>('card');
  const [cardNum, setCardNum] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvv, setCvv] = useState('');
  const [upiId, setUpiId] = useState('');
  const [bank, setBank] = useState('');

  const tax = Math.round(flight.fare.total_fare * 0.05);
  const serviceFee = 499;
  const total = flight.fare.total_fare + tax + serviceFee;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onPay();
  };

  const methodTab = (m: Method, icon: React.ReactNode, label: string) => (
    <button
      type="button"
      id={`pay-method-${m}`}
      onClick={() => setMethod(m)}
      style={{
        flex: 1,
        padding: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        border: `2px solid ${method === m ? '#0ea5e9' : '#e2e8f0'}`,
        borderRadius: '12px',
        background: method === m ? '#e0f2fe' : 'white',
        color: method === m ? '#0284c7' : '#64748b',
        cursor: 'pointer',
        fontFamily: 'inherit',
        fontSize: '13px',
        fontWeight: 600,
        transition: 'all 0.2s',
      }}
    >
      {icon}
      {label}
    </button>
  );

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '11px 14px',
    border: '1.5px solid #e2e8f0',
    borderRadius: '10px',
    fontSize: '14px',
    fontFamily: 'inherit',
    outline: 'none',
    background: 'white',
    color: '#0f172a',
    transition: 'border-color 0.2s',
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Method selector */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '24px' }}>
        {methodTab('card', <CreditCard size={16} />, 'Card')}
        {methodTab('upi', <Smartphone size={16} />, 'UPI')}
        {methodTab('netbanking', <Building2 size={16} />, 'Net Banking')}
      </div>

      {/* Card inputs */}
      {method === 'card' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '5px', display: 'block' }}>
              Card Number
            </label>
            <input
              id="pay-card-num"
              style={inputStyle}
              placeholder="1234 5678 9012 3456"
              value={cardNum}
              maxLength={19}
              onChange={(e) => {
                const v = e.target.value.replace(/\D/g, '').slice(0, 16);
                setCardNum(v.replace(/(.{4})/g, '$1 ').trim());
              }}
              onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
              onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '5px', display: 'block' }}>
                Expiry
              </label>
              <input
                id="pay-expiry"
                style={inputStyle}
                placeholder="MM/YY"
                value={expiry}
                maxLength={5}
                onChange={(e) => {
                  let v = e.target.value.replace(/\D/g, '').slice(0, 4);
                  if (v.length >= 3) v = v.slice(0, 2) + '/' + v.slice(2);
                  setExpiry(v);
                }}
                onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '5px', display: 'block' }}>
                CVV
              </label>
              <input
                id="pay-cvv"
                style={inputStyle}
                placeholder="•••"
                type="password"
                value={cvv}
                maxLength={4}
                onChange={(e) => setCvv(e.target.value.replace(/\D/g, '').slice(0, 4))}
                onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              />
            </div>
          </div>
        </div>
      )}

      {method === 'upi' && (
        <div>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '5px', display: 'block' }}>
            UPI ID
          </label>
          <input
            id="pay-upi"
            style={inputStyle}
            placeholder="yourname@upi"
            value={upiId}
            onChange={(e) => setUpiId(e.target.value)}
            onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
            onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
          />
        </div>
      )}

      {method === 'netbanking' && (
        <div>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '5px', display: 'block' }}>
            Select Bank
          </label>
          <select
            id="pay-bank"
            style={{ ...inputStyle, cursor: 'pointer' }}
            value={bank}
            onChange={(e) => setBank(e.target.value)}
          >
            <option value="">Choose your bank</option>
            <option value="sbi">State Bank of India</option>
            <option value="hdfc">HDFC Bank</option>
            <option value="icici">ICICI Bank</option>
            <option value="axis">Axis Bank</option>
            <option value="kotak">Kotak Mahindra Bank</option>
          </select>
        </div>
      )}

      {/* Fare summary */}
      <div
        style={{
          marginTop: '24px',
          background: '#f8fafc',
          borderRadius: '12px',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        {[
          { label: `Fare (${passengers} pax)`, amount: flight.fare.total_fare },
          { label: 'Taxes (5%)', amount: tax },
          { label: 'Service fee', amount: serviceFee },
        ].map(({ label, amount }) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: '#64748b' }}>
            <span>{label}</span>
            <span>{formatCurrency(amount)}</span>
          </div>
        ))}
        <div
          style={{
            borderTop: '1px solid #e2e8f0',
            paddingTop: '10px',
            marginTop: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '16px',
            fontWeight: 800,
            color: '#0f172a',
          }}
        >
          <span>Total</span>
          <span>{formatCurrency(total)}</span>
        </div>
      </div>

      {/* Secure note */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginTop: '12px',
          color: '#64748b',
          fontSize: '12px',
        }}
      >
        <Lock size={12} />
        Your payment details are encrypted and secure.
      </div>

      {/* Pay button */}
      <button
        id="pay-confirm-btn"
        type="submit"
        className="btn-primary"
        disabled={paying}
        style={{ width: '100%', marginTop: '20px', padding: '14px', fontSize: '16px' }}
      >
        {paying ? (
          <>
            <div
              style={{
                width: '18px',
                height: '18px',
                border: '2px solid rgba(255,255,255,0.4)',
                borderTopColor: 'white',
                borderRadius: '50%',
                animation: 'spin-slow 0.8s linear infinite',
              }}
            />
            Processing...
          </>
        ) : (
          <>💳 Pay {formatCurrency(total)}</>
        )}
      </button>
    </form>
  );
}
