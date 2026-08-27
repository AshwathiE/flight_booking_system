import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
} from "react";

import {
  sendChatMessage,
  clearChatHistory,
  downloadTicketPdfApi,
} from "../services/api";

import type {
  ChatResponse,
  ChatFlightData,
  ChatBookingSuccessData,
  ChatTicketData,
} from "../services/api";

import { useAuth } from "../context/AuthContext";

// ============================================================================
// TYPES
// ============================================================================

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  type: ChatResponse["type"];
  data: ChatResponse["data"];
  timestamp: Date;
  isLoading?: boolean;
}

interface SelectedFlight {
  flight: any;
  numberOfSeats: number;
}

// ============================================================================
// HELPERS
// ============================================================================

function createId(): string {
  return `${Date.now()}-${Math.random()
    .toString(36)
    .substring(2, 9)}`;
}

function formatPrice(
  price: number | string | null | undefined
): string {
  if (
    price === null ||
    price === undefined ||
    price === ""
  ) {
    return "N/A";
  }

  const numericPrice = Number(price);

  if (Number.isNaN(numericPrice)) {
    return "N/A";
  }

  return `₹${numericPrice.toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`;
}

function formatTime(
  time: string | null | undefined
): string {
  if (!time) return "N/A";

  return String(time).substring(0, 5);
}

function formatDate(
  date: string | null | undefined
): string {
  if (!date) return "N/A";

  try {
    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return String(date);
    }

    return parsedDate.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return String(date);
  }
}

// ============================================================================
// FLIGHT RESULT CARD
// ============================================================================

interface FlightResultCardProps {
  flight: any;
  isRecommended?: boolean;
  onSelect: (flight: any) => void;
  disabled?: boolean;
}

function FlightResultCard({
  flight,
  isRecommended = false,
  onSelect,
  disabled = false,
}: FlightResultCardProps) {
  const fare = flight?.fare ?? {};

  const totalFare =
    fare?.total_fare ??
    fare?.total_price ??
    flight?.price ??
    null;

  const baseFare =
    fare?.base_fare ??
    flight?.price ??
    null;

  const soldOut =
    Number(flight?.available_seats ?? 0) <= 0;

  return (
    <div
      style={{
        background: isRecommended
          ? "linear-gradient(135deg, rgba(14,165,233,0.08), rgba(99,102,241,0.08))"
          : "rgba(255,255,255,0.95)",
        border: isRecommended
          ? "1.5px solid #0ea5e9"
          : "1px solid #e2e8f0",
        borderRadius: 14,
        padding: 16,
        marginBottom: 10,
        position: "relative",
        boxShadow: isRecommended
          ? "0 4px 20px rgba(14,165,233,0.15)"
          : "0 2px 8px rgba(0,0,0,0.04)",
      }}
    >
      {isRecommended && (
        <div
          style={{
            position: "absolute",
            top: -10,
            left: 14,
            background:
              "linear-gradient(90deg,#0ea5e9,#6366f1)",
            color: "#fff",
            fontSize: 10,
            fontWeight: 700,
            padding: "3px 10px",
            borderRadius: 999,
            letterSpacing: "0.05em",
          }}
        >
          ⭐ RECOMMENDED
        </div>
      )}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        {/* Airline */}
        <div style={{ minWidth: 140 }}>
          <div
            style={{
              fontWeight: 700,
              fontSize: 15,
              color: "#0f172a",
            }}
          >
            {flight?.airline || "Unknown Airline"}
          </div>

          <div
            style={{
              fontSize: 12,
              color: "#64748b",
              marginTop: 3,
            }}
          >
            {flight?.flight_id || "N/A"} ·{" "}
            {flight?.travel_class || "Economy"}
          </div>
        </div>

        {/* Route */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                fontSize: 17,
                fontWeight: 700,
                color: "#0f172a",
              }}
            >
              {formatTime(flight?.departure_time)}
            </div>

            <div
              style={{
                fontSize: 11,
                color: "#64748b",
              }}
            >
              {flight?.origin || "N/A"}
            </div>
          </div>

          <div
            style={{
              color: "#94a3b8",
              fontSize: 18,
            }}
          >
            ✈
          </div>

          <div style={{ textAlign: "center" }}>
            <div
              style={{
                fontSize: 17,
                fontWeight: 700,
                color: "#0f172a",
              }}
            >
              {formatTime(flight?.arrival_time)}
            </div>

            <div
              style={{
                fontSize: 11,
                color: "#64748b",
              }}
            >
              {flight?.destination || "N/A"}
            </div>
          </div>
        </div>

        {/* Seats */}
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              fontSize: 13,
              color: soldOut
                ? "#ef4444"
                : "#10b981",
              fontWeight: 600,
            }}
          >
            {flight?.available_seats ?? 0} seats
          </div>

          <div
            style={{
              fontSize: 11,
              color: "#94a3b8",
            }}
          >
            {flight?.date
              ? formatDate(flight.date)
              : ""}
          </div>
        </div>

        {/* Fare */}
        <div
          style={{
            textAlign: "right",
            minWidth: 100,
          }}
        >
          <div
            style={{
              fontSize: 18,
              fontWeight: 800,
              color: "#0ea5e9",
            }}
          >
            {formatPrice(totalFare)}
          </div>

          {baseFare !== null &&
            totalFare !== null &&
            Number(baseFare) !== Number(totalFare) && (
              <div
                style={{
                  fontSize: 10,
                  color: "#94a3b8",
                }}
              >
                Base {formatPrice(baseFare)}
              </div>
            )}
        </div>

        {/* Select */}
        <button
          type="button"
          disabled={disabled || soldOut}
          onClick={() => onSelect(flight)}
          style={{
            background:
              disabled || soldOut
                ? "#cbd5e1"
                : "linear-gradient(135deg,#0ea5e9,#0284c7)",
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "8px 16px",
            fontSize: 13,
            fontWeight: 600,
            cursor:
              disabled || soldOut
                ? "not-allowed"
                : "pointer",
          }}
        >
          {soldOut ? "Sold Out" : "Select"}
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// FLIGHT RESULTS
// ============================================================================

function FlightResultsBlock({
  data,
  onSelect,
  disabled,
}: {
  data: ChatFlightData;
  onSelect: (flight: any) => void;
  disabled?: boolean;
}) {
  const flights = data?.flights ?? [];
  const recommended = data?.recommended_flight;
  const params = data?.search_parameters;

  if (!flights.length) {
    return (
      <div
        style={{
          padding: "10px 0",
          color: "#64748b",
          fontStyle: "italic",
        }}
      >
        No flights found for the given criteria.
      </div>
    );
  }

  return (
    <div style={{ marginTop: 8 }}>
      {params && (
        <div
          style={{
            fontSize: 12,
            color: "#64748b",
            marginBottom: 12,
            display: "flex",
            gap: 12,
            flexWrap: "wrap",
          }}
        >
          {params.origin && (
            <span>
              🛫 {params.origin} → {params.destination}
            </span>
          )}

          {params.date && (
            <span>
              📅 {formatDate(params.date)}
            </span>
          )}

          {params.total_seats && (
            <span>
              👤 {params.total_seats} passenger
              {Number(params.total_seats) !== 1
                ? "s"
                : ""}
            </span>
          )}

          {params.travel_class && (
            <span>
              💺 {params.travel_class}
            </span>
          )}
        </div>
      )}

      {data.recommendation_reason && (
        <div
          style={{
            fontSize: 12,
            color: "#475569",
            marginBottom: 10,
          }}
        >
          <strong>Recommendation:</strong>{" "}
          {data.recommendation_reason}
        </div>
      )}

      {flights.map((flight: any, index: number) => (
        <FlightResultCard
          key={
            flight?.flight_id ??
            `${flight?.airline}-${index}`
          }
          flight={flight}
          isRecommended={
            Boolean(
              recommended?.flight_id &&
              flight?.flight_id ===
              recommended.flight_id
            )
          }
          onSelect={onSelect}
          disabled={disabled}
        />
      ))}
    </div>
  );
}

// ============================================================================
// SELECTED FLIGHT / CONFIRMATION
// ============================================================================

function SelectedFlightBlock({
  selectedFlight,
  onSeatsChange,
  onConfirm,
  onCancel,
  disabled,
}: {
  selectedFlight: SelectedFlight;
  onSeatsChange: (value: number) => void;
  onConfirm: () => void;
  onCancel: () => void;
  disabled: boolean;
}) {
  const flight = selectedFlight.flight;

  const price =
    flight?.fare?.total_fare ??
    flight?.fare?.total_price ??
    flight?.price ??
    0;

  const seats = selectedFlight.numberOfSeats;

  const totalPrice = Number(price) * seats;

  const availableSeats = Number(
    flight?.available_seats ?? 0
  );

  return (
    <div
      style={{
        margin: "0 20px 12px",
        background: "#ffffff",
        border: "2px solid #0ea5e9",
        borderRadius: 16,
        padding: 16,
        boxShadow:
          "0 6px 20px rgba(14,165,233,0.15)",
      }}
    >
      <div
        style={{
          fontSize: 15,
          fontWeight: 700,
          color: "#0f172a",
          marginBottom: 12,
        }}
      >
        ✈ Selected Flight
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit,minmax(130px,1fr))",
          gap: 10,
          fontSize: 13,
          color: "#475569",
        }}
      >
        <div>
          Airline
          <strong
            style={{
              display: "block",
              color: "#0f172a",
            }}
          >
            {flight?.airline || "N/A"}
          </strong>
        </div>

        <div>
          Flight
          <strong
            style={{
              display: "block",
              color: "#0f172a",
            }}
          >
            {flight?.flight_id || "N/A"}
          </strong>
        </div>

        <div>
          Route
          <strong
            style={{
              display: "block",
              color: "#0f172a",
            }}
          >
            {flight?.origin} → {flight?.destination}
          </strong>
        </div>

        <div>
          Date
          <strong
            style={{
              display: "block",
              color: "#0f172a",
            }}
          >
            {formatDate(flight?.date)}
          </strong>
        </div>
      </div>

      <div
        style={{
          marginTop: 16,
          display: "flex",
          alignItems: "center",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <label
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: "#334155",
          }}
        >
          Number of seats:
        </label>

        <select
          value={seats}
          onChange={(event) =>
            onSeatsChange(
              Number(event.target.value)
            )
          }
          disabled={disabled}
          style={{
            border: "1px solid #cbd5e1",
            borderRadius: 8,
            padding: "7px 12px",
            fontSize: 13,
          }}
        >
          {Array.from(
            {
              length: Math.min(
                availableSeats,
                9
              ),
            },
            (_, index) => index + 1
          ).map((number) => (
            <option
              key={number}
              value={number}
            >
              {number}
            </option>
          ))}
        </select>

        <div
          style={{
            marginLeft: "auto",
            fontSize: 16,
            fontWeight: 800,
            color: "#0ea5e9",
          }}
        >
          Total: {formatPrice(totalPrice)}
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: 10,
          marginTop: 16,
        }}
      >
        <button
          type="button"
          onClick={onCancel}
          disabled={disabled}
          style={{
            flex: 1,
            background: "#f1f5f9",
            color: "#475569",
            border: "1px solid #cbd5e1",
            borderRadius: 10,
            padding: "10px 16px",
            fontWeight: 600,
            cursor: disabled
              ? "not-allowed"
              : "pointer",
          }}
        >
          Cancel
        </button>

        <button
          type="button"
          onClick={onConfirm}
          disabled={disabled}
          style={{
            flex: 2,
            background: disabled
              ? "#94a3b8"
              : "linear-gradient(135deg,#10b981,#059669)",
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "10px 16px",
            fontWeight: 700,
            cursor: disabled
              ? "not-allowed"
              : "pointer",
          }}
        >
          {disabled
            ? "Booking..."
            : "✓ Confirm & Book"}
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// BOOKING SUCCESS
// ============================================================================

function BookingSuccessBlock({
  data,
  onDownload,
  downloadingId,
}: {
  data: ChatBookingSuccessData;
  onDownload: (bookingId: number) => void;
  downloadingId: number | null;
}) {
  const bookingId = Number(
    data?.booking_id
  );

  return (
    <div
      style={{
        background:
          "linear-gradient(135deg, rgba(16,185,129,0.08), rgba(14,165,233,0.08))",
        border: "1.5px solid #10b981",
        borderRadius: 14,
        padding: "16px 18px",
        marginTop: 8,
      }}
    >
      <div
        style={{
          fontWeight: 700,
          fontSize: 15,
          color: "#064e3b",
          marginBottom: 12,
        }}
      >
        🎉 Booking Confirmed!
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit,minmax(140px,1fr))",
          gap: "7px 16px",
          fontSize: 13,
        }}
      >
        <div>
          <span style={{ color: "#64748b" }}>
            Reference:
          </span>{" "}
          <strong>
            {data?.booking_reference || "N/A"}
          </strong>
        </div>

        <div>
          <span style={{ color: "#64748b" }}>
            Flight:
          </span>{" "}
          <strong>
            {data?.flight_id || "N/A"}
          </strong>
        </div>

        <div>
          <span style={{ color: "#64748b" }}>
            Seats:
          </span>{" "}
          <strong>
            {data?.number_of_seats ?? 1}
          </strong>
        </div>

        <div>
          <span style={{ color: "#64748b" }}>
            Total:
          </span>{" "}
          <strong
            style={{ color: "#0ea5e9" }}
          >
            {formatPrice(data?.total_price)}
          </strong>
        </div>

        <div>
          <span style={{ color: "#64748b" }}>
            Status:
          </span>{" "}
          <strong
            style={{
              color: "#065f46",
            }}
          >
            {data?.status || "CONFIRMED"}
          </strong>
        </div>
      </div>

      {bookingId > 0 && (
        <button
          type="button"
          disabled={
            downloadingId === bookingId
          }
          onClick={() =>
            onDownload(bookingId)
          }
          style={{
            marginTop: 14,
            background:
              downloadingId === bookingId
                ? "#94a3b8"
                : "linear-gradient(135deg,#0ea5e9,#0284c7)",
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "10px 20px",
            fontSize: 13,
            fontWeight: 600,
            cursor:
              downloadingId === bookingId
                ? "not-allowed"
                : "pointer",
          }}
        >
          {downloadingId === bookingId
            ? "Preparing PDF..."
            : "📄 Download Ticket"}
        </button>
      )}
    </div>
  );
}

// ============================================================================
// BOOKING SUMMARY
// ============================================================================

function BookingSummaryBlock({
  data,
  onDownload,
  downloadingId,
}: {
  data: any;
  onDownload: (bookingId: number) => void;
  downloadingId: number | null;
}) {
  const bookings: any[] = Array.isArray(
    data?.bookings
  )
    ? data.bookings
    : data?.booking_id || data?.id
      ? [data]
      : [];

  if (!bookings.length) {
    return null;
  }

  return (
    <div style={{ marginTop: 8 }}>
      {bookings.map(
        (booking, index) => {
          const bookingId = Number(
            booking?.booking_id ??
            booking?.id
          );

          const status =
            booking?.status || "UNKNOWN";

          const isConfirmed =
            status.toUpperCase() ===
            "CONFIRMED";

          const isCancelled =
            status.toUpperCase() ===
            "CANCELLED";

          return (
            <div
              key={
                bookingId > 0
                  ? bookingId
                  : `booking-${index}`
              }
              style={{
                background:
                  "rgba(255,255,255,0.95)",
                border:
                  "1px solid #e2e8f0",
                borderRadius: 12,
                padding: "12px 14px",
                marginBottom: 8,
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent:
                    "space-between",
                  alignItems: "center",
                  marginBottom: 8,
                }}
              >
                <span
                  style={{
                    fontWeight: 700,
                    fontSize: 14,
                  }}
                >
                  {booking?.booking_reference ||
                    `#${bookingId}`}
                </span>

                <span
                  style={{
                    padding: "2px 10px",
                    borderRadius: 999,
                    fontSize: 11,
                    fontWeight: 700,
                    background:
                      isConfirmed
                        ? "#d1fae5"
                        : isCancelled
                          ? "#fee2e2"
                          : "#fef3c7",
                    color:
                      isConfirmed
                        ? "#065f46"
                        : isCancelled
                          ? "#991b1b"
                          : "#92400e",
                  }}
                >
                  {status}
                </span>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit,minmax(130px,1fr))",
                  gap: "5px 12px",
                  fontSize: 12,
                  color: "#475569",
                }}
              >
                <div>
                  Flight:{" "}
                  <strong>
                    {booking?.flight_id ||
                      "N/A"}
                  </strong>
                </div>

                <div>
                  Seats:{" "}
                  <strong>
                    {booking?.number_of_seats ??
                      "N/A"}
                  </strong>
                </div>

                <div>
                  Total:{" "}
                  <strong
                    style={{
                      color: "#0ea5e9",
                    }}
                  >
                    {formatPrice(
                      booking?.total_price
                    )}
                  </strong>
                </div>
              </div>

              {bookingId > 0 &&
                isConfirmed && (
                  <button
                    type="button"
                    disabled={
                      downloadingId ===
                      bookingId
                    }
                    onClick={() =>
                      onDownload(
                        bookingId
                      )
                    }
                    style={{
                      marginTop: 10,
                      background:
                        downloadingId ===
                          bookingId
                          ? "#94a3b8"
                          : "linear-gradient(135deg,#0ea5e9,#0284c7)",
                      color: "#fff",
                      border: "none",
                      borderRadius: 8,
                      padding:
                        "7px 14px",
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    {downloadingId ===
                      bookingId
                      ? "Preparing..."
                      : "📄 Download Ticket"}
                  </button>
                )}
            </div>
          );
        }
      )}
    </div>
  );
}

// ============================================================================
// TICKET
// ============================================================================

function TicketBlock({
  data,
  onDownload,
  downloadingId,
}: {
  data: ChatTicketData;
  onDownload: (bookingId: number) => void;
  downloadingId: number | null;
}) {
  const bookingId = Number(
    data?.booking_id
  );

  return (
    <div
      style={{
        background:
          "linear-gradient(135deg, rgba(99,102,241,0.08), rgba(14,165,233,0.08))",
        border: "1.5px solid #6366f1",
        borderRadius: 14,
        padding: "14px 16px",
        marginTop: 8,
      }}
    >
      <div
        style={{
          fontWeight: 700,
          color: "#312e81",
          marginBottom: 10,
        }}
      >
        🎫{" "}
        {data?.booking_reference ||
          `Booking #${bookingId}`}
      </div>

      <div
        style={{
          fontSize: 12,
          color: "#64748b",
          marginBottom: 12,
        }}
      >
        Flight:{" "}
        <strong>
          {data?.flight_id || "N/A"}
        </strong>
      </div>

      {bookingId > 0 && (
        <button
          type="button"
          disabled={
            downloadingId === bookingId
          }
          onClick={() =>
            onDownload(bookingId)
          }
          style={{
            background:
              downloadingId === bookingId
                ? "#94a3b8"
                : "linear-gradient(135deg,#6366f1,#4f46e5)",
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "10px 22px",
            fontSize: 14,
            fontWeight: 700,
          }}
        >
          {downloadingId === bookingId
            ? "Preparing PDF..."
            : "📥 Download Ticket PDF"}
        </button>
      )}
    </div>
  );
}

// ============================================================================
// TYPING INDICATOR
// ============================================================================

function TypingIndicator() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          background:
            "linear-gradient(135deg,#0ea5e9,#6366f1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        ✈
      </div>

      <div
        style={{
          display: "flex",
          gap: 4,
        }}
      >
        {[0, 1, 2].map(
          (item) => (
            <div
              key={item}
              className="dot-bounce"
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "#94a3b8",
                animationDelay:
                  `${item * 0.2}s`,
              }}
            />
          )
        )}
      </div>
    </div>
  );
}

// ============================================================================
// MESSAGE BUBBLE
// ============================================================================

function MessageBubble({
  message,
  onFlightSelect,
  onDownload,
  downloadingId,
  isLoading,
}: {
  message: Message;
  onFlightSelect: (flight: any) => void;
  onDownload: (bookingId: number) => void;
  downloadingId: number | null;
  isLoading: boolean;
}) {
  const isUser =
    message.role === "user";

  const formatMessage = (
    text: string
  ) => {
    if (!text) return "";

    return text
      .replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
      )
      .replace(/\n/g, "<br />");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: isUser
          ? "row-reverse"
          : "row",
        alignItems: "flex-start",
        gap: 10,
        marginBottom: 16,
      }}
    >
      {!isUser && (
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: "50%",
            background:
              "linear-gradient(135deg,#0ea5e9,#6366f1)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            color: "#fff",
          }}
        >
          ✈
        </div>
      )}

      <div
        style={{
          maxWidth: "78%",
          minWidth: 60,
        }}
      >
        <div
          style={{
            background: isUser
              ? "linear-gradient(135deg,#0ea5e9,#0284c7)"
              : message.type === "error"
                ? "rgba(239,68,68,0.06)"
                : "rgba(255,255,255,0.95)",

            color: isUser
              ? "#fff"
              : "#0f172a",

            borderRadius: isUser
              ? "18px 18px 4px 18px"
              : "18px 18px 18px 4px",

            padding: "10px 14px",
            fontSize: 14,
            lineHeight: 1.6,

            border: isUser
              ? "none"
              : message.type === "error"
                ? "1px solid rgba(239,68,68,0.2)"
                : "1px solid #e2e8f0",
          }}
        >
          {message.isLoading ? (
            <TypingIndicator />
          ) : (
            <span
              dangerouslySetInnerHTML={{
                __html:
                  formatMessage(
                    message.content
                  ),
              }}
            />
          )}
        </div>

        {!isUser &&
          !message.isLoading && (
            <>
              {message.type ===
                "flight_results" &&
                message.data && (
                  <FlightResultsBlock
                    data={
                      message.data as ChatFlightData
                    }
                    onSelect={
                      onFlightSelect
                    }
                    disabled={isLoading}
                  />
                )}

              {message.type ===
                "booking_success" &&
                message.data && (
                  <BookingSuccessBlock
                    data={
                      message.data as ChatBookingSuccessData
                    }
                    onDownload={
                      onDownload
                    }
                    downloadingId={
                      downloadingId
                    }
                  />
                )}

              {message.type ===
                "booking_summary" &&
                message.data && (
                  <BookingSummaryBlock
                    data={
                      message.data
                    }
                    onDownload={
                      onDownload
                    }
                    downloadingId={
                      downloadingId
                    }
                  />
                )}

              {message.type ===
                "ticket" &&
                message.data && (
                  <TicketBlock
                    data={
                      message.data as ChatTicketData
                    }
                    onDownload={
                      onDownload
                    }
                    downloadingId={
                      downloadingId
                    }
                  />
                )}
            </>
          )}

        <div
          style={{
            fontSize: 10,
            color: isUser
              ? "rgba(255,255,255,0.6)"
              : "#94a3b8",
            textAlign: isUser
              ? "right"
              : "left",
            marginTop: 4,
          }}
        >
          {message.timestamp.toLocaleTimeString(
            "en-IN",
            {
              hour: "2-digit",
              minute: "2-digit",
            }
          )}
        </div>
      </div>

      {isUser && (
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: "50%",
            background:
              "linear-gradient(135deg,#6366f1,#8b5cf6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            color: "#fff",
          }}
        >
          👤
        </div>
      )}
    </div>
  );
}

// ============================================================================
// QUICK SUGGESTIONS
// ============================================================================

const QUICK_SUGGESTIONS = [
  "Find flights from Chennai to Delhi tomorrow",
  "Show cheap flights for 2 people",
  "Show my bookings",
  "Download my ticket",
];

// ============================================================================
// MAIN AI ASSISTANT
// ============================================================================

export default function AIAssistant() {
  const {
    userToken,
    user,
    isLoading: authLoading,
  } = useAuth();

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [input, setInput] =
    useState("");

  const [isLoading, setIsLoading] =
    useState(false);

  const [downloadingId, setDownloadingId] =
    useState<number | null>(null);

  // NEW:
  // Stores selected flight before booking
  const [selectedFlight, setSelectedFlight] =
    useState<SelectedFlight | null>(null);

  const messagesEndRef =
    useRef<HTMLDivElement>(null);

  const inputRef =
    useRef<HTMLTextAreaElement>(null);

  // ==========================================================================
  // WELCOME
  // ==========================================================================

  useEffect(() => {
    if (authLoading) return;

    setMessages([
      {
        id: createId(),
        role: "assistant",
        content: `Hello${user?.name
            ? ` ${user.name}`
            : ""
          }! 👋 I'm your AI Flight Assistant.

I can help you:

• Search and compare flights
• Select and book seats
• View your bookings
• Manage bookings
• Download your ticket PDF

Try: "Find flights from Chennai to Delhi tomorrow for 2 people"`,

        type: "text",
        data: null,
        timestamp: new Date(),
      },
    ]);
  }, [
    authLoading,
    user?.name,
  ]);

  // ==========================================================================
  // AUTO SCROLL
  // ==========================================================================

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [
    messages,
    selectedFlight,
  ]);

  // ==========================================================================
  // SEND MESSAGE
  // ==========================================================================

  const handleSend = useCallback(
    async (messageText?: string) => {
      const text = (
        messageText ?? input
      ).trim();

      if (
        !text ||
        isLoading ||
        !userToken
      ) {
        return;
      }

      setInput("");

      const userMessage: Message = {
        id: createId(),
        role: "user",
        content: text,
        type: "text",
        data: null,
        timestamp: new Date(),
      };

      const loadingMessage: Message = {
        id: createId(),
        role: "assistant",
        content: "",
        type: "text",
        data: null,
        timestamp: new Date(),
        isLoading: true,
      };

      setMessages(
        (previous) => [
          ...previous,
          userMessage,
          loadingMessage,
        ]
      );

      setIsLoading(true);

      try {
        const response =
          await sendChatMessage(
            text,
            userToken
          );

        const assistantMessage: Message = {
          id: createId(),
          role: "assistant",
          content:
            response?.message ||
            "I received your request.",
          type:
            response?.type || "text",
          data:
            response?.data ?? null,
          timestamp: new Date(),
        };

        setMessages(
          (previous) => {
            const index =
              previous.findIndex(
                (message) =>
                  message.id ===
                  loadingMessage.id
              );

            if (index === -1) {
              return [
                ...previous,
                assistantMessage,
              ];
            }

            const updated = [
              ...previous,
            ];

            updated[index] =
              assistantMessage;

            return updated;
          }
        );
      } catch (error: any) {
        console.error(
          "AI Assistant error:",
          error
        );

        const errorDetail =
          error?.response?.data?.detail;

        const errorMessage =
          typeof errorDetail ===
            "string"
            ? errorDetail
            : error?.message ||
            "Something went wrong. Please try again.";

        setMessages(
          (previous) => {
            const index =
              previous.findIndex(
                (message) =>
                  message.id ===
                  loadingMessage.id
              );

            const errorObject: Message = {
              id: createId(),
              role: "assistant",
              content: `I'm sorry, I encountered an error: ${errorMessage}`,
              type: "error",
              data: null,
              timestamp: new Date(),
            };

            if (index === -1) {
              return [
                ...previous,
                errorObject,
              ];
            }

            const updated = [
              ...previous,
            ];

            updated[index] =
              errorObject;

            return updated;
          }
        );
      } finally {
        setIsLoading(false);

        setTimeout(() => {
          inputRef.current?.focus();
        }, 0);
      }
    },
    [
      input,
      isLoading,
      userToken,
    ]
  );

  // ==========================================================================
  // SELECT FLIGHT
  //
  // IMPORTANT:
  // Selecting a flight DOES NOT BOOK IT.
  // ==========================================================================

  const handleFlightSelect =
    useCallback(
      (flight: any) => {
        if (!flight) return;

        const availableSeats = Number(
          flight?.available_seats ?? 0
        );

        if (availableSeats <= 0) {
          return;
        }

        // Only store the selected flight.
        // DO NOT call handleSend() here.
        setSelectedFlight({
          flight,
          numberOfSeats: 1,
        });
      },
      []
    );

  // ==========================================================================
  // CHANGE NUMBER OF SEATS
  // ==========================================================================

  const handleSeatsChange =
    useCallback(
      (numberOfSeats: number) => {
        if (!selectedFlight) return;

        const availableSeats =
          Number(
            selectedFlight.flight
              ?.available_seats ?? 0
          );

        if (
          numberOfSeats < 1 ||
          numberOfSeats >
          availableSeats
        ) {
          return;
        }

        setSelectedFlight({
          ...selectedFlight,
          numberOfSeats,
        });
      },
      [selectedFlight]
    );

  // ==========================================================================
  // CONFIRM BOOKING
  //
  // This is the ONLY point where we send the booking
  // command to the backend.
  // ==========================================================================

  const handleConfirmBooking =
    useCallback(() => {
      if (
        !selectedFlight ||
        !userToken
      ) {
        return;
      }

      const flight =
        selectedFlight.flight;

      const seats =
        selectedFlight.numberOfSeats;

      const bookingMessage =
        `Book flight ${flight?.flight_id} for ${seats} seat${seats !== 1 ? "s" : ""
        }`;

      setSelectedFlight(null);

      handleSend(bookingMessage);
    }, [
      selectedFlight,
      userToken,
      handleSend,
    ]);

  // ==========================================================================
  // CANCEL FLIGHT SELECTION
  // ==========================================================================

  const handleCancelSelection =
    useCallback(() => {
      setSelectedFlight(null);
    }, []);

  // ==========================================================================
  // DOWNLOAD TICKET
  // ==========================================================================

  const handleDownload =
    useCallback(
      async (bookingId: number) => {
        if (
          !userToken ||
          !bookingId ||
          downloadingId !== null
        ) {
          return;
        }

        setDownloadingId(bookingId);

        try {
          const blob =
            await downloadTicketPdfApi(
              bookingId,
              userToken
            );

          if (!(blob instanceof Blob)) {
            throw new Error(
              "Invalid PDF response"
            );
          }

          const url =
            window.URL.createObjectURL(
              blob
            );

          const link =
            document.createElement("a");

          link.href = url;
          link.download =
            `ticket_${bookingId}.pdf`;

          document.body.appendChild(
            link
          );

          link.click();

          document.body.removeChild(
            link
          );

          window.URL.revokeObjectURL(
            url
          );
        } catch (error) {
          console.error(
            "Ticket download error:",
            error
          );

          setMessages(
            (previous) => [
              ...previous,
              {
                id: createId(),
                role: "assistant",
                content:
                  "Sorry, I could not generate the ticket PDF. Please try again.",
                type: "error",
                data: null,
                timestamp: new Date(),
              },
            ]
          );
        } finally {
          setDownloadingId(null);
        }
      },
      [
        userToken,
        downloadingId,
      ]
    );

  // ==========================================================================
  // CLEAR HISTORY
  // ==========================================================================

  const handleClearHistory =
    useCallback(async () => {
      if (!userToken) return;

      try {
        await clearChatHistory(
          userToken
        );
      } catch (error) {
        console.warn(
          "Could not clear server chat history:",
          error
        );
      }

      setSelectedFlight(null);

      setMessages([
        {
          id: createId(),
          role: "assistant",
          content:
            "Conversation cleared. How can I help you?",
          type: "text",
          data: null,
          timestamp: new Date(),
        },
      ]);

      setInput("");
    }, [userToken]);

  // ==========================================================================
  // KEYBOARD
  // ==========================================================================

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      handleSend();
    }
  };

  // ==========================================================================
  // AUTH LOADING
  // ==========================================================================

  if (authLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background:
            "linear-gradient(135deg,#0f172a,#1e1b4b)",
          color: "#fff",
        }}
      >
        Loading AI Assistant...
      </div>
    );
  }

  if (!userToken) {
    return null;
  }

  // ==========================================================================
  // UI
  // ==========================================================================

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0c1445 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "24px 0",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 820,
          padding: "0 16px",
          display: "flex",
          flexDirection: "column",
          height: "calc(100vh - 48px)",
        }}
      >
        {/* HEADER */}
        <div
          style={{
            background:
              "rgba(255,255,255,0.05)",
            backdropFilter:
              "blur(20px)",
            border:
              "1px solid rgba(255,255,255,0.1)",
            borderRadius:
              "20px 20px 0 0",
            padding: "18px 22px",
            display: "flex",
            alignItems: "center",
            justifyContent:
              "space-between",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
            }}
          >
            <div
              style={{
                width: 46,
                height: 46,
                borderRadius: "50%",
                background:
                  "linear-gradient(135deg,#0ea5e9,#6366f1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 22,
              }}
            >
              ✈
            </div>

            <div>
              <div
                style={{
                  color: "#fff",
                  fontWeight: 700,
                  fontSize: 18,
                }}
              >
                AI Flight Assistant
              </div>

              <div
                style={{
                  color:
                    "rgba(255,255,255,0.5)",
                  fontSize: 12,
                }}
              >
                Powered by GPT · Always online
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={
              handleClearHistory
            }
            style={{
              background:
                "rgba(255,255,255,0.08)",
              border:
                "1px solid rgba(255,255,255,0.15)",
              borderRadius: 10,
              color:
                "rgba(255,255,255,0.7)",
              padding: "7px 14px",
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            🗑 Clear
          </button>
        </div>

        {/* MESSAGES */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            background:
              "linear-gradient(180deg,rgba(248,250,252,0.97),rgba(241,245,249,0.97))",
            padding: "20px",
            borderLeft:
              "1px solid rgba(255,255,255,0.08)",
            borderRight:
              "1px solid rgba(255,255,255,0.08)",
          }}
        >
          {messages.map(
            (message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onFlightSelect={
                  handleFlightSelect
                }
                onDownload={
                  handleDownload
                }
                downloadingId={
                  downloadingId
                }
                isLoading={
                  isLoading
                }
              />
            )
          )}

          <div
            ref={messagesEndRef}
          />
        </div>

        {/* SELECTED FLIGHT CONFIRMATION */}

        {selectedFlight && (
          <SelectedFlightBlock
            selectedFlight={
              selectedFlight
            }
            onSeatsChange={
              handleSeatsChange
            }
            onConfirm={
              handleConfirmBooking
            }
            onCancel={
              handleCancelSelection
            }
            disabled={isLoading}
          />
        )}

        {/* QUICK SUGGESTIONS */}

        {messages.length <= 1 &&
          !selectedFlight && (
            <div
              style={{
                background:
                  "rgba(248,250,252,0.97)",
                padding:
                  "10px 20px",
                display: "flex",
                gap: 8,
                flexWrap: "wrap",
                borderTop:
                  "1px solid #e2e8f0",
              }}
            >
              {QUICK_SUGGESTIONS.map(
                (suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    disabled={
                      isLoading
                    }
                    onClick={() =>
                      handleSend(
                        suggestion
                      )
                    }
                    style={{
                      background:
                        "white",
                      border:
                        "1px solid #e2e8f0",
                      borderRadius: 20,
                      padding:
                        "6px 14px",
                      fontSize: 12,
                      color:
                        "#475569",
                      cursor:
                        isLoading
                          ? "not-allowed"
                          : "pointer",
                    }}
                  >
                    {suggestion}
                  </button>
                )
              )}
            </div>
          )}

        {/* INPUT */}

        <div
          style={{
            background:
              "rgba(255,255,255,0.97)",
            borderRadius:
              "0 0 20px 20px",
            border:
              "1px solid rgba(255,255,255,0.1)",
            borderTop:
              "1px solid #e2e8f0",
            padding:
              "14px 16px",
            display: "flex",
            gap: 12,
            alignItems: "flex-end",
          }}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={(event) =>
              setInput(
                event.target.value
              )
            }
            onKeyDown={
              handleKeyDown
            }
            placeholder="Ask me about flights, bookings, or tickets..."
            rows={1}
            disabled={isLoading}
            style={{
              flex: 1,
              resize: "none",
              border:
                "1.5px solid #e2e8f0",
              borderRadius: 14,
              padding:
                "10px 14px",
              fontSize: 14,
              fontFamily:
                "inherit",
              color: "#0f172a",
              background: "white",
              outline: "none",
              lineHeight: 1.5,
              maxHeight: 120,
              overflowY: "auto",
            }}
          />

          <button
            type="button"
            onClick={() =>
              handleSend()
            }
            disabled={
              isLoading ||
              !input.trim()
            }
            style={{
              background:
                isLoading ||
                  !input.trim()
                  ? "#e2e8f0"
                  : "linear-gradient(135deg,#0ea5e9,#0284c7)",
              color:
                isLoading ||
                  !input.trim()
                  ? "#94a3b8"
                  : "#fff",
              border: "none",
              borderRadius: 14,
              width: 46,
              height: 46,
              fontSize: 18,
              cursor:
                isLoading ||
                  !input.trim()
                  ? "not-allowed"
                  : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent:
                "center",
              flexShrink: 0,
            }}
          >
            {isLoading ? (
              <div
                style={{
                  width: 18,
                  height: 18,
                  border:
                    "2px solid #94a3b8",
                  borderTop:
                    "2px solid #475569",
                  borderRadius: "50%",
                  animation:
                    "spin-slow 0.8s linear infinite",
                }}
              />
            ) : (
              "➤"
            )}
          </button>
        </div>
      </div>

      {/* ANIMATIONS */}

      <style>
        {`
          @keyframes spin-slow {
            from {
              transform: rotate(0deg);
            }

            to {
              transform: rotate(360deg);
            }
          }

          @keyframes dot-bounce {
            0%, 60%, 100% {
              transform: translateY(0);
              opacity: 0.5;
            }

            30% {
              transform: translateY(-4px);
              opacity: 1;
            }
          }

          .dot-bounce {
            animation:
              dot-bounce
              1.2s
              infinite
              ease-in-out;
          }
        `}
      </style>
    </div>
  );
}