export interface FlightSearchRequest {
  origin: string;
  destination: string;
  date: string;
  total_seats: number;
  travel_class: string | null;
  max_price: number | null;
  preference: string;
}

export interface Fare {
  flight_id: string;
  total_seats: number;
  travel_class: string;
  base_fare: number;
  tax: number;
  service_fee: number;
  total_fare: number;
}

export interface Flight {
  flight_id: string;
  airline: string;
  origin: string;
  destination: string;
  date: string;
  departure_time: string;
  arrival_time: string;
  price: number;
  travel_class: string;
  available_seats: number;
  requested_seats: number;
  availability: string;
  fare: Fare;
}

export interface SearchResponse {
  user_request: string;
  search_parameters: FlightSearchRequest;
  flights: Flight[];
  recommended_flight?: Flight;
  recommendation_reason?: string;
  message: string;
}

export interface SearchParameters {
  origin: string;
  destination: string;
  date: string;
  passengers?: number;
}