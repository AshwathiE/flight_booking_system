import React, { useState, FormEvent } from 'react';
import { MapPin, Calendar, Users, Tag, DollarSign, ChevronDown, ChevronUp } from 'lucide-react';

interface StructuredFormData {
  from: string;
  to: string;
  date: string;
  passengers: string;
  travelClass: string;
  maxPrice: string;
  preference: string;
}

interface Props {
  onSearch: (message: string) => void;
  loading: boolean;
}

export default function FlightSearchForm({ onSearch, loading }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [form, setForm] = useState<StructuredFormData>({
    from: '',
    to: '',
    date: '',
    passengers: '1',
    travelClass: '',
    maxPrice: '',
    preference: 'automatic',
  });

  const handle = (field: keyof StructuredFormData, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!form.from || !form.to || !form.date) return;
    let msg = `Flight from ${form.from} to ${form.to} for ${form.passengers} passenger${Number(form.passengers) > 1 ? 's' : ''} on ${form.date}`;
    if (form.travelClass) msg += ` in ${form.travelClass}`;
    if (form.maxPrice) msg += ` with max price ${form.maxPrice}`;
    if (form.preference && form.preference !== 'automatic') msg += `, prefer ${form.preference}`;
    onSearch(msg);
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 12px',
    border: '1.5px solid #e2e8f0',
    borderRadius: '10px',
    fontSize: '14px',
    fontFamily: 'inherit',
    outline: 'none',
    transition: 'border-color 0.2s',
    background: 'white',
    color: '#0f172a',
  };

  const labelStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    fontSize: '12px',
    fontWeight: 600,
    color: '#64748b',
    marginBottom: '6px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  };

  return (
    <div
      style={{
        background: 'rgba(255,255,255,0.6)',
        border: '1px solid #e2e8f0',
        borderRadius: '14px',
        overflow: 'hidden',
        marginTop: '12px',
      }}
    >
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          padding: '14px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          fontFamily: 'inherit',
          fontSize: '14px',
          fontWeight: 600,
          color: '#64748b',
        }}
      >
        <span>Or use structured search form</span>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {expanded && (
        <form onSubmit={handleSubmit} style={{ padding: '0 20px 20px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '14px',
              marginBottom: '16px',
            }}
          >
            {/* From */}
            <div>
              <label style={labelStyle}>
                <MapPin size={12} /> From
              </label>
              <input
                id="form-from"
                style={inputStyle}
                placeholder="Chennai"
                value={form.from}
                onChange={(e) => handle('from', e.target.value)}
                onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              />
            </div>
            {/* To */}
            <div>
              <label style={labelStyle}>
                <MapPin size={12} /> To
              </label>
              <input
                id="form-to"
                style={inputStyle}
                placeholder="Delhi"
                value={form.to}
                onChange={(e) => handle('to', e.target.value)}
                onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              />
            </div>
            {/* Date */}
            <div>
              <label style={labelStyle}>
                <Calendar size={12} /> Date
              </label>
              <input
                id="form-date"
                type="date"
                style={inputStyle}
                value={form.date}
                onChange={(e) => handle('date', e.target.value)}
                onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              />
            </div>
            {/* Passengers */}
            <div>
              <label style={labelStyle}>
                <Users size={12} /> Passengers
              </label>
              <input
                id="form-passengers"
                type="number"
                min="1"
                max="200"
                style={inputStyle}
                value={form.passengers}
                onChange={(e) => handle('passengers', e.target.value)}
                onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              />
            </div>
            {/* Travel Class */}
            <div>
              <label style={labelStyle}>
                <Tag size={12} /> Travel Class
              </label>
              <select
                id="form-class"
                style={{ ...inputStyle, cursor: 'pointer' }}
                value={form.travelClass}
                onChange={(e) => handle('travelClass', e.target.value)}
                onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              >
                <option value="">Any class</option>
                <option value="Economy">Economy</option>
                <option value="Business">Business</option>
                <option value="First Class">First Class</option>
                <option value="Premium Economy">Premium Economy</option>
              </select>
            </div>
            {/* Max Price */}
            <div>
              <label style={labelStyle}>
                <DollarSign size={12} /> Max Price (₹)
              </label>
              <input
                id="form-maxprice"
                type="number"
                style={inputStyle}
                placeholder="No limit"
                value={form.maxPrice}
                onChange={(e) => handle('maxPrice', e.target.value)}
                onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              />
            </div>
            {/* Preference */}
            <div>
              <label style={labelStyle}>Preference</label>
              <select
                id="form-preference"
                style={{ ...inputStyle, cursor: 'pointer' }}
                value={form.preference}
                onChange={(e) => handle('preference', e.target.value)}
                onFocus={(e) => (e.target.style.borderColor = '#0ea5e9')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              >
                <option value="automatic">Automatic</option>
                <option value="cheapest">Cheapest</option>
                <option value="earliest">Earliest</option>
                <option value="fastest">Fastest</option>
              </select>
            </div>
          </div>

          <button
            id="structured-search-btn"
            type="submit"
            disabled={!form.from || !form.to || !form.date || loading}
            className="btn-primary"
            style={{ width: '100%' }}
          >
            Search Flights ✈️
          </button>
        </form>
      )}
    </div>
  );
}
