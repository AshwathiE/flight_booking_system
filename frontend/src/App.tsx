import React from "react";
import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";

import Header from "./components/Header";

import Home from "./pages/Home";
import SearchResults from "./pages/SearchResults";
import Booking from "./pages/Booking";
import About from "./pages/About";

import Login from "./pages/Login";
import Register from "./pages/Register";

import AdminLogin from "./pages/AdminLogin";
import AdminDashboard from "./pages/AdminDashboard";

import {
  ProtectedRoute,
  AdminProtectedRoute,
} from "./components/ProtectedRoute";

// Dashboard
import DashboardLayout from "./components/DashboardLayout";
import DashboardHome from "./pages/DashboardHome";
import MyBookings from "./pages/MyBookings";
import Profile from "./pages/Profile";
import BookingDetails from "./pages/BookingDetails";
import ViewTicket from "./pages/ViewTicket";

// AI
import AIAssistant from "./pages/AIAssistant";
import FloatingChatbot from "./components/FloatingChatbot";

// Payment
import Payment from "./pages/Payment";


export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>

        <Header />

        {/* Floating AI chatbot - visible on every page for logged-in users */}
        <FloatingChatbot />

        <main>
          <Routes>

            {/* ================= USER PUBLIC ROUTES ================= */}

            <Route
              path="/"
              element={<Home />}
            />

            <Route
              path="/home"
              element={<Home />}
            />

            <Route
              path="/results"
              element={<SearchResults />}
            />

            <Route
              path="/search"
              element={<SearchResults />}
            />

            <Route
              path="/booking"
              element={<Booking />}
            />

            <Route
              path="/payment"
              element={
                <ProtectedRoute>
                  <Payment />
                </ProtectedRoute>
              }
            />

            <Route
              path="/payment/:paymentId"
              element={
                <ProtectedRoute>
                  <Payment />
                </ProtectedRoute>
              }
            />

            <Route
              path="/about"
              element={<About />}
            />

            <Route
              path="/login"
              element={<Login />}
            />

            <Route
              path="/register"
              element={<Register />}
            />


            {/* ================= ADMIN ================= */}

            <Route
              path="/admin/login"
              element={<AdminLogin />}
            />

            <Route
              path="/admin/dashboard"
              element={
                <AdminProtectedRoute>
                  <AdminDashboard />
                </AdminProtectedRoute>
              }
            />


            {/* ================= USER DASHBOARD ================= */}

            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <DashboardHome />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/my-bookings"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <MyBookings />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Profile />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/booking/:bookingId"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <BookingDetails />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/ticket/:bookingId"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <ViewTicket />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />


            {/* ================= AI ASSISTANT ================= */}

            <Route
              path="/ai-assistant"
              element={
                <ProtectedRoute>
                  <AIAssistant />
                </ProtectedRoute>
              }
            />


            {/* ================= FALLBACK ================= */}

            <Route
              path="*"
              element={<Home />}
            />

          </Routes>
        </main>

      </AuthProvider>
    </BrowserRouter>
  );
}