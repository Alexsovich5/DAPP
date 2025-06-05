import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthContext, User } from '../context/AuthContext'; // Import User type
import { ThemeProvider } from '@mui/material/styles';
import theme from '../theme';

// Mock auth context state
export const mockAuthState = {
  user: null as User | null, // Explicitly type user
  isAuthenticated: false,
  isLoading: false,
  error: null as string | null, // Allow string or null for error
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
  updateProfile: jest.fn(),
  clearError: jest.fn(),
};

const customRender = (
  ui: React.ReactElement,
  {
    route = '/',
    ...renderOptions
  }: RenderOptions & {
    route?: string;
  } = {}
) => {
  window.history.pushState({}, 'Test page', route);

  return render(ui, {
    wrapper: ({ children }) => (
      <BrowserRouter>
        <ThemeProvider theme={theme}>
          <AuthContext.Provider value={mockAuthState}>
            {children}
          </AuthContext.Provider>
        </ThemeProvider>
      </BrowserRouter>
    ),
    ...renderOptions,
  });
};

// Custom hooks testing
const createMockRouter = (params: any = {}) => ({
  push: jest.fn(),
  replace: jest.fn(),
  go: jest.fn(),
  goBack: jest.fn(),
  goForward: jest.fn(),
  block: jest.fn(),
  listen: jest.fn(),
  location: { pathname: '/', search: '', hash: '', state: null, ...params },
  match: { params: {}, isExact: true, path: '/', url: '/', ...params },
});

export * from '@testing-library/react';
export { customRender as render, createMockRouter, mockAuthState };