export interface User {
  id: string;
  email: string;
  name: string;
  profileImage?: string;
  foodPreferences?: string[];
  dietaryRestrictions?: string[];
  locationPreferences?: {
    latitude: number;
    longitude: number;
    radius: number;
  };
  datePreferences?: {
    ageRange: [number, number];
    gender?: string;
    lookingFor?: string[];
  };
  createdAt: Date;
  updatedAt: Date;
}
