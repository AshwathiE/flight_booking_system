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