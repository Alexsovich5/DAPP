export const environment = {
  production: true,
  apiUrl: 'https://api.dinner1.com/api/v1', // Production API URL
  tokenKey: 'dinner1_auth_token',
  socketUrl: 'wss://api.dinner1.com', // Secure WebSocket for production
  
  // UI Configuration
  ui: {
    toastDuration: 4000, // Slightly shorter for production
    animationDuration: 250, // Faster animations for production
    debounceTime: 500, // Longer debounce to reduce API calls
    pageSize: 20, // More items per page for better UX
    maxFileSize: 5 * 1024 * 1024, // 5MB max file upload size
    maxImageWidth: 1920, // Max image width for uploads
    maxImageHeight: 1080 // Max image height for uploads
  },
  
  // Soul Before Skin configuration
  soulBeforeSkin: {
    revelationCycleDays: 7,
    compatibilityThreshold: 60, // Higher threshold for production
    defaultPhotoHidden: true,
    emotionalOnboardingRequired: true,
    maxInterests: 8, // Slightly lower for focused matching
    maxBioLength: 300, // Shorter for better mobile experience
    minCompatibilityScore: 40 // Higher minimum for quality matches
  },
  
  // API Configuration
  api: {
    timeout: 20000, // Shorter timeout for production
    retryAttempts: 2, // Fewer retries to avoid overload
    retryDelay: 2000 // Longer delay between retries
  },
  
  // Security Configuration
  security: {
    sessionTimeout: 12 * 60 * 60 * 1000, // 12 hours for production
    tokenRefreshThreshold: 10 * 60 * 1000, // Refresh 10 minutes before expiry
    maxLoginAttempts: 3 // Stricter login attempt limit
  }
};