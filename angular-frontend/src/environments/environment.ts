export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api/v1',
  tokenKey: 'dinner1_auth_token',
  socketUrl: 'ws://localhost:5000',
  
  // UI Configuration
  ui: {
    toastDuration: 5000, // Default toast display duration in ms
    animationDuration: 300, // Default animation duration in ms
    debounceTime: 300, // Default debounce time for search/input
    pageSize: 10, // Default pagination size
    maxFileSize: 5 * 1024 * 1024, // 5MB max file upload size
    maxImageWidth: 1920, // Max image width for uploads
    maxImageHeight: 1080 // Max image height for uploads
  },
  
  // Soul Before Skin configuration
  soulBeforeSkin: {
    revelationCycleDays: 7,
    compatibilityThreshold: 50,
    defaultPhotoHidden: true,
    emotionalOnboardingRequired: true,
    maxInterests: 10, // Maximum interests a user can select
    maxBioLength: 500, // Maximum biography length
    minCompatibilityScore: 30 // Minimum compatibility score to show matches
  },
  
  // API Configuration
  api: {
    timeout: 30000, // Default API timeout in ms
    retryAttempts: 3, // Number of retry attempts for failed requests
    retryDelay: 1000 // Delay between retry attempts in ms
  },
  
  // Security Configuration
  security: {
    sessionTimeout: 24 * 60 * 60 * 1000, // 24 hours in ms
    tokenRefreshThreshold: 5 * 60 * 1000, // Refresh token 5 minutes before expiry
    maxLoginAttempts: 5 // Maximum login attempts before lockout
  }
};
