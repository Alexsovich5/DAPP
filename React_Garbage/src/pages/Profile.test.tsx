import React from 'react';
import { render, screen, fireEvent, createMockAuthState } from '../utils/test-utils';
import Profile from './Profile';
import { useNavigate } from 'react-router-dom';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}));

describe('Profile Component', () => {
  const mockNavigate = jest.fn();

  const mockUser = {
    _id: '123',
    email: 'john.doe@example.com',
    firstName: 'John',
    lastName: 'Doe',
    profilePicture: 'https://example.com/profile.jpg',
    dateOfBirth: '1990-01-01',
    gender: 'male',
    isProfileComplete: true,
    bio: 'Software Engineer',
    interests: ['coding', 'hiking'],
    dietaryPreferences: ['vegetarian'],
    locationPreferences: { city: 'New York', state: 'NY', country: 'USA' },
    matchPreferences: { ageRange: { min: 25, max: 35 }, gender: 'female', distance: 50 },
  };

  beforeEach(() => {
    (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
    // Reset mockAuthState before each test if needed, or set defaults
    const mockAuthState = createMockAuthState();
    Object.assign(mockAuthState, {
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: jest.fn(),
      logout: jest.fn(),
      register: jest.fn(),
      updateProfile: jest.fn(),
      clearError: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state', () => {
    const mockAuthState = createMockAuthState(); // Create fresh instance
    mockAuthState.isLoading = true;
    render(<Profile />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders error state', () => {
    const mockAuthState = createMockAuthState();
    mockAuthState.error = 'Failed to load profile';
    render(<Profile />);
    expect(screen.getByText(/failed to load profile/i)).toBeInTheDocument();
  });

  it('renders message when user is not authenticated', () => {
    const mockAuthState = createMockAuthState();
    mockAuthState.isAuthenticated = false;
    render(<Profile />);
    expect(screen.getByText(/please log in to view your profile/i)).toBeInTheDocument();
  });

  it('renders user profile information when authenticated', () => {
    // Set the user in the global mockAuthState for this test
    const mockAuthState = createMockAuthState();
    mockAuthState.user = mockUser;
    mockAuthState.isAuthenticated = true;

    render(<Profile />); // Remove the authState option

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john.doe@example.com')).toBeInTheDocument();
    expect(screen.getByText('Software Engineer')).toBeInTheDocument();
    expect(screen.getByAltText('John Doe')).toHaveAttribute('src', 'https://example.com/profile.jpg');
  });

  it('navigates to edit profile page on button click', () => {
    // Set the user in the global mockAuthState for this test
    const mockAuthState = createMockAuthState();
    mockAuthState.user = mockUser;
    mockAuthState.isAuthenticated = true;

    render(<Profile />); // Remove the authState option

    const editButton = screen.getByRole('button', { name: /edit profile/i });
    fireEvent.click(editButton);
    expect(mockNavigate).toHaveBeenCalledWith('/edit-profile');
  });
});