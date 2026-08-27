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

// ── Payment Types ─────────────────────────────────────────────────────────────

export interface CreatePaymentRequest {
  booking_id: number;
  payment_method?: string;
  currency?: string;
}

export interface PaymentResponse {
  success: boolean;

  payment_id: string;
  booking_id: number;
  booking_reference?: string | null;

  user_id?: number;

  amount: number;
  currency: string;

  status:
  | "PENDING"
  | "PROCESSING"
  | "SUCCESS"
  | "FAILED"
  | "REFUNDED";

  payment_status?: string | null;

  payment_method?: string | null;

  transaction_id?: string | null;
  failure_reason?: string | null;
  refund_id?: string | null;

  booking_status?: string | null;
  booking_payment_status?: string | null;
  booking_payment_id?: string | null;

  paid_at?: string | null;

  ticket_status?: "NOT_AVAILABLE" | "AVAILABLE" | string;
  ticket_download_allowed?: boolean;

  created_at?: string | null;
  updated_at?: string | null;

  payment_exists?: boolean;

  error?: string;
  message?: string;
}

export interface ProcessPaymentRequest {
  payment_method: string;
}

export interface RefundPaymentRequest {
  reason: string;
}


