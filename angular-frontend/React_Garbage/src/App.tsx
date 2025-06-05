import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './context/AuthContext';
import logo from './logo.svg';
import './App.css';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import Profile from './pages/Profile';
import EditProfile from './pages/EditProfile';
import Discover from './pages/Discover';
import Matches from './pages/Matches';
import Chat from './pages/Chat';
import Preferences from './pages/Preferences';
import Landing from './pages/Landing';
import NotFound from './pages/NotFound';
import { ProtectedRoute } from './components/common/ProtectedRoute';

// Theme definition
const theme = createTheme({
  palette: {
    primary: {
      main: '#ff4b4b', // A warm reddish color for a dating app
      light: '#ff7c7c',
      dark: '#c50000',
    },
    secondary: {
      main: '#4caf50', // Green for "match" actions
      light: '#80e27e',
      dark: '#087f23',
    },
    background: {
      default: '#f8f8f8',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Poppins", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 600,
    },
    h2: {
      fontWeight: 600,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            
            {/* Protected routes */}
            <Route path="/profile" element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            } />
            <Route path="/edit-profile" element={
              <ProtectedRoute>
                <EditProfile />
              </ProtectedRoute>
            } />
            <Route path="/discover" element={
              <ProtectedRoute>
                <Discover />
              </ProtectedRoute>
            } />
            <Route path="/matches" element={
              <ProtectedRoute>
                <Matches />
              </ProtectedRoute>
            } />
            <Route path="/chat/:id" element={
              <ProtectedRoute>
                <Chat />
              </ProtectedRoute>
            } />
            <Route path="/preferences" element={
              <ProtectedRoute>
                <Preferences />
              </ProtectedRoute>
            } />
            
            {/* Not found route */}
            <Route path="/404" element={<NotFound />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
