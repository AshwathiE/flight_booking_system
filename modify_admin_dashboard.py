import sys

def modify_file():
    filepath = 'frontend/src/pages/AdminDashboard.tsx'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Handlers
    handlers_code = '''
  // ── User Management helpers ──────────────────────────────
  const fetchUsers = async () => {
    if (!adminToken) return;
    setLoadingUsers(true);
    setUsersError('');
    try {
      const data = await getAdminUsersApi(adminToken);
      setUsers(data);
      setUsersFetched(true);
    } catch (err: any) {
      setUsersError('Failed to load users.');
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleToggleUsers = () => {
    if (showUsers) {
      setShowUsers(false);
    } else {
      setShowUsers(true);
      if (!usersFetched) {
        fetchUsers();
      }
    }
  };

  const handleRetryUsers = () => {
    setUsersFetched(false);
    fetchUsers();
  };

  const handleToggleUserStatus = async (userId: number, currentStatus: string) => {
    if (!adminToken) return;
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    try {
      await updateAdminUserStatusApi(userId, newStatus, adminToken);
      setUsers(users.map(u => u.id === userId ? { ...u, status: newStatus } : u));
    } catch (err) {
      alert('Failed to update user status.');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!adminToken) return;
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    try {
      await deleteAdminUserApi(userId, adminToken);
      setUsers(users.filter(u => u.id !== userId));
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to delete user.';
      alert(msg);
    }
  };

  // ── Flight management handlers ───────────────────────────'''
    content = content.replace('  // ── Flight management handlers ───────────────────────────', handlers_code)

    # Button
    button_code = '''
          <button
            onClick={handleToggleUsers}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              borderRadius: '12px',
              background: showUsers
                ? 'linear-gradient(135deg, #db2777, #be185d)'
                : 'linear-gradient(135deg, #f43f5e, #e11d48)',
              border: 'none',
              color: 'white',
              fontWeight: 700,
              fontSize: '15px',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(244,63,94,0.3)',
              transition: 'all 0.2s',
            }}
          >
            <Users size={18} />
            {showUsers ? 'Hide Users' : 'User Management'}
          </button>

        </div>

        {/* ── Bookings Section ── */}'''
    content = content.replace('        </div>\n\n        {/* ── Bookings Section ── */}', button_code)

    # UI Section
    ui_code = '''
        {/* ── User Management Section ── */}
        {showUsers && (
          <div
            style={{
              background: 'white',
              borderRadius: '20px',
              padding: '28px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
              marginBottom: '32px',
            }}
          >
            <h3
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: '#0f172a',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <Users size={20} color="#e11d48" />
              User Management
            </h3>

            {loadingUsers && (
              <div style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>
                Loading users...
              </div>
            )}

            {!loadingUsers && usersError && (
              <div style={{ padding: '16px', background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', borderRadius: '12px', display: 'flex', justifyContent: 'space-between' }}>
                <span>{usersError}</span>
                <button onClick={handleRetryUsers} style={{ padding: '6px 14px', borderRadius: '8px', background: '#dc2626', color: 'white', border: 'none', cursor: 'pointer' }}>Retry</button>
              </div>
            )}

            {!loadingUsers && !usersError && users.length === 0 && (
              <div style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>No users found.</div>
            )}

            {!loadingUsers && !usersError && users.length > 0 && (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                  <thead>
                    <tr style={{ background: '#f1f5f9', borderBottom: '2px solid #e2e8f0' }}>
                      <th style={{ padding: '12px 16px', textAlign: 'left', color: '#475569' }}>Name</th>
                      <th style={{ padding: '12px 16px', textAlign: 'left', color: '#475569' }}>Email</th>
                      <th style={{ padding: '12px 16px', textAlign: 'left', color: '#475569' }}>Role</th>
                      <th style={{ padding: '12px 16px', textAlign: 'left', color: '#475569' }}>Status</th>
                      <th style={{ padding: '12px 16px', textAlign: 'left', color: '#475569' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '12px 16px', fontWeight: 600 }}>{u.name}</td>
                        <td style={{ padding: '12px 16px' }}>{u.email}</td>
                        <td style={{ padding: '12px 16px' }}>{u.role}</td>
                        <td style={{ padding: '12px 16px' }}>
                          <span style={{ padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 700, background: u.status === 'active' ? '#dcfce7' : '#fef2f2', color: u.status === 'active' ? '#16a34a' : '#dc2626' }}>
                            {u.status}
                          </span>
                        </td>
                        <td style={{ padding: '12px 16px', display: 'flex', gap: '8px' }}>
                          <button onClick={() => handleToggleUserStatus(u.id, u.status)} style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', background: 'white', cursor: 'pointer' }}>
                            {u.status === 'active' ? 'Deactivate' : 'Activate'}
                          </button>
                          <button onClick={() => handleDeleteUser(u.id)} style={{ padding: '6px 12px', borderRadius: '6px', border: 'none', background: '#fee2e2', color: '#dc2626', cursor: 'pointer' }}>
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── Bookings Section ── */}'''
    content = content.replace('        {/* ── Bookings Section ── */}', ui_code, 1)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    modify_file()
