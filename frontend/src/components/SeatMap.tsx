import React, { useState, useMemo } from 'react';

interface Props {
  requiredSeats: number;
  onConfirm: (seats: string[]) => void;
}

const ROWS = 20;
const COLS = ['A', 'B', 'C', 'D', 'E', 'F'];

// Pre-occupy some seats randomly (deterministic)
function getOccupied(): Set<string> {
  const occ = new Set<string>();
  const seeds = [2, 5, 8, 11, 14, 17, 3, 6, 9, 12, 15, 18, 1, 4, 7, 10, 13, 16];
  seeds.forEach((r, i) => {
    if (i % 3 === 0) occ.add(`${r}${COLS[i % 6]}`);
  });
  return occ;
}

export default function SeatMap({ requiredSeats, onConfirm }: Props) {
  const occupied = useMemo(() => getOccupied(), []);
  const [selected, setSelected] = useState<string[]>([]);

  const toggleSeat = (seat: string) => {
    if (occupied.has(seat)) return;
    setSelected((prev) =>
      prev.includes(seat)
        ? prev.filter((s) => s !== seat)
        : prev.length < requiredSeats
        ? [...prev, seat]
        : prev
    );
  };

  const done = selected.length === requiredSeats;

  return (
    <div>
      {/* Legend */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '24px', justifyContent: 'center' }}>
        {[
          { color: '#e0f2fe', border: '#7dd3fc', text: 'Available' },
          { color: '#0ea5e9', border: '#0284c7', text: 'Selected' },
          { color: '#f1f5f9', border: '#e2e8f0', text: 'Occupied' },
        ].map(({ color, border, text }) => (
          <div key={text} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div
              style={{
                width: '20px',
                height: '20px',
                borderRadius: '4px',
                background: color,
                border: `2px solid ${border}`,
              }}
            />
            <span style={{ fontSize: '13px', color: '#64748b' }}>{text}</span>
          </div>
        ))}
      </div>

      {/* Progress */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          padding: '12px 16px',
          background: done ? '#d1fae5' : '#f0f9ff',
          borderRadius: '10px',
          border: `1px solid ${done ? '#6ee7b7' : '#7dd3fc'}`,
        }}
      >
        <span style={{ fontSize: '14px', fontWeight: 600, color: done ? '#065f46' : '#0284c7' }}>
          {selected.length} / {requiredSeats} seats selected
        </span>
        {done && (
          <span style={{ fontSize: '13px', color: '#065f46', fontWeight: 700 }}>
            ✓ All seats selected!
          </span>
        )}
      </div>

      {/* Plane layout */}
      <div
        style={{
          overflowX: 'auto',
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div>
          {/* Cockpit */}
          <div
            style={{
              textAlign: 'center',
              marginBottom: '16px',
              fontSize: '32px',
            }}
          >
            ✈️
          </div>

          {/* Column labels */}
          <div
            style={{
              display: 'flex',
              gap: '4px',
              marginBottom: '8px',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <div style={{ width: '28px' }} />
            {COLS.map((c, i) => (
              <React.Fragment key={c}>
                {i === 3 && <div style={{ width: '20px' }} />}
                <div
                  style={{
                    width: '32px',
                    textAlign: 'center',
                    fontSize: '11px',
                    fontWeight: 700,
                    color: '#94a3b8',
                    letterSpacing: '1px',
                  }}
                >
                  {c}
                </div>
              </React.Fragment>
            ))}
          </div>

          {/* Rows */}
          {Array.from({ length: ROWS }, (_, ri) => {
            const row = ri + 1;
            return (
              <div
                key={row}
                style={{
                  display: 'flex',
                  gap: '4px',
                  marginBottom: '4px',
                  alignItems: 'center',
                }}
              >
                <div
                  style={{
                    width: '28px',
                    textAlign: 'right',
                    fontSize: '11px',
                    color: '#94a3b8',
                    fontWeight: 600,
                    paddingRight: '4px',
                  }}
                >
                  {row}
                </div>
                {COLS.map((col, ci) => {
                  const seatId = `${row}${col}`;
                  const isOccupied = occupied.has(seatId);
                  const isSelected = selected.includes(seatId);
                  return (
                    <React.Fragment key={seatId}>
                      {ci === 3 && <div style={{ width: '20px' }} />}
                      <button
                        id={`seat-${seatId}`}
                        onClick={() => toggleSeat(seatId)}
                        disabled={isOccupied}
                        className={`seat ${isOccupied ? 'occupied' : isSelected ? 'selected' : 'available'}`}
                        title={seatId}
                      >
                        {isSelected ? '✓' : ''}
                      </button>
                    </React.Fragment>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* Continue button */}
      <div style={{ marginTop: '32px', display: 'flex', justifyContent: 'center' }}>
        <button
          id="seat-confirm-btn"
          className="btn-primary"
          disabled={!done}
          onClick={() => onConfirm(selected)}
          style={{ padding: '14px 40px', fontSize: '15px' }}
        >
          Continue to Payment →
        </button>
      </div>
    </div>
  );
}
