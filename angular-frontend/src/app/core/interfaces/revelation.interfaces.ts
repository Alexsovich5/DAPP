export interface DailyRevelation {
  id: number;
  connection_id: number;
  sender_id: number;
  day_number: number;
  revelation_type: RevelationType;
  content: string;
  is_read: boolean;
  created_at: string;
  sender_name?: string;
}

export type RevelationType = 
  | 'personal_value'
  | 'meaningful_experience'
  | 'hope_or_dream'
  | 'what_makes_laugh'
  | 'challenge_overcome'
  | 'ideal_connection'
  | 'photo_reveal';

export interface DailyRevelationCreate {
  connection_id: number;
  day_number: number;
  revelation_type: RevelationType;
  content: string;
}

export interface DailyRevelationUpdate {
  content?: string;
  is_read?: boolean;
}

export interface RevelationTimelineResponse {
  connection_id: number;
  current_day: number;
  revelations: DailyRevelation[];
  next_revelation_type?: RevelationType;
  is_cycle_complete: boolean;
}

export interface RevelationPrompt {
  day_number: number;
  revelation_type: RevelationType;
  prompt_text: string;
  example_response: string;
}

export interface EmotionalOnboarding {
  relationship_values?: string;
  ideal_evening?: string;
  feeling_understood?: string;
  core_values?: Record<string, any>;
  personality_traits?: Record<string, any>;
  communication_style?: Record<string, any>;
  interests?: string[];
}

export interface OnboardingResponse {
  emotional_onboarding_completed: boolean;
  emotional_depth_score?: number;
  next_step?: string;
}