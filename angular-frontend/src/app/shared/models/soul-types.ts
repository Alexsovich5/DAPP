/**
 * Shared type definitions for Soul-based components
 */

export interface SoulConfig {
  type: 'primary' | 'secondary' | 'neutral';
  state: 'active' | 'dormant' | 'connecting' | 'matched';
  energy: number;
  label: string;
  showParticles?: boolean;
  showSparkles?: boolean;
}

export interface ConnectionLine {
  show: boolean;
  strength: number;
  animated: boolean;
  color?: string;
}

export type AnimationConfig = Record<string, unknown>;

export type ComponentEventData = Record<string, unknown>;
