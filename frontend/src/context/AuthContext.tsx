import React, {
  createContext,
  useContext,
  useState,
  useEffect,
} from "react";

import {
  getUserMeApi,
  getAdminMeApi,
} from "../services/api";

import type {
  UserProfile,
  AdminProfile,
} from "../services/api";

interface AuthContextType {
  user: UserProfile | null;
  userToken: string | null;

  admin: AdminProfile | null;
  adminToken: string | null;

  isLoading: boolean;

  loginUser: (
    token: string,
    user: UserProfile
  ) => void;

  loginAdmin: (
    token: string,
    admin: AdminProfile
  ) => void;

  logoutUser: () => void;
  logoutAdmin: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const USER_TOKEN_KEY = 'user_token';
const ADMIN_TOKEN_KEY = 'admin_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [userToken, setUserToken] = useState<string | null>(localStorage.getItem(USER_TOKEN_KEY));
  const [admin, setAdmin] = useState<AdminProfile | null>(null);
  const [adminToken, setAdminToken] = useState<string | null>(localStorage.getItem(ADMIN_TOKEN_KEY));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);
      const storedUserToken = localStorage.getItem(USER_TOKEN_KEY);
      const storedAdminToken = localStorage.getItem(ADMIN_TOKEN_KEY);

      if (storedUserToken) {
        try {
          const userData = await getUserMeApi(storedUserToken);
          setUser(userData);
          setUserToken(storedUserToken);
        } catch {
          localStorage.removeItem(USER_TOKEN_KEY);
          setUserToken(null);
          setUser(null);
        }
      }

      if (storedAdminToken) {
        try {
          const adminData = await getAdminMeApi(storedAdminToken);
          setAdmin(adminData);
          setAdminToken(storedAdminToken);
        } catch {
          localStorage.removeItem(ADMIN_TOKEN_KEY);
          setAdminToken(null);
          setAdmin(null);
        }
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const loginUser = (token: string, userData: UserProfile) => {
    localStorage.setItem(USER_TOKEN_KEY, token);
    setUserToken(token);
    setUser(userData);
  };

  const loginAdmin = (token: string, adminData: AdminProfile) => {
    localStorage.setItem(ADMIN_TOKEN_KEY, token);
    setAdminToken(token);
    setAdmin(adminData);
  };

  const logoutUser = () => {
    localStorage.removeItem(USER_TOKEN_KEY);
    setUserToken(null);
    setUser(null);
  };

  const logoutAdmin = () => {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    setAdminToken(null);
    setAdmin(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        userToken,
        admin,
        adminToken,
        isLoading,
        loginUser,
        loginAdmin,
        logoutUser,
        logoutAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
