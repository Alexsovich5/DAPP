/**
 * Test Setup Configuration
 * Polyfills and mocks for Karma/Jasmine test environment
 */

// Mock localStorage for Chrome Headless
// Chrome Headless blocks localStorage access for security reasons
// This mock provides a working implementation for tests

// Create a shared store that persists across tests unless explicitly cleared
let localStorageStore: { [key: string]: string } = {};

const localStorageMock = {
  getItem(key: string): string | null {
    const value = localStorageStore[key];
    return value !== undefined ? value : null;
  },
  setItem(key: string, value: string): void {
    localStorageStore[key] = String(value);
  },
  removeItem(key: string): void {
    delete localStorageStore[key];
  },
  clear(): void {
    localStorageStore = {};
  },
  get length(): number {
    return Object.keys(localStorageStore).length;
  },
  key(index: number): string | null {
    const keys = Object.keys(localStorageStore);
    return keys[index] || null;
  },
  // Helper for debugging
  _getStore(): { [key: string]: string } {
    return localStorageStore;
  }
};

// Replace window.localStorage with mock
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
  configurable: true
});

// Mock sessionStorage as well (same issue)
let sessionStorageStore: { [key: string]: string } = {};

const sessionStorageMock = {
  getItem(key: string): string | null {
    const value = sessionStorageStore[key];
    return value !== undefined ? value : null;
  },
  setItem(key: string, value: string): void {
    sessionStorageStore[key] = String(value);
  },
  removeItem(key: string): void {
    delete sessionStorageStore[key];
  },
  clear(): void {
    sessionStorageStore = {};
  },
  get length(): number {
    return Object.keys(sessionStorageStore).length;
  },
  key(index: number): string | null {
    const keys = Object.keys(sessionStorageStore);
    return keys[index] || null;
  },
  // Helper for debugging
  _getStore(): { [key: string]: string } {
    return sessionStorageStore;
  }
};

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true,
  configurable: true
});

// Note: We don't suppress console.warn/error/log in test-setup
// because tests need to spy on these methods to verify error handling.
// Individual test suites can suppress console output if needed using beforeEach hooks.

// Export for test usage
export { localStorageMock, sessionStorageMock };
