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
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

function formatPrice(price: number | string | null | undefined): string {
  if (price === null || price === undefined || price === "") return "N/A";
  const n = Number(price);
  if (Number.isNaN(n)) return "N/A";
  return `\u20B9${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function formatTime(time: string | null | undefined): string {
  if (!time) return "N/A";
  return String(time).substring(0, 5);
}

function formatDate(date: string | null | undefined): string {
  if (!date) return "N/A";
  try {
    const d = new Date(date);
    if (Number.isNaN(d.getTime())) return String(date);
    return d.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return String(date);
  }
}

// ============================================================================
// TYPING INDICATOR
// ============================================================================

function TypingIndicator() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div
        style={{
          width: 24,
          height: 24,
          borderRadius: "50%",
          background: "linear-gradient(135deg,#0ea5e9,#6366f1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
          color: "#fff",
          flexShrink: 0,
        }}
      >
        {"\u2708"}
      </div>
      <div style={{ display: "flex", gap: 3 }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="fcb-dot-bounce"
            style={{
              width: 5,
              height: 5,
              borderRadius: "50%",
              background: "#94a3b8",
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// FLIGHT RESULT CARD
// ============================================================================

function FlightResultCard({
  flight,
  isRecommended = false,
  onSelect,
  disabled = false,
}: {
  flight: any;
  isRecommended?: boolean;
  onSelect: (flight: any) => void;
  disabled?: boolean;
}) {
  const fare = flight?.fare ?? {};
  const totalFare = fare?.total_fare ?? fare?.total_price ?? flight?.price ?? null;
  const soldOut = Number(flight?.available_seats ?? 0) <= 0;

  return (
    <div
      style={{
        background: isRecommended
          ? "linear-gradient(135deg,rgba(14,165,233,0.08),rgba(99,102,241,0.08))"
          : "rgba(255,255,255,0.95)",
        border: isRecommended ? "1.5px solid #0ea5e9" : "1px solid #e2e8f0",
        borderRadius: 10,
        padding: "10px 12px",
        marginBottom: 8,
        position: "relative",
      }}
    >
      {isRecommended && (
        <div
          style={{
            position: "absolute",
            top: -9,
            left: 10,
            background: "linear-gradient(90deg,#0ea5e9,#6366f1)",
            color: "#fff",
            fontSize: 9,
            fontWeight: 700,
            padding: "2px 8px",
            borderRadius: 999,
          }}
        >
          {"\u2B50"} BEST
        </div>
      )}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        <div style={{ minWidth: 90 }}>
          <div style={{ fontWeight: 700, fontSize: 12, color: "#0f172a" }}>
            {flight?.airline || "Unknown"}
          </div>
          <div style={{ fontSize: 10, color: "#64748b", marginTop: 1 }}>
            {flight?.flight_id || "N/A"}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#0f172a" }}>
              {formatTime(flight?.departure_time)}
            </div>
            <div style={{ fontSize: 10, color: "#64748b" }}>
              {flight?.origin || "N/A"}
            </div>
          </div>
          <div style={{ color: "#94a3b8", fontSize: 14 }}>{"\u2708"}</div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#0f172a" }}>
              {formatTime(flight?.arrival_time)}
            </div>
            <div style={{ fontSize: 10, color: "#64748b" }}>
              {flight?.destination || "N/A"}
            </div>
          </div>
        </div>

        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: "#0ea5e9" }}>
            {formatPrice(totalFare)}
          </div>
          <div
            style={{
              fontSize: 10,
              color: soldOut ? "#ef4444" : "#10b981",
              fontWeight: 600,
            }}
          >
            {flight?.available_seats ?? 0} seats
          </div>
        </div>

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
            borderRadius: 7,
            padding: "6px 12px",
            fontSize: 11,
            fontWeight: 600,
            cursor: disabled || soldOut ? "not-allowed" : "pointer",
          }}
        >
          {soldOut ? "Sold Out" : "Select"}
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// FLIGHT RESULTS BLOCK
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
      <div style={{ padding: "8px 0", color: "#64748b", fontStyle: "italic", fontSize: 12 }}>
        No flights found for the given criteria.
      </div>
    );
  }

  return (
    <div style={{ marginTop: 6 }}>
      {params && (
        <div
          style={{
            fontSize: 11,
            color: "#64748b",
            marginBottom: 8,
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
          }}
        >
          {params.origin && (
            <span>{"\uD83D\uDEEB"} {params.origin} {"\u2192"} {params.destination}</span>
          )}
          {params.date && <span>{"\uD83D\uDCC5"} {formatDate(params.date)}</span>}
          {params.total_seats && <span>{"\uD83D\uDC64"} {params.total_seats} pax</span>}
        </div>
      )}
      {data.recommendation_reason && (
        <div style={{ fontSize: 11, color: "#475569", marginBottom: 8 }}>
          <strong>Tip:</strong> {data.recommendation_reason}
        </div>
      )}
      {flights.map((flight: any, index: number) => (
        <FlightResultCard
          key={flight?.flight_id ?? `${flight?.airline}-${index}`}
          flight={flight}
          isRecommended={Boolean(
            recommended?.flight_id && flight?.flight_id === recommended.flight_id
          )}
          onSelect={onSelect}
          disabled={disabled}
        />
      ))}
    </div>
  );
}

// ============================================================================
// SELECTED FLIGHT BLOCK
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
    flight?.fare?.total_fare ?? flight?.fare?.total_price ?? flight?.price ?? 0;
  const seats = selectedFlight.numberOfSeats;
  const totalPrice = Number(price) * seats;
  const availableSeats = Number(flight?.available_seats ?? 0);

  return (
    <div
      style={{
        margin: "0 12px 8px",
        background: "#ffffff",
        border: "2px solid #0ea5e9",
        borderRadius: 12,
        padding: 12,
        boxShadow: "0 4px 16px rgba(14,165,233,0.15)",
        flexShrink: 0,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 700, color: "#0f172a", marginBottom: 8 }}>
        {"\u2708"} Selected Flight
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: 6,
          fontSize: 11,
          color: "#475569",
          marginBottom: 10,
        }}
      >
        <div>
          Airline <strong style={{ display: "block", color: "#0f172a" }}>{flight?.airline || "N/A"}</strong>
        </div>
        <div>
          Flight <strong style={{ display: "block", color: "#0f172a" }}>{flight?.flight_id || "N/A"}</strong>
        </div>
        <div>
          Route{" "}
          <strong style={{ display: "block", color: "#0f172a" }}>
            {flight?.origin} {"\u2192"} {flight?.destination}
          </strong>
        </div>
        <div>
          Date <strong style={{ display: "block", color: "#0f172a" }}>{formatDate(flight?.date)}</strong>
        </div>
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          flexWrap: "wrap",
          marginBottom: 10,
        }}
      >
        <label style={{ fontSize: 11, fontWeight: 600, color: "#334155" }}>Seats:</label>
        <select
          value={seats}
          onChange={(e) => onSeatsChange(Number(e.target.value))}
          disabled={disabled}
          style={{
            border: "1px solid #cbd5e1",
            borderRadius: 6,
            padding: "4px 8px",
            fontSize: 12,
          }}
        >
          {Array.from({ length: Math.min(availableSeats, 9) }, (_, i) => i + 1).map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
        <div style={{ marginLeft: "auto", fontSize: 14, fontWeight: 800, color: "#0ea5e9" }}>
          {formatPrice(totalPrice)}
        </div>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button
          type="button"
          onClick={onCancel}
          disabled={disabled}
          style={{
            flex: 1,
            background: "#f1f5f9",
            color: "#475569",
            border: "1px solid #cbd5e1",
            borderRadius: 8,
            padding: "8px 10px",
            fontSize: 12,
            fontWeight: 600,
            cursor: disabled ? "not-allowed" : "pointer",
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
            background: disabled ? "#94a3b8" : "linear-gradient(135deg,#10b981,#059669)",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "8px 10px",
            fontSize: 12,
            fontWeight: 700,
            cursor: disabled ? "not-allowed" : "pointer",
          }}
        >
          {disabled ? "Booking..." : "\u2713 Confirm & Book"}
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// BOOKING SUCCESS BLOCK
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
  const bookingId = Number(data?.booking_id);
  return (
    <div
      style={{
        background: "linear-gradient(135deg,rgba(16,185,129,0.08),rgba(14,165,233,0.08))",
        border: "1.5px solid #10b981",
        borderRadius: 10,
        padding: "12px 14px",
        marginTop: 6,
      }}
    >
      <div style={{ fontWeight: 700, fontSize: 13, color: "#064e3b", marginBottom: 8 }}>
        {"\uD83C\uDF89"} Booking Confirmed!
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "5px 10px", fontSize: 11 }}>
        <div>
          <span style={{ color: "#64748b" }}>Ref: </span>
          <strong>{data?.booking_reference || "N/A"}</strong>
        </div>
        <div>
          <span style={{ color: "#64748b" }}>Flight: </span>
          <strong>{data?.flight_id || "N/A"}</strong>
        </div>
        <div>
          <span style={{ color: "#64748b" }}>Seats: </span>
          <strong>{data?.number_of_seats ?? 1}</strong>
        </div>
        <div>
          <span style={{ color: "#64748b" }}>Total: </span>
          <strong style={{ color: "#0ea5e9" }}>{formatPrice(data?.total_price)}</strong>
        </div>
      </div>
      {bookingId > 0 && (
        <button
          type="button"
          disabled={downloadingId === bookingId}
          onClick={() => onDownload(bookingId)}
          style={{
            marginTop: 10,
            background:
              downloadingId === bookingId
                ? "#94a3b8"
                : "linear-gradient(135deg,#0ea5e9,#0284c7)",
            color: "#fff",
            border: "none",
            borderRadius: 7,
            padding: "7px 14px",
            fontSize: 11,
            fontWeight: 600,
            cursor: downloadingId === bookingId ? "not-allowed" : "pointer",
          }}
        >
          {downloadingId === bookingId ? "Preparing PDF..." : "\uD83D\uDCC4 Download Ticket"}
        </button>
      )}
    </div>
  );
}

// ============================================================================
// BOOKING SUMMARY BLOCK
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
  const bookings: any[] = Array.isArray(data?.bookings)
    ? data.bookings
    : data?.booking_id || data?.id
    ? [data]
    : [];

  if (!bookings.length) return null;

  return (
    <div style={{ marginTop: 6 }}>
      {bookings.map((booking, index) => {
        const bookingId = Number(booking?.booking_id ?? booking?.id);
        const status = booking?.status || "UNKNOWN";
        const isConfirmed = status.toUpperCase() === "CONFIRMED";
        const isCancelled = status.toUpperCase() === "CANCELLED";
        return (
          <div
            key={bookingId > 0 ? bookingId : `booking-${index}`}
            style={{
              background: "rgba(255,255,255,0.95)",
              border: "1px solid #e2e8f0",
              borderRadius: 8,
              padding: "10px 12px",
              marginBottom: 6,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 6,
              }}
            >
              <span style={{ fontWeight: 700, fontSize: 12 }}>
                {booking?.booking_reference || `#${bookingId}`}
              </span>
              <span
                style={{
                  padding: "2px 8px",
                  borderRadius: 999,
                  fontSize: 10,
                  fontWeight: 700,
                  background: isConfirmed ? "#d1fae5" : isCancelled ? "#fee2e2" : "#fef3c7",
                  color: isConfirmed ? "#065f46" : isCancelled ? "#991b1b" : "#92400e",
                }}
              >
                {status}
              </span>
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: "3px 8px",
                fontSize: 10,
                color: "#475569",
              }}
            >
              <div>
                Flight <strong style={{ display: "block" }}>{booking?.flight_id || "N/A"}</strong>
              </div>
              <div>
                Seats <strong style={{ display: "block" }}>{booking?.number_of_seats ?? "N/A"}</strong>
              </div>
              <div>
                Total{" "}
                <strong style={{ display: "block", color: "#0ea5e9" }}>
                  {formatPrice(booking?.total_price)}
                </strong>
              </div>
            </div>
            {bookingId > 0 && isConfirmed && (
              <button
                type="button"
                disabled={downloadingId === bookingId}
                onClick={() => onDownload(bookingId)}
                style={{
                  marginTop: 8,
                  background:
                    downloadingId === bookingId
                      ? "#94a3b8"
                      : "linear-gradient(135deg,#0ea5e9,#0284c7)",
                  color: "#fff",
                  border: "none",
                  borderRadius: 6,
                  padding: "5px 12px",
                  fontSize: 10,
                  fontWeight: 600,
                  cursor: downloadingId === bookingId ? "not-allowed" : "pointer",
                }}
              >
                {downloadingId === bookingId ? "Preparing..." : "\uD83D\uDCC4 Download Ticket"}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ============================================================================
// TICKET BLOCK
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
  const bookingId = Number(data?.booking_id);
  return (
    <div
      style={{
        background: "linear-gradient(135deg,rgba(99,102,241,0.08),rgba(14,165,233,0.08))",
        border: "1.5px solid #6366f1",
        borderRadius: 10,
        padding: "12px 14px",
        marginTop: 6,
      }}
    >
      <div style={{ fontWeight: 700, color: "#312e81", marginBottom: 6, fontSize: 13 }}>
        {"\uD83C\uDFAB"} {data?.booking_reference || `Booking #${bookingId}`}
      </div>
      <div style={{ fontSize: 11, color: "#64748b", marginBottom: 8 }}>
        Flight: <strong>{data?.flight_id || "N/A"}</strong>
      </div>
      {bookingId > 0 && (
        <button
          type="button"
          disabled={downloadingId === bookingId}
          onClick={() => onDownload(bookingId)}
          style={{
            background:
              downloadingId === bookingId
                ? "#94a3b8"
                : "linear-gradient(135deg,#6366f1,#4f46e5)",
            color: "#fff",
            border: "none",
            borderRadius: 7,
            padding: "7px 14px",
            fontSize: 11,
            fontWeight: 700,
            cursor: downloadingId === bookingId ? "not-allowed" : "pointer",
          }}
        >
          {downloadingId === bookingId ? "Preparing PDF..." : "\uD83D\uDCE5 Download Ticket PDF"}
        </button>
      )}
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
  const isUser = message.role === "user";

  const formatMessage = (text: string) => {
    if (!text) return "";
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br />");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: isUser ? "row-reverse" : "row",
        alignItems: "flex-start",
        gap: 8,
        marginBottom: 12,
      }}
    >
      {!isUser && (
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            background: "linear-gradient(135deg,#0ea5e9,#6366f1)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            color: "#fff",
            fontSize: 12,
          }}
        >
          {"\u2708"}
        </div>
      )}

      <div style={{ maxWidth: "82%", minWidth: 50 }}>
        <div
          style={{
            background: isUser
              ? "linear-gradient(135deg,#0ea5e9,#0284c7)"
              : message.type === "error"
              ? "rgba(239,68,68,0.06)"
              : "rgba(255,255,255,0.95)",
            color: isUser ? "#fff" : "#0f172a",
            borderRadius: isUser ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
            padding: "8px 11px",
            fontSize: 13,
            lineHeight: 1.55,
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
                __html: formatMessage(message.content),
              }}
            />
          )}
        </div>

        {!isUser && !message.isLoading && (
          <>
            {message.type === "flight_results" && message.data && (
              <FlightResultsBlock
                data={message.data as ChatFlightData}
                onSelect={onFlightSelect}
                disabled={isLoading}
              />
            )}
            {message.type === "booking_success" && message.data && (
              <BookingSuccessBlock
                data={message.data as ChatBookingSuccessData}
                onDownload={onDownload}
                downloadingId={downloadingId}
              />
            )}
            {message.type === "booking_summary" && message.data && (
              <BookingSummaryBlock
                data={message.data}
                onDownload={onDownload}
                downloadingId={downloadingId}
              />
            )}
            {message.type === "ticket" && message.data && (
              <TicketBlock
                data={message.data as ChatTicketData}
                onDownload={onDownload}
                downloadingId={downloadingId}
              />
            )}
          </>
        )}

        <div
          style={{
            fontSize: 9,
            color: isUser ? "rgba(255,255,255,0.6)" : "#94a3b8",
            textAlign: isUser ? "right" : "left",
            marginTop: 3,
          }}
        >
          {message.timestamp.toLocaleTimeString("en-IN", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>

      {isUser && (
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            background: "linear-gradient(135deg,#6366f1,#8b5cf6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            color: "#fff",
            fontSize: 12,
          }}
        >
          {"\uD83D\uDC64"}
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
// FLOATING CHATBOT
// ============================================================================

export default function FloatingChatbot() {
  const { userToken, user, isLoading: authLoading } = useAuth();

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [selectedFlight, setSelectedFlight] = useState<SelectedFlight | null>(null);
  const [hasUnread, setHasUnread] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Welcome message
  useEffect(() => {
    if (authLoading) return;
    setMessages([
      {
        id: createId(),
        role: "assistant",
        content: `Hello${user?.name ? ` ${user.name}` : ""}! \uD83D\uDC4B I'm your AI Flight Assistant.\n\nI can help you:\n\u2022 Search & compare flights\n\u2022 Book seats\n\u2022 View your bookings\n\u2022 Download ticket PDFs\n\nTry: "Find flights from Chennai to Delhi tomorrow for 2 people"`,
        type: "text",
        data: null,
        timestamp: new Date(),
      },
    ]);
  }, [authLoading, user?.name]);

  // Auto scroll
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, selectedFlight, isOpen]);

  // Focus + clear unread on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
      setHasUnread(false);
    }
  }, [isOpen]);

  // Send message
  const handleSend = useCallback(
    async (messageText?: string) => {
      const text = (messageText ?? input).trim();
      if (!text || isLoading || !userToken) return;

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

      setMessages((prev) => [...prev, userMessage, loadingMessage]);
      setIsLoading(true);

      try {
        const response = await sendChatMessage(text, userToken);

        const assistantMessage: Message = {
          id: createId(),
          role: "assistant",
          content: response?.message || "I received your request.",
          type: response?.type || "text",
          data: response?.data ?? null,
          timestamp: new Date(),
        };

        setMessages((prev) => {
          const idx = prev.findIndex((m) => m.id === loadingMessage.id);
          if (idx === -1) return [...prev, assistantMessage];
          const updated = [...prev];
          updated[idx] = assistantMessage;
          return updated;
        });

        if (!isOpen) setHasUnread(true);
      } catch (error: any) {
        const errorDetail = error?.response?.data?.detail;
        const errorMessage =
          typeof errorDetail === "string"
            ? errorDetail
            : error?.message || "Something went wrong. Please try again.";

        setMessages((prev) => {
          const idx = prev.findIndex((m) => m.id === loadingMessage.id);
          const errorObj: Message = {
            id: createId(),
            role: "assistant",
            content: `I'm sorry, I encountered an error: ${errorMessage}`,
            type: "error",
            data: null,
            timestamp: new Date(),
          };
          if (idx === -1) return [...prev, errorObj];
          const updated = [...prev];
          updated[idx] = errorObj;
          return updated;
        });

        if (!isOpen) setHasUnread(true);
      } finally {
        setIsLoading(false);
        setTimeout(() => inputRef.current?.focus(), 0);
      }
    },
    [input, isLoading, userToken, isOpen]
  );

  const handleFlightSelect = useCallback((flight: any) => {
    if (!flight) return;
    const availableSeats = Number(flight?.available_seats ?? 0);
    if (availableSeats <= 0) return;
    setSelectedFlight({ flight, numberOfSeats: 1 });
  }, []);

  const handleSeatsChange = useCallback(
    (numberOfSeats: number) => {
      if (!selectedFlight) return;
      const available = Number(selectedFlight.flight?.available_seats ?? 0);
      if (numberOfSeats < 1 || numberOfSeats > available) return;
      setSelectedFlight({ ...selectedFlight, numberOfSeats });
    },
    [selectedFlight]
  );

  const handleConfirmBooking = useCallback(() => {
    if (!selectedFlight || !userToken) return;
    const flight = selectedFlight.flight;
    const seats = selectedFlight.numberOfSeats;
    const bookingMessage = `Book flight ${flight?.flight_id} for ${seats} seat${seats !== 1 ? "s" : ""}`;
    setSelectedFlight(null);
    handleSend(bookingMessage);
  }, [selectedFlight, userToken, handleSend]);

  const handleCancelSelection = useCallback(() => {
    setSelectedFlight(null);
  }, []);

  const handleDownload = useCallback(
    async (bookingId: number) => {
      if (!userToken || !bookingId || downloadingId !== null) return;
      setDownloadingId(bookingId);
      try {
        const blob = await downloadTicketPdfApi(bookingId, userToken);
        if (!(blob instanceof Blob)) throw new Error("Invalid PDF response");
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `ticket_${bookingId}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Ticket download error:", error);
        setMessages((prev) => [
          ...prev,
          {
            id: createId(),
            role: "assistant",
            content: "Sorry, I could not generate the ticket PDF. Please try again.",
            type: "error",
            data: null,
            timestamp: new Date(),
          },
        ]);
      } finally {
        setDownloadingId(null);
      }
    },
    [userToken, downloadingId]
  );

  const handleClearHistory = useCallback(async () => {
    if (!userToken) return;
    try {
      await clearChatHistory(userToken);
    } catch (error) {
      console.warn("Could not clear server chat history:", error);
    }
    setSelectedFlight(null);
    setMessages([
      {
        id: createId(),
        role: "assistant",
        content: "Conversation cleared. How can I help you?",
        type: "text",
        data: null,
        timestamp: new Date(),
      },
    ]);
    setInput("");
  }, [userToken]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Only render for logged-in users
  if (authLoading || !userToken) return null;

  return (
    <>
      {/* ── GLOBAL STYLES ─────────────────────────────────────────────── */}
      <style>{`
        @keyframes fcb-spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes fcb-dot {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
          30%            { transform: translateY(-4px); opacity: 1; }
        }
        .fcb-dot-bounce {
          animation: fcb-dot 1.2s infinite ease-in-out;
        }
        @keyframes fcb-popup-in {
          from { opacity: 0; transform: scale(0.88) translateY(20px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }
        @keyframes fcb-btn-pulse {
          0%, 100% { box-shadow: 0 6px 24px rgba(14,165,233,0.45); }
          50%       { box-shadow: 0 6px 24px rgba(14,165,233,0.45), 0 0 0 10px rgba(14,165,233,0.12); }
        }
        .fcb-fab {
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .fcb-fab:hover {
          transform: scale(1.1) !important;
          box-shadow: 0 10px 36px rgba(14,165,233,0.6) !important;
        }
        .fcb-popup {
          animation: fcb-popup-in 0.24s cubic-bezier(0.34,1.56,0.64,1) forwards;
        }
        .fcb-send-btn:hover:not(:disabled) {
          transform: scale(1.08);
          filter: brightness(1.1);
        }
        .fcb-send-btn {
          transition: transform 0.15s, filter 0.15s;
        }
        .fcb-suggestion:hover {
          border-color: #0ea5e9 !important;
          color: #0284c7 !important;
          background: #f0f9ff !important;
        }
        .fcb-suggestion {
          transition: border-color 0.15s, color 0.15s, background 0.15s;
        }

        @media (max-width: 480px) {
          .fcb-window {
            width: calc(100vw - 24px) !important;
            right: 12px !important;
            bottom: 80px !important;
            height: calc(100vh - 110px) !important;
          }
        }
        @media (min-width: 481px) and (max-width: 768px) {
          .fcb-window {
            width: 320px !important;
          }
        }

        #fcb-messages::-webkit-scrollbar { width: 4px; }
        #fcb-messages::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
      `}</style>

      {/* ── FLOATING ACTION BUTTON ──────────────────────────────────────── */}
      <button
        id="fcb-toggle-btn"
        type="button"
        aria-label={isOpen ? "Close AI Assistant" : "Open AI Assistant"}
        className="fcb-fab"
        onClick={() => setIsOpen((prev) => !prev)}
        style={{
          position: "fixed",
          bottom: 24,
          right: 24,
          width: 58,
          height: 58,
          borderRadius: "50%",
          background: "linear-gradient(135deg,#0ea5e9,#6366f1)",
          border: "none",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 10000,
          boxShadow: "0 6px 24px rgba(14,165,233,0.45)",
          color: "#fff",
          animation: !isOpen ? "fcb-btn-pulse 2.6s ease-in-out infinite" : undefined,
        }}
      >
        {isOpen ? (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            <circle cx="9" cy="10" r="1" fill="currentColor" />
            <circle cx="12" cy="10" r="1" fill="currentColor" />
            <circle cx="15" cy="10" r="1" fill="currentColor" />
          </svg>
        )}

        {/* Unread dot */}
        {hasUnread && !isOpen && (
          <span
            style={{
              position: "absolute",
              top: 5,
              right: 5,
              width: 11,
              height: 11,
              borderRadius: "50%",
              background: "#ef4444",
              border: "2px solid #fff",
            }}
          />
        )}
      </button>

      {/* ── CHAT POPUP ───────────────────────────────────────────────────── */}
      {isOpen && (
        <div
          id="fcb-popup"
          className="fcb-popup fcb-window"
          role="dialog"
          aria-label="AI Flight Assistant"
          style={{
            position: "fixed",
            bottom: 94,
            right: 24,
            width: 390,
            height: 570,
            borderRadius: 20,
            background: "#f1f5f9",
            boxShadow:
              "0 24px 64px rgba(15,23,42,0.2), 0 8px 24px rgba(14,165,233,0.14)",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            zIndex: 9999,
            border: "1px solid rgba(226,232,240,0.7)",
          }}
        >
          {/* ── HEADER ─────────────────────────────────────────────────── */}
          <div
            style={{
              background: "linear-gradient(135deg,#0f172a 0%,#1e1b4b 100%)",
              padding: "14px 16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexShrink: 0,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: "50%",
                  background: "linear-gradient(135deg,#0ea5e9,#6366f1)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 18,
                  color: "#fff",
                  flexShrink: 0,
                }}
              >
                {"\u2708"}
              </div>
              <div>
                <div style={{ color: "#fff", fontWeight: 700, fontSize: 14 }}>
                  AI Flight Assistant
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 5, marginTop: 2 }}>
                  <span
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: "50%",
                      background: "#4ade80",
                      display: "inline-block",
                    }}
                  />
                  <span style={{ color: "rgba(255,255,255,0.5)", fontSize: 11 }}>
                    Online &middot; Always ready
                  </span>
                </div>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <button
                type="button"
                title="Clear conversation"
                onClick={handleClearHistory}
                style={{
                  background: "rgba(255,255,255,0.08)",
                  border: "1px solid rgba(255,255,255,0.15)",
                  borderRadius: 7,
                  color: "rgba(255,255,255,0.6)",
                  padding: "5px 10px",
                  fontSize: 11,
                  cursor: "pointer",
                }}
              >
                {"\uD83D\uDDD1"}
              </button>
              <button
                type="button"
                title="Close"
                onClick={() => setIsOpen(false)}
                style={{
                  background: "rgba(255,255,255,0.08)",
                  border: "1px solid rgba(255,255,255,0.15)",
                  borderRadius: 7,
                  color: "rgba(255,255,255,0.7)",
                  padding: "5px 8px",
                  fontSize: 14,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </div>

          {/* ── MESSAGES ───────────────────────────────────────────────── */}
          <div
            id="fcb-messages"
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "14px 12px",
              display: "flex",
              flexDirection: "column",
              background: "linear-gradient(180deg,rgba(248,250,252,0.98),rgba(241,245,249,0.98))",
            }}
          >
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onFlightSelect={handleFlightSelect}
                onDownload={handleDownload}
                downloadingId={downloadingId}
                isLoading={isLoading}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* ── SELECTED FLIGHT ─────────────────────────────────────────── */}
          {selectedFlight && (
            <SelectedFlightBlock
              selectedFlight={selectedFlight}
              onSeatsChange={handleSeatsChange}
              onConfirm={handleConfirmBooking}
              onCancel={handleCancelSelection}
              disabled={isLoading}
            />
          )}

          {/* ── QUICK SUGGESTIONS ──────────────────────────────────────── */}
          {messages.length <= 1 && !selectedFlight && (
            <div
              style={{
                background: "rgba(248,250,252,0.97)",
                padding: "8px 12px",
                display: "flex",
                gap: 5,
                flexWrap: "wrap",
                borderTop: "1px solid #e2e8f0",
                flexShrink: 0,
              }}
            >
              {QUICK_SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="fcb-suggestion"
                  disabled={isLoading}
                  onClick={() => handleSend(suggestion)}
                  style={{
                    background: "white",
                    border: "1px solid #e2e8f0",
                    borderRadius: 14,
                    padding: "4px 10px",
                    fontSize: 10,
                    color: "#475569",
                    cursor: isLoading ? "not-allowed" : "pointer",
                    whiteSpace: "nowrap",
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          {/* ── INPUT ──────────────────────────────────────────────────── */}
          <div
            style={{
              background: "rgba(255,255,255,0.98)",
              borderTop: "1px solid #e2e8f0",
              padding: "10px 12px",
              display: "flex",
              gap: 8,
              alignItems: "center",
              flexShrink: 0,
            }}
          >
            <input
              ref={inputRef}
              id="fcb-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about flights, bookings\u2026"
              disabled={isLoading}
              style={{
                flex: 1,
                border: "1.5px solid #e2e8f0",
                borderRadius: 12,
                padding: "9px 13px",
                fontSize: 13,
                fontFamily: "inherit",
                color: "#0f172a",
                background: "white",
                outline: "none",
                transition: "border-color 0.15s",
              }}
              onFocus={(e) => (e.currentTarget.style.borderColor = "#0ea5e9")}
              onBlur={(e) => (e.currentTarget.style.borderColor = "#e2e8f0")}
            />

            <button
              id="fcb-send-btn"
              type="button"
              className="fcb-send-btn"
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              style={{
                background:
                  isLoading || !input.trim()
                    ? "#e2e8f0"
                    : "linear-gradient(135deg,#0ea5e9,#0284c7)",
                color: isLoading || !input.trim() ? "#94a3b8" : "#fff",
                border: "none",
                borderRadius: 12,
                width: 42,
                height: 42,
                cursor: isLoading || !input.trim() ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              {isLoading ? (
                <div
                  style={{
                    width: 16,
                    height: 16,
                    border: "2px solid #94a3b8",
                    borderTop: "2px solid #475569",
                    borderRadius: "50%",
                    animation: "fcb-spin 0.8s linear infinite",
                  }}
                />
              ) : (
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
