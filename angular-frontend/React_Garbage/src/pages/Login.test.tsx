import React from 'react';
import { render, screen, fireEvent, waitFor, createMockAuthState } from '../utils/test-utils';
import Login from './Login';
import { useNavigate, useLocation } from 'react-router-dom';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
  useLocation: jest.fn(),
}));

describe('Login Component', () => {
  const mockNavigate = jest.fn();
  const mockLocation = {
    state: { from: { pathname: '/discover' } },
    pathname: '/login',
    search: '',
    hash: '',
  };

  beforeEach(() => {
    (useNavigate as jest.Mock).mockImplementation(() => mockNavigate);
    (useLocation as jest.Mock).mockImplementation(() => mockLocation);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders login form', () => {
    render(<Login />);
    
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /remember me/i })).toBeInTheDocument();
    expect(screen.getByText(/forgot password/i)).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(<Login />);
    
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(submitButton);

    expect(await screen.findByText('Please enter both email and password')).toBeInTheDocument();
  });

  it('handles successful login', async () => {
    const mockAuthState = createMockAuthState(); // Create fresh instance
    mockAuthState.login = jest.fn().mockResolvedValue(undefined);

    render(<Login />);

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockAuthState.login).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(mockNavigate).toHaveBeenCalledWith('/discover', { replace: true });
    });
  });

  it('handles login failure', async () => {
    const mockAuthState = createMockAuthState();
    const mockError = new Error('Invalid credentials');
    mockAuthState.login = jest.fn().mockRejectedValue(mockError);

    render(<Login />);

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
    fireEvent.click(submitButton);

    expect(await screen.findByText(/Invalid credentials/i)).toBeInTheDocument();
  });

  it('handles "Remember me" checkbox', () => {
    render(<Login />);
    
    const checkbox = screen.getByRole('checkbox', { name: /remember me/i });
    expect(checkbox).not.toBeChecked();
    
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
  });

  it('navigates to forgot password page', () => {
    render(<Login />);
    
    const forgotPasswordLink = screen.getByText(/forgot password/i);
    fireEvent.click(forgotPasswordLink);
    
    expect(mockNavigate).toHaveBeenCalledWith('/forgot-password');
  });

  it('navigates to register page', () => {
    render(<Login />);
    
    const registerLink = screen.getByText(/create one now/i);
    fireEvent.click(registerLink);
    
    expect(mockNavigate).toHaveBeenCalledWith('/register');
  });

  it('shows loading state during authentication', async () => {
    const mockAuthState = createMockAuthState();
    mockAuthState.login = jest.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

    render(<Login />);

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    expect(await screen.findByRole('progressbar')).toBeInTheDocument();
  });

  it('disables form inputs during submission', async () => {
    const mockAuthState = createMockAuthState();
    mockAuthState.login = jest.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

    render(<Login />);

    const emailInput = screen.getByLabelText(/email address/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(emailInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
      expect(submitButton).toBeDisabled();
    });
  });
});