import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { searchFlightsService } from '../services/flightService';

import SearchSummary from '../components/SearchSummary';
import FlightList from '../components/FlightList';
import LoadingState from '../components/LoadingState';
import EmptyState from '../components/EmptyState';
import ErrorMessage from '../components/ErrorMessage';
import NaturalLanguageSearch from '../components/NaturalLanguageSearch';

import type { Flight, SearchResponse } from '../types';

import { Plane, X } from 'lucide-react';

export default function SearchResults() {
  const navigate = useNavigate();
  const location = useLocation();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);

  // Store search result directly in React state, initialized from navigation state
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(
    (location.state as { searchResponse?: SearchResponse })?.searchResponse || null
  );

  useEffect(() => {
    if (!searchResponse && !loading) {
      navigate('/');
    }
  }, [searchResponse, loading, navigate]);

  const handleSearch = async (message: string) => {
    setError('');
    setLoading(true);
    setEditing(false);

    try {
      const response = await searchFlightsService(message);

      setSearchResponse(response);
    } catch (e: unknown) {
      setError(
        e instanceof Error
          ? e.message
          : 'Unable to search flights right now. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSelectFlight = (flight: Flight) => {
    console.log('Selected flight:', flight);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#f8fafc',
      }}
    >
      <div
        style={{
          maxWidth: '900px',
          margin: '0 auto',
          padding: '32px 24px',
        }}
      >
        {/* Edit search */}
        {editing && (
          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '20px',
              marginBottom: '24px',
              border: '1.5px solid #e2e8f0',
              boxShadow: '0 4px 16px rgba(15,23,42,0.06)',
            }}
          >
            <NaturalLanguageSearch
              onSearch={handleSearch}
              loading={loading}
              initialValue={searchResponse?.user_request || ''}
            />

            <button
              className="btn-ghost"
              style={{ marginTop: '12px' }}
              onClick={() => setEditing(false)}
            >
              <X size={14} />
              Cancel
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && <LoadingState />}

        {/* Error */}
        {!loading && error && (
          <ErrorMessage
            message={error}
            onRetry={() => setEditing(true)}
          />
        )}

        {/* Results */}
        {!loading && !error && searchResponse && (
          <>
            <SearchSummary
              params={searchResponse.search_parameters}
              totalFlights={searchResponse.flights.length}
              onEditSearch={() => setEditing(true)}
            />

            {searchResponse.flights.length === 0 ? (
              <EmptyState
                params={searchResponse.search_parameters}
              />
            ) : (
              <>
                <div style={{ marginBottom: '20px' }}>
                  <h2
                    style={{
                      fontSize: '20px',
                      fontWeight: 800,
                      color: '#0f172a',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    <Plane size={20} color="#0ea5e9" />

                    Available Flights

                    <span
                      style={{
                        background: '#e0f2fe',
                        color: '#0284c7',
                        borderRadius: '999px',
                        padding: '2px 10px',
                        fontSize: '13px',
                        fontWeight: 700,
                      }}
                    >
                      {searchResponse.flights.length}
                    </span>
                  </h2>
                </div>

                <FlightList
                  searchResponse={searchResponse}
                  onSelectFlight={handleSelectFlight}
                />
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}