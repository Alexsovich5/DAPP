export interface SoulConnection {
  id: number;
  user1_id: number;
  user2_id: number;
  initiated_by: number;
  connection_stage: ConnectionStage;
  compatibility_score?: number;
  compatibility_breakdown?: CompatibilityBreakdown;
  reveal_day: number;
  mutual_reveal_consent: boolean;
  first_dinner_completed: boolean;
  status: string;
  created_at: string;
  updated_at: string;
  user1_profile?: UserProfile;
  user2_profile?: UserProfile;
}

export type ConnectionStage = 
  | 'soul_discovery' 
  | 'revelation_phase' 
  | 'photo_reveal' 
  | 'dinner_planning' 
  | 'completed';

export interface CompatibilityBreakdown {
  interests: number;
  values: number;
  demographics: number;
  communication: number;
  personality: number;
}

export interface CompatibilityResponse {
  total_compatibility: number;
  breakdown: CompatibilityBreakdown;
  match_quality: string;
  explanation: string;
}

export interface DiscoveryRequest {
  max_results?: number;
  min_compatibility?: number;
  hide_photos?: boolean;
  age_range_min?: number;
  age_range_max?: number;
}

export interface DiscoveryResponse {
  user_id: number;
  compatibility: CompatibilityResponse;
  profile_preview: ProfilePreview;
  is_photo_hidden: boolean;
}

export interface ProfilePreview {
  first_name: string;
  age: number;
  location?: string;
  bio?: string;
  interests: string[];
  emotional_depth_score?: number;
}

export interface UserProfile {
  id: number;
  first_name: string;
  profile_picture?: string;
}

export interface SoulConnectionCreate {
  user2_id: number;
  connection_stage?: ConnectionStage;
  reveal_day?: number;
  mutual_reveal_consent?: boolean;
  first_dinner_completed?: boolean;
  status?: string;
}

export interface SoulConnectionUpdate {
  connection_stage?: ConnectionStage;
  reveal_day?: number;
  mutual_reveal_consent?: boolean;
  first_dinner_completed?: boolean;
  status?: string;
}