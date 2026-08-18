import axios from "axios";
import type {
  SearchResponse,
  BookingRequest,
  BookingResponse,
} from "../types";

const API_URL = "http://127.0.0.1:8000";

// ── User / Admin Interfaces ──────────────────────────────────────────────────

export interface UserProfile {
  id: number;
  name: string;
  email: string;
  mobile_number?: string;
  created_at: string;
  role: string;
  status: string;
}

export interface AdminProfile {
  id: number;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_type: "user" | "admin";
  user?: UserProfile;
  admin?: AdminProfile;
}

export interface AdminStats {
  total_users: number;
  total_admins: number;
  total_flights: number;
  system_status: string;
  mcp_server: string;
}

// ── User Auth APIs ────────────────────────────────────────────────────────────

export async function registerUserApi(
  data: {
    name: string;
    email: string;
    password: string;
  }
): Promise<AuthResponse> {
  const response = await axios.post<AuthResponse>(
    `${API_URL}/auth/register`,
    data
  );

  return response.data;
}

export async function loginUserApi(
  data: {
    email: string;
    password: string;
  }
): Promise<AuthResponse> {
  const response = await axios.post<AuthResponse>(
    `${API_URL}/auth/login`,
    data
  );

  return response.data;
}

export async function getUserMeApi(
  token: string
): Promise<UserProfile> {
  const response = await axios.get<UserProfile>(
    `${API_URL}/auth/me`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

// ── Admin Auth APIs ───────────────────────────────────────────────────────────

export async function loginAdminApi(
  data: {
    email: string;
    password: string;
  }
): Promise<AuthResponse> {
  const response = await axios.post<AuthResponse>(
    `${API_URL}/admin/login`,
    data
  );

  return response.data;
}

export async function getAdminMeApi(
  token: string
): Promise<AdminProfile> {
  const response = await axios.get<AdminProfile>(
    `${API_URL}/admin/me`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

export async function getAdminStatsApi(
  token: string
): Promise<AdminStats> {
  const response = await axios.get<AdminStats>(
    `${API_URL}/admin/dashboard-stats`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

// ── Flight Search API ────────────────────────────────────────────────────────

export async function searchFlights(
  message: string
): Promise<SearchResponse> {
  const response = await axios.post<SearchResponse>(
    `${API_URL}/ai/search_flights`,
    { message }
  );

  return response.data;
}

// ── Availability API ──────────────────────────────────────────────────────────

export interface AvailabilityResponse {
  flight_id: string;
  requested_seats: number;
  available_seats: number;
  available: boolean;
  error?: string;
}

export async function checkAvailabilityApi(
  flightId: string,
  totalSeats: number
): Promise<AvailabilityResponse> {
  const response = await axios.get<AvailabilityResponse>(
    `${API_URL}/flights/${flightId}/availability`,
    {
      params: {
        total_seats: totalSeats,
      },
    }
  );

  return response.data;
}

// ── Booking API ───────────────────────────────────────────────────────────────

export async function createBookingApi(
  data: BookingRequest,
  token: string
): Promise<BookingResponse> {
  const response = await axios.post<BookingResponse>(
    `${API_URL}/bookings`,
    data,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

// ── Admin Bookings ────────────────────────────────────────────────────────────

export interface BookingRecord {
  booking_id: number;
  booking_reference: string;
  user_id: number;
  flight_id: string;
  number_of_seats: number;
  total_price: number;
  status: string;
  created_at: string;
}

export interface AllBookingsResponse {
  success: boolean;
  bookings: BookingRecord[];
}

export async function getAllBookingsApi(
  token: string
): Promise<AllBookingsResponse> {
  const response = await axios.get<AllBookingsResponse>(
    `${API_URL}/admin/bookings`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

// ── Admin Flight Management ──────────────────────────────────────────────────

export interface ImportRowError {
  row: number;
  errors: string[];
}

export interface ImportSummary {
  total_rows: number;
  imported: number;
  failed: number;
  errors: ImportRowError[];
}

export interface ManualFlightData {
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
  total_seats?: number;
}

/**
 * Upload a CSV file to the admin bulk-import endpoint.
 */
export async function adminUploadCsvApi(
  file: File,
  token: string
): Promise<ImportSummary> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await axios.post<ImportSummary>(
    `${API_URL}/admin/flights/upload/csv`,
    formData,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

/**
 * Upload an Excel file (.xlsx / .xls).
 */
export async function adminUploadExcelApi(
  file: File,
  token: string
): Promise<ImportSummary> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await axios.post<ImportSummary>(
    `${API_URL}/admin/flights/upload/excel`,
    formData,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}

/**
 * Manually create a single flight.
 */
export async function adminCreateFlightApi(
  data: ManualFlightData,
  token: string
): Promise<{
  success: boolean;
  message: string;
  flight_id: string;
}> {
  const response = await axios.post<{
    success: boolean;
    message: string;
    flight_id: string;
  }>(
    `${API_URL}/admin/flights`,
    data,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

// ── Admin User Management ─────────────────────────────────────────────────────

/**
 * Get all registered users.
 */
export async function getAdminUsersApi(
  token: string
): Promise<UserProfile[]> {
  const response = await axios.get<UserProfile[]>(
    `${API_URL}/admin/users`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

/**
 * Get a single user by ID.
 */
export async function getAdminUserApi(
  userId: number,
  token: string
): Promise<UserProfile> {
  const response = await axios.get<UserProfile>(
    `${API_URL}/admin/users/${userId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

// ── Admin User Booking Management ────────────────────────────────────────────

export interface UserBookingRecord {
  booking_id: number;
  booking_reference: string;
  user_id: number;
  flight_id: string;
  number_of_seats: number;
  total_price: number;
  status: string;
  created_at: string;
}

export interface UserBookingsResponse {
  success: boolean;
  bookings: UserBookingRecord[];
}

/**
 * Get all bookings belonging to a specific user.
 * Admin only.
 */
export async function getAdminUserBookingsApi(
  userId: number,
  token: string
): Promise<UserBookingsResponse> {
  const response = await axios.get<UserBookingsResponse>(
    `${API_URL}/admin/users/${userId}/bookings`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

/**
 * Update user information.
 */
export async function updateAdminUserApi(
  userId: number,
  data: {
    name: string;
    email: string;
    role: string;
  },
  token: string
): Promise<UserProfile> {
  const response = await axios.put<UserProfile>(
    `${API_URL}/admin/users/${userId}`,
    data,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

/**
 * Activate or deactivate a user.
 */
export async function updateAdminUserStatusApi(
  userId: number,
  status: string,
  token: string
): Promise<UserProfile> {
  const response = await axios.patch<UserProfile>(
    `${API_URL}/admin/users/${userId}/status`,
    { status },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

/**
 * Delete a user.
 */
export async function deleteAdminUserApi(
  userId: number,
  token: string
): Promise<void> {
  await axios.delete(
    `${API_URL}/admin/users/${userId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
}

// ── Admin Flight Data ─────────────────────────────────────────────────────────

export interface AdminFlightRecord {
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
  total_seats: number | null;
}

export interface AdminFlightsResponse {
  success: boolean;
  flights: AdminFlightRecord[];
}

/**
 * Fetch all flights stored in the database.
 * Admin only.
 */
export async function getAdminFlightsApi(
  token: string
): Promise<AdminFlightsResponse> {
  const response = await axios.get<AdminFlightsResponse>(
    `${API_URL}/admin/flights`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
}

// ── User Dashboard API endpoints ──────────────────────────────────────────────

export async function updateProfileApi(
  data: {
    name: string;
    email: string;
    mobile_number?: string;
    password?: string;
  },
  token: string
): Promise<UserProfile> {
  const response = await axios.put<UserProfile>(
    `${API_URL}/auth/profile`,
    data,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return response.data;
}

export interface MyBookingsResponse {
  success: boolean;
  user_id: number;
  count: number;
  bookings: any[];
}

export async function getMyBookingsApi(
  token: string
): Promise<MyBookingsResponse> {
  const response = await axios.get<MyBookingsResponse>(
    `${API_URL}/bookings/my-bookings`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return response.data;
}

export async function getBookingDetailsApi(
  bookingId: number,
  token: string
): Promise<any> {
  const response = await axios.get<any>(
    `${API_URL}/bookings/${bookingId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return response.data;
}

export async function cancelBookingApi(
  bookingId: number,
  token: string
): Promise<any> {
  const response = await axios.post<any>(
    `${API_URL}/bookings/${bookingId}/cancel`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return response.data;
}

export async function downloadTicketPdfApi(
  bookingId: number,
  token: string
): Promise<Blob> {
  const response = await axios.get(
    `${API_URL}/bookings/${bookingId}/ticket/pdf`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      responseType: "blob",
    }
  );
  return response.data;
}