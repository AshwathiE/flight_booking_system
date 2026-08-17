import axios from "axios";
import type { SearchResponse, BookingRequest, BookingResponse } from "../types";

const API_URL = "http://127.0.0.1:8000";

export interface UserProfile {
  id: number;
  name: string;
  email: string;
  created_at: string;
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

// User Auth APIs
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

// Admin Auth APIs
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

// Flight Search API
export async function searchFlights(
  message: string
): Promise<SearchResponse> {
  const response = await axios.post<SearchResponse>(
    `${API_URL}/ai/search_flights`,
    { message }
  );

  return response.data;
}

// Booking API
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

// Admin Bookings
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

// ── Admin Flight Management ───────────────────────────────────────────────────

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
 * Returns an ImportSummary with per-row error details.
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
 * Upload an Excel file (.xlsx / .xls) to the admin bulk-import endpoint.
 * Returns an ImportSummary with per-row error details.
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
 * Manually create a single flight via the admin endpoint.
 */
export async function adminCreateFlightApi(
  data: ManualFlightData,
  token: string
): Promise<{ success: boolean; message: string; flight_id: string }> {
  const response = await axios.post<{ success: boolean; message: string; flight_id: string }>(
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