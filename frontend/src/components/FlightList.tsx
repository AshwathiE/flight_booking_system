import React from 'react';
import type { Flight, SearchResponse } from '../types';
import RecommendedFlightCard from './RecommendedFlightCard';
import FlightCard from './FlightCard';
import { getRecommendedFlight, getOtherFlights } from '../services/flightService';

interface Props {
  searchResponse: SearchResponse;
  onSelectFlight: (flight: Flight) => void;
}

export default function FlightList({ searchResponse, onSelectFlight }: Props) {
  const { flights, search_parameters, recommendation_reason } = searchResponse;
  const recommended = getRecommendedFlight(searchResponse);
  const others = getOtherFlights(searchResponse);
  const totalPassengers = search_parameters.total_seats;

  return (
    <div>
      {recommended && (
        <RecommendedFlightCard
          flight={recommended}
          reason={recommendation_reason || ''}
          totalPassengers={totalPassengers}
          onSelect={onSelectFlight}
        />
      )}

      {others.length > 0 && (
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '16px',
              marginTop: recommended ? '8px' : 0,
            }}
          >
            <h2 style={{ fontSize: '17px', fontWeight: 700, color: '#0f172a' }}>
              Other Available Flights
            </h2>
            <span
              style={{
                background: '#f1f5f9',
                color: '#64748b',
                borderRadius: '999px',
                padding: '2px 10px',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              {others.length}
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {others.map((flight) => (
              <FlightCard
                key={flight.flight_id}
                flight={flight}
                totalPassengers={totalPassengers}
                onSelect={onSelectFlight}
              />
            ))}
          </div>
        </div>
      )}

      {flights.length > 0 && !recommended && others.length === 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {flights.map((flight) => (
            <FlightCard
              key={flight.flight_id}
              flight={flight}
              totalPassengers={totalPassengers}
              onSelect={onSelectFlight}
            />
          ))}
        </div>
      )}
    </div>
  );
}
