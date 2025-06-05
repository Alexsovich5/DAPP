import React from 'react';
import { render, screen } from './utils/test-utils';
import App from './App';

describe('App Component', () => {
  it('renders landing page content', () => {
    render(<App />);
    expect(screen.getByText('Find Your Perfect Dinner Date')).toBeInTheDocument();
    expect(screen.getByText(/Connect with people who share your culinary interests/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /join now/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
  });

  it('displays "How It Works" section', () => {
    render(<App />);
    expect(screen.getByText('How It Works')).toBeInTheDocument();
    expect(screen.getByText('Match with Foodies')).toBeInTheDocument();
  });

  it('renders navigation properly', () => {
    render(<App />);
    expect(screen.getByRole('link', { name: /join now/i })).toHaveAttribute('href', '/register');
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login');
  });
});
