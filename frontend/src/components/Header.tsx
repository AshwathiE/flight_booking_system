import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Plane,
  Search,
  Info,
  LogIn,
  UserPlus,
  LogOut,
  User,
  ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    user,
    admin,
    logoutUser,
    logoutAdmin,
  } = useAuth();

  const isActive = (path: string) => location.pathname === path;

  // =========================================================
  // LOGOUT MODAL STATE
  // =========================================================

  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [logoutType, setLogoutType] = useState<'user' | 'admin' | null>(null);

  // =========================================================
  // OPEN LOGOUT CONFIRMATION
  // =========================================================

  const handleUserLogout = () => {
    setLogoutType('user');
    setShowLogoutModal(true);
  };

  const handleAdminLogout = () => {
    setLogoutType('admin');
    setShowLogoutModal(true);
  };

  // =========================================================
  // CONFIRM LOGOUT
  // =========================================================

  const confirmLogout = () => {
    if (logoutType === 'user') {
      logoutUser();

      setShowLogoutModal(false);
      setLogoutType(null);

      navigate('/');
      return;
    }

    if (logoutType === 'admin') {
      logoutAdmin();

      setShowLogoutModal(false);
      setLogoutType(null);

      navigate('/admin/login');
      return;
    }
  };

  // =========================================================
  // CANCEL LOGOUT
  // =========================================================

  const cancelLogout = () => {
    setShowLogoutModal(false);
    setLogoutType(null);
  };

  // =========================================================
  // ESC KEY SUPPORT
  // =========================================================

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        cancelLogout();
      }
    };

    if (showLogoutModal) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [showLogoutModal]);

  return (
    <header
      style={{
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: '1px solid #e2e8f0',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        boxShadow: '0 2px 16px rgba(15,23,42,0.06)',
      }}
    >
      {/* =====================================================
          HEADER CONTENT
      ===================================================== */}

      <div
        style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 24px',
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* ===================================================
            LOGO
        =================================================== */}

        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            textDecoration: 'none',
          }}
        >
          <div
            style={{
              width: '36px',
              height: '36px',
              background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Plane size={20} color="white" />
          </div>

          <span
            style={{
              fontWeight: 800,
              fontSize: '18px',
              background: 'linear-gradient(135deg, #0ea5e9, #0284c7)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '-0.3px',
            }}
          >
            AI Flight Booking
          </span>
        </Link>

        {/* ===================================================
            CENTER NAVIGATION
        =================================================== */}

        <nav
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          {[
            {
              to: '/',
              icon: Search,
              label: 'Search Flights',
            },

            ...(user
              ? [
                {
                  to: '/dashboard',
                  icon: User,
                  label: 'Dashboard',
                },
              ]
              : []),

            {
              to: '/about',
              icon: Info,
              label: 'About',
            },
          ].map(({ to, icon: Icon, label }) => (
            <Link
              key={to}
              to={to}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 14px',
                borderRadius: '9px',
                textDecoration: 'none',
                fontSize: '14px',
                fontWeight: isActive(to) ? 600 : 500,
                color: isActive(to) ? '#0284c7' : '#64748b',
                background: isActive(to) ? '#e0f2fe' : 'transparent',
                transition: 'all 0.2s',
                border: 'none',
              }}
            >
              {Icon && <Icon size={15} />}

              <span className="hidden-mobile">
                {label}
              </span>
            </Link>
          ))}

          {/* =================================================
              ADMIN DASHBOARD
          ================================================= */}

          {admin && (
            <Link
              to="/admin/dashboard"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 14px',
                borderRadius: '9px',
                textDecoration: 'none',
                fontSize: '14px',

                fontWeight: isActive('/admin/dashboard')
                  ? 600
                  : 500,

                color: '#4f46e5',

                background: isActive('/admin/dashboard')
                  ? '#e0e7ff'
                  : 'transparent',

                transition: 'all 0.2s',
              }}
            >
              <ShieldCheck size={16} />

              <span className="hidden-mobile">
                Admin Dashboard
              </span>
            </Link>
          )}
        </nav>

        {/* ===================================================
            RIGHT AUTH NAVIGATION
        =================================================== */}

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          {/* =================================================
              LOGGED-IN USER
          ================================================= */}

          {user ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              {/* User Profile */}

              <Link
                to="/dashboard"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  textDecoration: 'none',
                }}
              >
                {/* Avatar */}

                <div
                  style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '50%',
                    background: '#e0f2fe',
                    color: '#0284c7',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '14px',
                  }}
                >
                  {user.name ? (
                    user.name.charAt(0).toUpperCase()
                  ) : (
                    <User size={16} />
                  )}
                </div>

                {/* User Details */}

                <div className="hidden-mobile">
                  <div
                    style={{
                      fontSize: '13px',
                      fontWeight: 700,
                      color: '#0f172a',
                    }}
                  >
                    {user.name}
                  </div>

                  <div
                    style={{
                      fontSize: '11px',
                      color: '#64748b',
                    }}
                  >
                    {user.email}
                  </div>
                </div>
              </Link>

              {/* User Logout */}

              <button
                onClick={handleUserLogout}
                title="Logout"
                type="button"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 12px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  background: '#f8fafc',
                  color: '#475569',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <LogOut size={14} />

                <span className="hidden-mobile">
                  Logout
                </span>
              </button>
            </div>
          ) : admin ? (

            /* =================================================
               LOGGED-IN ADMIN
            ================================================= */

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              {/* Admin Label */}

              <span
                style={{
                  fontSize: '13px',
                  fontWeight: 700,
                  color: '#4f46e5',
                  background: '#e0e7ff',
                  padding: '4px 10px',
                  borderRadius: '6px',
                }}
              >
                Admin: {admin.email}
              </span>

              {/* Admin Logout */}

              <button
                onClick={handleAdminLogout}
                title="Logout"
                type="button"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 12px',
                  borderRadius: '8px',
                  border: '1px solid #ef4444',
                  background: '#fef2f2',
                  color: '#dc2626',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <LogOut size={14} />

                <span>
                  Logout
                </span>
              </button>
            </div>
          ) : (

            /* =================================================
               GUEST USER
            ================================================= */

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              {/* Login */}

              <Link
                to="/login"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 14px',
                  borderRadius: '9px',
                  textDecoration: 'none',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: '#0284c7',
                  background: '#e0f2fe',
                }}
              >
                <LogIn size={15} />

                <span>
                  Login
                </span>
              </Link>

              {/* Register */}

              <Link
                to="/register"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 14px',
                  borderRadius: '9px',
                  textDecoration: 'none',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: 'white',
                  background:
                    'linear-gradient(135deg, #0ea5e9, #0284c7)',
                }}
              >
                <UserPlus size={15} />

                <span>
                  Register
                </span>
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* =====================================================
          LOGOUT CONFIRMATION MODAL
      ===================================================== */}

      {showLogoutModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="logout-modal-title"
          onClick={cancelLogout}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.45)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '20px',
          }}
        >
          {/* Modal */}

          <div
            onClick={(event) => event.stopPropagation()}
            style={{
              width: '100%',
              maxWidth: '400px',
              background: '#ffffff',
              borderRadius: '16px',
              padding: '28px',
              boxShadow: '0 20px 50px rgba(0,0,0,0.2)',
              animation: 'logoutModalFadeIn 0.2s ease-out',
            }}
          >
            {/* Logout Icon */}

            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: '#fef2f2',
                color: '#dc2626',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
              }}
            >
              <LogOut size={22} />
            </div>

            {/* Title */}

            <h2
              id="logout-modal-title"
              style={{
                margin: '0 0 8px',
                fontSize: '20px',
                fontWeight: 700,
                color: '#0f172a',
              }}
            >
              Confirm Logout
            </h2>

            {/* Message */}

            <p
              style={{
                margin: '0 0 24px',
                color: '#64748b',
                fontSize: '14px',
                lineHeight: 1.5,
              }}
            >
              Are you sure you want to logout?
            </p>

            {/* Buttons */}

            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: '10px',
              }}
            >
              {/* Cancel */}

              <button
                type="button"
                onClick={cancelLogout}
                style={{
                  padding: '9px 18px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  background: '#ffffff',
                  color: '#475569',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>

              {/* Confirm Logout */}

              <button
                type="button"
                onClick={confirmLogout}
                style={{
                  padding: '9px 18px',
                  borderRadius: '8px',
                  border: 'none',
                  background: '#dc2626',
                  color: '#ffffff',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================
          RESPONSIVE CSS + MODAL ANIMATION
      ===================================================== */}

      <style>{`
        @media (max-width: 640px) {
          .hidden-mobile {
            display: none;
          }
        }

        @keyframes logoutModalFadeIn {
          from {
            opacity: 0;
            transform: scale(0.95);
          }

          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </header>
  );
}