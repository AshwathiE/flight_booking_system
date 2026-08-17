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


  const [searchResponse, setSearchResponse] =
    useState<SearchResponse | null>(
      (location.state as {
        searchResponse?: SearchResponse
      })?.searchResponse || null
    );


  // --------------------------------------------------
  // Redirect to home if there is no search response
  // --------------------------------------------------

  useEffect(() => {

    if (!searchResponse && !loading) {
      navigate('/');
    }

  }, [
    searchResponse,
    loading,
    navigate
  ]);


  // --------------------------------------------------
  // Search
  // --------------------------------------------------

  const handleSearch = async (message: string) => {

    setError('');

    setLoading(true);

    setEditing(false);


    try {

      const response =
        await searchFlightsService(message);

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


  // --------------------------------------------------
  // Select flight
  // --------------------------------------------------

  const handleSelectFlight = (flight: Flight) => {

    navigate('/booking', {

      state: {

        flight,

        passengers:
          searchResponse
            ?.search_parameters
            ?.total_seats || 1,

      },

    });

  };


  // --------------------------------------------------
  // Render
  // --------------------------------------------------

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


        {/* ================================================= */}
        {/* EDIT SEARCH                                      */}
        {/* ================================================= */}

        {editing && (

          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '20px',
              marginBottom: '24px',
              border: '1.5px solid #e2e8f0',
              boxShadow:
                '0 4px 16px rgba(15,23,42,0.06)',
            }}
          >

            <NaturalLanguageSearch

              onSearch={handleSearch}

              loading={loading}

              initialValue={
                searchResponse?.user_request || ''
              }

            />


            <button

              className="btn-ghost"

              style={{
                marginTop: '12px'
              }}

              onClick={() =>
                setEditing(false)
              }

            >

              <X size={14} />

              Cancel

            </button>

          </div>

        )}


        {/* ================================================= */}
        {/* LOADING                                           */}
        {/* ================================================= */}

        {loading && <LoadingState />}


        {/* ================================================= */}
        {/* API / NETWORK ERROR                               */}
        {/* ================================================= */}

        {!loading && error && (

          <ErrorMessage

            message={error}

            onRetry={() =>
              setEditing(true)
            }

          />

        )}


        {/* ================================================= */}
        {/* BACKEND RESPONSE                                  */}
        {/* ================================================= */}

        {!loading &&
          !error &&
          searchResponse && (

            <>

              {/* ----------------------------------------- */}
              {/* NEEDS INFORMATION                         */}
              {/* ----------------------------------------- */}

              {searchResponse.status ===
                'needs_information' && (

                  <ErrorMessage
                    message={
                      searchResponse.message ||
                      'Please provide the missing information.'
                    }
                    onRetry={() =>
                      setEditing(true)
                    }
                  />

                )}


              {/* ----------------------------------------- */}
              {/* VALIDATION ERROR                          */}
              {/* ----------------------------------------- */}

              {searchResponse.status ===
                'validation_error' && (

                  <ErrorMessage
                    message={
                      searchResponse.message ||
                      'The search request is invalid.'
                    }
                    onRetry={() =>
                      setEditing(true)
                    }
                  />

                )}


              {/* ----------------------------------------- */}
              {/* NO RESULTS                                */}
              {/* ----------------------------------------- */}

              {searchResponse.status ===
                'no_results' && (

                  <EmptyState
                    params={
                      searchResponse.search_parameters
                    }
                  />

                )}


              {/* ----------------------------------------- */}
              {/* NO AVAILABILITY                           */}
              {/* ----------------------------------------- */}

              {searchResponse.status ===
                'no_availability' && (

                  <EmptyState
                    params={
                      searchResponse.search_parameters
                    }
                  />

                )}


              {/* ----------------------------------------- */}
              {/* GENERAL BACKEND ERROR                     */}
              {/* ----------------------------------------- */}

              {searchResponse.status ===
                'error' && (

                  <ErrorMessage
                    message={
                      searchResponse.message ||
                      'Something went wrong.'
                    }
                    onRetry={() =>
                      setEditing(true)
                    }
                  />

                )}


              {/* ================================================= */}
              {/* SUCCESS                                           */}
              {/* ================================================= */}

              {searchResponse.status ===
                'success' && (

                  <>

                    {/* ----------------------------------------- */}
                    {/* SAFE FLIGHT ARRAY                         */}
                    {/* ----------------------------------------- */}

                    {(() => {

                      const flights =
                        searchResponse.flights ?? [];


                      return (

                        <>

                          {/* --------------------------------- */}
                          {/* SEARCH SUMMARY                   */}
                          {/* --------------------------------- */}

                          <SearchSummary

                            params={
                              searchResponse.search_parameters
                            }

                            totalFlights={
                              flights.length
                            }

                            onEditSearch={() =>
                              setEditing(true)
                            }

                          />


                          {/* --------------------------------- */}
                          {/* EMPTY RESULT                     */}
                          {/* --------------------------------- */}

                          {flights.length === 0 ? (

                            <EmptyState

                              params={
                                searchResponse.search_parameters
                              }

                            />

                          ) : (

                            <>

                              {/* ----------------------------- */}
                              {/* AVAILABLE FLIGHTS HEADER      */}
                              {/* ----------------------------- */}

                              <div
                                style={{
                                  marginBottom: '20px'
                                }}
                              >

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

                                  <Plane
                                    size={20}
                                    color="#0ea5e9"
                                  />


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

                                    {flights.length}

                                  </span>

                                </h2>

                              </div>


                              {/* ----------------------------- */}
                              {/* FLIGHT LIST                   */}
                              {/* ----------------------------- */}

                              <FlightList

                                searchResponse={
                                  searchResponse
                                }

                                onSelectFlight={
                                  handleSelectFlight
                                }

                              />

                            </>

                          )}

                        </>

                      );

                    })()}

                  </>

                )}

            </>

          )}

      </div>

    </div>

  );
}