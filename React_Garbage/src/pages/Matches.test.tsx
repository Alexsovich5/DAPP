import React from 'react';
import { screen, render, fireEvent, waitFor } from '../utils/test-utils';
import { act } from 'react-dom/test-utils';
import Matches from './Matches';
import { useNavigate } from 'react-router-dom';

// Mock useNavigate
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
}));

describe('Matches Component', () => {
  const mockNavigate = jest.fn();
  
  beforeEach(() => {
    (useNavigate as jest.Mock).mockImplementation(() => mockNavigate);
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.useRealTimers();
  });

  it('renders loading state initially', () => {
    render(<Matches />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders no matches message when there are no matches', async () => {
    // Mock the API to return empty array
    jest.spyOn(global, 'Promise').mockImplementationOnce(() => 
      Promise.resolve([])
    );

    render(<Matches />);
    
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(screen.getByText('No Matches Yet')).toBeInTheDocument();
    expect(screen.getByText('Start discovering potential matches to connect with fellow food lovers!')).toBeInTheDocument();
  });

  it('renders matches list when data is loaded', async () => {
    const mockMatches = [
      {
        _id: 'm1',
        userId: 'u1',
        firstName: 'Emma',
        lastName: 'Wilson',
        profilePicture: 'test.jpg',
        bio: 'Test bio',
        lastMessage: {
          text: 'Test message',
          timestamp: new Date().toISOString(),
          isRead: false,
        },
        matchedAt: new Date().toISOString(),
        restaurantSuggestions: [
          {
            id: 'r1',
            name: 'Test Restaurant',
            cuisine: 'Italian',
            rating: 4.5,
            price: '$$',
            imageUrl: 'restaurant.jpg',
            location: 'Test Location'
          }
        ]
      }
    ];

    jest.spyOn(global, 'Promise').mockImplementationOnce(() => 
      Promise.resolve(mockMatches)
    );

    render(<Matches />);
    
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(screen.getByText('Emma Wilson')).toBeInTheDocument();
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('navigates to chat when clicking on a match', async () => {
    const mockMatches = [
      {
        _id: 'm1',
        userId: 'u1',
        firstName: 'Emma',
        lastName: 'Wilson',
        profilePicture: 'test.jpg',
        lastMessage: {
          text: 'Test message',
          timestamp: new Date().toISOString(),
          isRead: false,
        },
        matchedAt: new Date().toISOString(),
      }
    ];

    jest.spyOn(global, 'Promise').mockImplementationOnce(() => 
      Promise.resolve(mockMatches)
    );

    render(<Matches />);
    
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    fireEvent.click(screen.getByText('Emma Wilson'));
    expect(mockNavigate).toHaveBeenCalledWith('/chat/u1');
  });

  it('switches between messages and restaurant suggestions tabs', async () => {
    const mockMatches = [
      {
        _id: 'm1',
        userId: 'u1',
        firstName: 'Emma',
        lastName: 'Wilson',
        profilePicture: 'test.jpg',
        lastMessage: {
          text: 'Test message',
          timestamp: new Date().toISOString(),
          isRead: false,
        },
        matchedAt: new Date().toISOString(),
        restaurantSuggestions: [
          {
            id: 'r1',
            name: 'Test Restaurant',
            cuisine: 'Italian',
            rating: 4.5,
            price: '$$',
            imageUrl: 'restaurant.jpg',
            location: 'Test Location'
          }
        ]
      }
    ];

    jest.spyOn(global, 'Promise').mockImplementationOnce(() => 
      Promise.resolve(mockMatches)
    );

    render(<Matches />);
    
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    // Initially on Messages tab
    expect(screen.getByText('Test message')).toBeInTheDocument();

    // Switch to Restaurant Suggestions tab
    fireEvent.click(screen.getByRole('tab', { name: /restaurant suggestions/i }));
    expect(screen.getByText('Test Restaurant')).toBeInTheDocument();
  });

  it('handles API error gracefully', async () => {
    jest.spyOn(global, 'Promise').mockImplementationOnce(() => 
      Promise.reject(new Error('API Error'))
    );

    render(<Matches />);
    
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(screen.getByText('Failed to load matches. Please try again later.')).toBeInTheDocument();
  });

  it('formats message timestamps correctly', async () => {
    const now = new Date();
    const mockMatches = [
      {
        _id: 'm1',
        userId: 'u1',
        firstName: 'Emma',
        lastName: 'Wilson',
        profilePicture: 'test.jpg',
        lastMessage: {
          text: 'Today message',
          timestamp: now.toISOString(),
          isRead: false,
        },
        matchedAt: now.toISOString(),
      },
      {
        _id: 'm2',
        userId: 'u2',
        firstName: 'John',
        lastName: 'Doe',
        profilePicture: 'test2.jpg',
        lastMessage: {
          text: 'Yesterday message',
          timestamp: new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString(),
          isRead: true,
        },
        matchedAt: now.toISOString(),
      }
    ];

    jest.spyOn(global, 'Promise').mockImplementationOnce(() => 
      Promise.resolve(mockMatches)
    );

    render(<Matches />);
    
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(screen.getByText(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))).toBeInTheDocument();
    expect(screen.getByText('Yesterday')).toBeInTheDocument();
  });
});