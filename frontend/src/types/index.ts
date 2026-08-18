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
  user_request?: string;

  status:
  | "success"
  | "needs_information"
  | "validation_error"
  | "no_results"
  | "no_availability"
  | "error";

  search_parameters?: FlightSearchRequest;

  flights?: Flight[];

  recommended_flight?: Flight | null;

  recommendation_reason?: string | null;

  message: string;

  missing_fields?: string[];

  field?: string;
}

export interface Booking {
  booking_id: number;
  booking_reference: string;
  user_id: number;
  flight_id: string;
  number_of_seats: number;
  total_price: number;
  status: string;
  created_at: string;
  flight?: Flight;
}

export interface BookingRequest {
  flight_id: string;
  number_of_seats: number;
}

export interface BookingResponse {
  success: boolean;
  booking_id: number;
  booking_reference: string;
  user_id: number;
  flight_id: string;
  number_of_seats: number;
  total_price: number;
  status: string;
  created_at: string;
  error?: string;
  message?: string;
}