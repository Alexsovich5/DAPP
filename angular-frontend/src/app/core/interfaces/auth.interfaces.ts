export interface User {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  profile_picture?: string;
  date_of_birth?: string;
  gender?: string;
  is_profile_complete: boolean;
  is_active: boolean;
  bio?: string;
  interests?: string[];
  dietary_preferences?: string[];
  location?: string;
  created_at?: string;
  updated_at?: string;

  // Soul Before Skin fields
  emotional_onboarding_completed?: boolean;
  soul_profile_visibility?: 'hidden' | 'visible' | 'selective';
  emotional_depth_score?: number;
  core_values?: Record<string, unknown>;
  personality_traits?: Record<string, unknown>;
  communication_style?: Record<string, unknown>;
  emotional_responses?: Record<string, unknown>;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  gender?: string;
  dietary_preferences?: string[];
  cuisine_preferences?: string[];
  location?: string;
  looking_for?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ValidationError {
  loc: string[];
  msg: string;
  type: string;
}

export interface ApiErrorResponse {
  detail: ValidationError[] | string;
}
