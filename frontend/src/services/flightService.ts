import type { Flight } from "../types";
import { searchFlights } from './api';

export async function searchFlightsService(message: string): Promise<SearchResponse> {
  return searchFlights(message);
}

export function getRecommendedFlight(response: SearchResponse): Flight | null {
  if (!response.recommended_flight || !response.flights.length) return null;
  return response.flights.find(
    (f) => f.flight_id === response.recommended_flight!.flight_id
  ) ?? null;
}

export function getOtherFlights(response: SearchResponse): Flight[] {
  if (!response.recommended_flight) return response.flights;
  return response.flights.filter(
    (f) => f.flight_id !== response.recommended_flight!.flight_id
  );
}

export function formatTime(time: string): string {
  // Converts "06:30:00" → "06:30"
  return time.slice(0, 5);
}

export function formatDate(dateStr: string): string {
  // "2026-08-20" → "20 Aug 2026"
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
  }).format(amount);
}
