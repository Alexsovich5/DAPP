// Demo server environment — single-origin via NPM.
// All API calls go through the same hostname; nginx in the frontend
// container proxies /api/ to the backend container.
export const environment = {
  production: true,
  apiUrl: '/api/v1',
  tokenKey: 'dinner_first_auth_token',
  socketUrl: '/ws',

  ui: {
    toastDuration: 4000,
    animationDuration: 250,
    debounceTime: 500,
    pageSize: 20,
    maxFileSize: 5 * 1024 * 1024,
    maxImageWidth: 1920,
    maxImageHeight: 1080,
  },

  soulBeforeSkin: {
    revelationCycleDays: 7,
    compatibilityThreshold: 60,
    defaultPhotoHidden: true,
    emotionalOnboardingRequired: true,
    maxInterests: 8,
    maxBioLength: 300,
    minCompatibilityScore: 40,
  },

  api: {
    timeout: 20000,
    retryAttempts: 2,
    retryDelay: 2000,
  },

  security: {
    sessionTimeout: 12 * 60 * 60 * 1000,
    tokenRefreshThreshold: 10 * 60 * 1000,
    maxLoginAttempts: 3,
  },
};
