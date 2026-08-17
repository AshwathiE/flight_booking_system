import type { Flight } from "../types";
import { searchFlights } from "./api";

export interface SearchResponse {
  status:
  | "success"
  | "needs_information"
  | "validation_error"
  | "no_results"
  | "no_availability"
  | "error";

  message: string;

  missing_fields?: string[];

  field?: string;

  flights?: Flight[];

  recommended_flight?: Flight | null;

  recommendation_reason?: string | null;

  search_parameters?: {
    origin: string;
    destination: string;
    date: string;
    total_seats: number;
    travel_class?: string | null;
    max_price?: number | null;
    preference?: string | null;
  };
}


export async function searchFlightsService(
  message: string
): Promise<SearchResponse> {
  return searchFlights(message);
}


export function getRecommendedFlight(
  response: SearchResponse
): Flight | null {

  const flights = response.flights ?? [];

  if (!response.recommended_flight) {
    return null;
  }

  if (flights.length === 0) {
    return null;
  }

  return (
    flights.find(
      (f) =>
        f.flight_id ===
        response.recommended_flight!.flight_id
    ) ?? null
  );
}


export function getOtherFlights(
  response: SearchResponse
): Flight[] {

  const flights = response.flights ?? [];

  if (!response.recommended_flight) {
    return flights;
  }

  return flights.filter(
    (f) =>
      f.flight_id !==
      response.recommended_flight!.flight_id
  );
}


export function formatTime(
  time: string
): string {

  // Converts "06:30:00" → "06:30"

  return time.slice(0, 5);
}


export function formatDate(
  dateStr: string
): string {

  // "2026-08-20" → "20 Aug 2026"

  const d = new Date(dateStr);

  return d.toLocaleDateString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  );
}


export function formatCurrency(
  amount: number
): string {

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
    }
  ).format(amount);
}