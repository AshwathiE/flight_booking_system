import React from 'react';
import type { FlightSearchRequest, SearchParameters } from "../types";
import { Plane, Calendar, Users, Edit2 } from 'lucide-react';
import { formatDate } from '../services/flightService';

interface Props {
  params: FlightSearchRequest | SearchParameters;
  totalFlights: number;
  onEditSearch: () => void;
}

export default function SearchSummary({ params, totalFlights, onEditSearch }: Props) {
  return (
    <div
      style={{
        background: 'linear-gradient(135deg, #0f172a, #1e293b)',
        borderRadius: '16px',
        padding: '24px',
        color: 'white',
        marginBottom: '24px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        {/* Route */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '2px' }}>From</div>
            <div style={{ fontSize: '22px', fontWeight: 700, textTransform: 'capitalize' }}>
              {params.origin}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0ea5e9' }}>
            <div style={{ height: '1px', width: '24px', background: '#334155' }} />
            <Plane size={22} />
            <div style={{ height: '1px', width: '24px', background: '#334155' }} />
          </div>
          <div>
            <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '2px' }}>To</div>
            <div style={{ fontSize: '22px', fontWeight: 700, textTransform: 'capitalize' }}>
              {params.destination}
            </div>
          </div>
        </div>

        {/* Meta */}
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calendar size={16} color="#7dd3fc" />
            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>Date</div>
              <div style={{ fontSize: '14px', fontWeight: 600 }}>{formatDate(params.date)}</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={16} color="#7dd3fc" />
            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>Passengers</div>
              <div style={{ fontSize: '14px', fontWeight: 600 }}>
                {'total_seats' in params ? params.total_seats : (params.passengers || 1)}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Plane size={16} color="#7dd3fc" />
            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>Class</div>
              <div style={{ fontSize: '14px', fontWeight: 600 }}>
                {('travel_class' in params && params.travel_class) ? params.travel_class : 'Economy'}
              </div>
            </div>
          </div>
        </div>

        {/* Edit + count */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
          <button
            id="edit-search-btn"
            onClick={onEditSearch}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '10px',
              padding: '8px 14px',
              color: 'white',
              cursor: 'pointer',
              fontFamily: 'inherit',
              fontSize: '13px',
              fontWeight: 500,
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.18)')
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.1)')
            }
          >
            <Edit2 size={13} />
            Edit Search
          </button>
          <span
            style={{
              fontSize: '13px',
              color: '#94a3b8',
              background: 'rgba(255,255,255,0.06)',
              borderRadius: '8px',
              padding: '4px 10px',
            }}
          >
            {totalFlights} flight{totalFlights !== 1 ? 's' : ''} available
          </span>
        </div>
      </div>
    </div>
  );
}
