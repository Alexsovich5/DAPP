/**
 * Test user fixtures for E2E tests
 */

export interface TestUser {
  email: string;
  password: string;
  username: string;
  firstName: string;
  lastName: string;
}

export const testUsers = {
  validUser: {
    email: 'test.user@dinnerfirst.com',
    password: 'TestPassword123!',
    username: 'testuser',
    firstName: 'Test',
    lastName: 'User',
  } as TestUser,

  newUser: {
    email: `test.${Date.now()}@dinnerfirst.com`,
    password: 'NewUser123!',
    username: `newuser${Date.now()}`,
    firstName: 'New',
    lastName: 'User',
  } as TestUser,

  onboardedUser: {
    email: 'onboarded.user@dinnerfirst.com',
    password: 'Onboarded123!',
    username: 'onboardeduser',
    firstName: 'Onboarded',
    lastName: 'User',
  } as TestUser,
};

export const mockProfileData = {
  interests: ['photography', 'hiking', 'cooking', 'music'],
  values: ['honesty', 'kindness', 'growth', 'adventure'],
  bio: 'Love exploring new places and meeting interesting people.',
  lookingFor: 'meaningful connections and shared experiences',
};
