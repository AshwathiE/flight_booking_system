import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Plane, Briefcase, User, LogOut } from 'lucide-react';

interface Props {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: Props) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logoutUser } = useAuth();

  const handleLogout = () => {
    logoutUser();
    navigate('/');
  };

  const menuItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/', label: 'Search Flights', icon: Plane },
    { to: '/my-bookings', label: 'My Bookings', icon: Briefcase },
    { to: '/profile', label: 'Profile', icon: User },
  ];

  return (
    <div style={{ display: 'flex', minHeight: 'calc(100vh - 64px)', background: '#f8fafc' }} className="dashboard-container">
      {/* Sidebar */}
      <aside
        style={{
          width: '260px',
          background: 'white',
          borderRight: '1px solid #e2e8f0',
          padding: '24px 16px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
        className="dashboard-sidebar"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ padding: '0 12px 16px 12px', borderBottom: '1px solid #f1f5f9', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '12px', fontWeight: 700, color: '#94a3b8', letterSpacing: '1px', textTransform: 'uppercase' }}>
              User Portal
            </h3>
          </div>

          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  textDecoration: 'none',
                  fontSize: '14px',
                  fontWeight: 600,
                  color: isActive ? '#0284c7' : '#64748b',
                  background: isActive ? '#e0f2fe' : 'transparent',
                  transition: 'all 0.2s',
                }}
                className={`sidebar-link ${isActive ? 'active' : ''}`}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = '#0284c7';
                    e.currentTarget.style.background = '#f0f9ff';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = '#64748b';
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        <button
          onClick={handleLogout}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: '12px',
            border: 'none',
            background: 'transparent',
            fontSize: '14px',
            fontWeight: 600,
            color: '#ef4444',
            cursor: 'pointer',
            textAlign: 'left',
            width: '100%',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#fef2f2';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
          }}
        >
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </aside>

      {/* Main Content Area */}
      <main style={{ flexGrow: 1, padding: '40px 24px', maxWidth: '1200px', margin: '0 auto', width: '100%' }} className="dashboard-content">
        {children}
      </main>

      <style>{`
        @media (max-width: 768px) {
          .dashboard-container {
            flex-direction: column !important;
          }
          .dashboard-sidebar {
            width: 100% !important;
            border-right: none !important;
            border-bottom: 1px solid #e2e8f0 !important;
            padding: 16px !important;
            flex-direction: row !important;
            align-items: center !important;
            justifyContent: space-between !important;
          }
          .dashboard-sidebar > div {
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 4px !important;
            width: auto !important;
          }
          .dashboard-sidebar > div > div {
            display: none !important;
          }
          .sidebar-link {
            padding: 8px 12px !important;
            border-radius: 8px !important;
            font-size: 13px !important;
          }
          .dashboard-sidebar > button {
            width: auto !important;
            padding: 8px 12px !important;
            border-radius: 8px !important;
            font-size: 13px !important;
          }
          .dashboard-content {
            padding: 24px 16px !important;
          }
        }
      `}</style>
    </div>
  );
}
