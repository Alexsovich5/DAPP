import React from 'react';
import { render, screen, fireEvent, waitFor, createMockAuthState } from '../utils/test-utils';
import userEvent from '@testing-library/user-event';
import Register from './Register';

// Mock API responses
jest.mock('../services/api');

describe('Register Component', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  it('renders initial step (Account Details)', () => {
    render(<Register />);
    expect(screen.getByText('Create Account')).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument();
    // Using data-testid to find password fields
    expect(screen.getByTestId('password-input')).toBeInTheDocument();
    expect(screen.getByTestId('confirm-password-input')).toBeInTheDocument();
  });

  it('validates email format', async () => {
    render(<Register />);
    const emailInput = screen.getByLabelText(/email/i);
    await userEvent.type(emailInput, 'invalid-email');
    fireEvent.blur(emailInput);
    expect(await screen.findByText(/enter a valid email/i)).toBeInTheDocument();
  });

  it('validates password requirements', async () => {
    render(<Register />);
    // Using data-testid to find password fields
    const passwordInput = screen.getByTestId('password-input');
    await userEvent.type(passwordInput, 'weak');
    fireEvent.blur(passwordInput);
    expect(await screen.findByText(/password must be at least 8 characters/i)).toBeInTheDocument();
  });

  it('validates password confirmation match', async () => {
    render(<Register />);
    // Using data-testid to find password fields
    const passwordInput = screen.getByTestId('password-input');
    const confirmPasswordInput = screen.getByTestId('confirm-password-input');
    
    await userEvent.type(passwordInput, 'StrongPass123!');
    await userEvent.type(confirmPasswordInput, 'DifferentPass123!');
    fireEvent.blur(confirmPasswordInput);
    
    expect(await screen.findByText(/passwords must match/i)).toBeInTheDocument();
  });

  it('moves through registration steps when valid', async () => {
    render(<Register />);
    
    // Fill in account details
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByTestId('password-input'), 'StrongPass123!');
    await userEvent.type(screen.getByTestId('confirm-password-input'), 'StrongPass123!');
    await userEvent.click(screen.getByTestId('next-button'));

    // Personal Information step
    await userEvent.type(screen.getByLabelText(/first name/i), 'John');
    await userEvent.type(screen.getByLabelText(/last name/i), 'Doe');
    await userEvent.type(screen.getByLabelText(/date of birth/i), '1990-01-01');
    const genderSelect = screen.getByRole('combobox', { name: /gender/i });
    await userEvent.selectOptions(genderSelect, 'male');
    await userEvent.click(screen.getByTestId('next-button'));

    // Preferences step
    const dietarySelect = screen.getByRole('combobox', { name: /dietary preferences/i });
    await userEvent.selectOptions(dietarySelect, 'omnivore');
    const cuisineSelect = screen.getByRole('combobox', { name: /favorite cuisine/i });
    await userEvent.selectOptions(cuisineSelect, 'italian');
    await userEvent.type(screen.getByLabelText(/location/i), 'New York');
    const lookingForSelect = screen.getByRole('combobox', { name: /looking for/i });
    await userEvent.selectOptions(lookingForSelect, 'everyone');
    await userEvent.click(screen.getByLabelText(/terms/i));

    // Move to final step
    await userEvent.click(screen.getByTestId('next-button'));
    
    // Submit registration
    expect(screen.getByText('All steps completed - you\'re ready to join Dinner1!')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /create account/i }));
  });

  it('handles successful registration', async () => {
    const mockAuthState = createMockAuthState(); // Create fresh instance
    const mockRegister = jest.fn().mockResolvedValueOnce({
      email: 'test@example.com',
      firstName: 'John',
      lastName: 'Doe'
    });
    mockAuthState.register = mockRegister;

    render(<Register />);
    
    // Fill in account details
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByTestId('password-input'), 'StrongPass123!');
    await userEvent.type(screen.getByTestId('confirm-password-input'), 'StrongPass123!');
    await userEvent.click(screen.getByTestId('next-button'));

    // Fill in personal information
    await userEvent.type(screen.getByLabelText(/first name/i), 'John');
    await userEvent.type(screen.getByLabelText(/last name/i), 'Doe');
    await userEvent.type(screen.getByLabelText(/date of birth/i), '1990-01-01');
    const genderSelect = screen.getByRole('combobox', { name: /gender/i });
    await userEvent.selectOptions(genderSelect, 'male');
    await userEvent.click(screen.getByTestId('next-button'));

    // Fill in preferences
    const dietarySelect = screen.getByRole('combobox', { name: /dietary preferences/i });
    await userEvent.selectOptions(dietarySelect, 'omnivore');
    const cuisineSelect = screen.getByRole('combobox', { name: /favorite cuisine/i });
    await userEvent.selectOptions(cuisineSelect, 'italian');
    await userEvent.type(screen.getByLabelText(/location/i), 'New York');
    const lookingForSelect = screen.getByRole('combobox', { name: /looking for/i });
    await userEvent.selectOptions(lookingForSelect, 'everyone');
    await userEvent.click(screen.getByLabelText(/terms/i));
    await userEvent.click(screen.getByTestId('next-button'));

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    // Wait for the registration to complete
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'StrongPass123!',
        firstName: 'John',
        lastName: 'Doe',
        dateOfBirth: '1990-01-01',
        gender: 'male',
        dietaryPreferences: 'omnivore',
        cuisinePreferences: 'italian',
        location: 'New York',
        lookingFor: 'everyone'
      });
    });

    // Reset mock state
    Object.assign(mockAuthState, createMockAuthState());
  });

  it('handles registration failure', async () => {
    const mockAuthState = createMockAuthState(); // Create fresh instance
    const mockError = new Error('Registration failed');
    const mockRegister = jest.fn().mockRejectedValueOnce(mockError);
    mockAuthState.register = mockRegister;

    render(<Register />);
    
    // Fill in account details
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByTestId('password-input'), 'StrongPass123!');
    await userEvent.type(screen.getByTestId('confirm-password-input'), 'StrongPass123!');
    await userEvent.click(screen.getByTestId('next-button'));

    // Fill in personal information
    await userEvent.type(screen.getByLabelText(/first name/i), 'John');
    await userEvent.type(screen.getByLabelText(/last name/i), 'Doe');
    await userEvent.type(screen.getByLabelText(/date of birth/i), '1990-01-01');
    const genderSelect = screen.getByRole('combobox', { name: /gender/i });
    await userEvent.selectOptions(genderSelect, 'male');
    await userEvent.click(screen.getByTestId('next-button'));

    // Fill in preferences
    const dietarySelect = screen.getByRole('combobox', { name: /dietary preferences/i });
    await userEvent.selectOptions(dietarySelect, 'omnivore');
    const cuisineSelect = screen.getByRole('combobox', { name: /favorite cuisine/i });
    await userEvent.selectOptions(cuisineSelect, 'italian');
    await userEvent.type(screen.getByLabelText(/location/i), 'New York');
    const lookingForSelect = screen.getByRole('combobox', { name: /looking for/i });
    await userEvent.selectOptions(lookingForSelect, 'everyone');
    await userEvent.click(screen.getByLabelText(/terms/i));
    await userEvent.click(screen.getByTestId('next-button'));

    // Submit form and expect error
    const submitButton = screen.getByRole('button', { name: /create account/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalled();
      expect(screen.getByText(/registration failed/i)).toBeInTheDocument();
    });

    // Reset mock state
    Object.assign(mockAuthState, createMockAuthState());
  });

  it('validates age requirement', async () => {
    render(<Register />);
    
    // Fill in account details and move to personal information
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByTestId('password-input'), 'StrongPass123!');
    await userEvent.type(screen.getByTestId('confirm-password-input'), 'StrongPass123!');
    await userEvent.click(screen.getByTestId('next-button'));

    // Try to enter an invalid date of birth (under 18)
    const today = new Date();
    const underageDate = new Date(today.setFullYear(today.getFullYear() - 16)).toISOString().split('T')[0];
    await userEvent.type(screen.getByLabelText(/date of birth/i), underageDate);
    fireEvent.blur(screen.getByLabelText(/date of birth/i));
    
    expect(await screen.findByText(/must be at least 18 years old/i)).toBeInTheDocument();
  });
});