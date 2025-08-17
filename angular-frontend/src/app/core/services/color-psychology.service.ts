import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface EmotionalColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  shadow: string;
  glow: string;
}

export interface MoodState {
  id: string;
  name: string;
  description: string;
  primaryEmotion: 'joy' | 'love' | 'trust' | 'growth' | 'mystery';
  intensity: 'subtle' | 'moderate' | 'strong' | 'intense';
  colorPalette: EmotionalColorPalette;
  psychologicalEffects: string[];
}

export interface CompatibilityColorScheme {
  level: 'soulmate' | 'exceptional' | 'strong' | 'good' | 'potential' | 'growing';
  score: number;
  colors: {
    primary: string;
    secondary: string;
    gradient: string;
    glow: string;
    shadowIntensity: 'soft' | 'medium' | 'strong';
  };
  emotionalImpact: string;
}

export interface ColorPersonality {
  dominant: 'warm' | 'cool' | 'neutral';
  trustPreference: 'security' | 'adventure' | 'balance';
  emotionalDepth: 'surface' | 'moderate' | 'deep' | 'profound';
  communicationStyle: 'vibrant' | 'calm' | 'sophisticated' | 'playful';
}

@Injectable({
  providedIn: 'root'
})
export class ColorPsychologyService {
  private currentMoodSubject = new BehaviorSubject<MoodState>(this.getDefaultMood());
  private colorPersonalitySubject = new BehaviorSubject<ColorPersonality>(this.getDefaultPersonality());
  private adaptiveColorsSubject = new BehaviorSubject<boolean>(true);

  public currentMood$ = this.currentMoodSubject.asObservable();
  public colorPersonality$ = this.colorPersonalitySubject.asObservable();
  public adaptiveColors$ = this.adaptiveColorsSubject.asObservable();

  // Predefined mood states based on color psychology research
  private moodStates: MoodState[] = [
    {
      id: 'contemplative',
      name: 'Contemplative',
      description: 'Deep thinking and reflection',
      primaryEmotion: 'mystery',
      intensity: 'moderate',
      colorPalette: {
        primary: 'var(--soul-purple-600)',
        secondary: 'var(--trust-sage-600)',
        accent: 'var(--trust-ocean-600)',
        background: 'var(--mood-contemplative-background)',
        shadow: 'var(--shadow-soul-soft)',
        glow: 'var(--emotion-mystery-glow)'
      },
      psychologicalEffects: [
        'Encourages introspection',
        'Promotes thoughtful decision-making',
        'Creates sense of depth and meaning'
      ]
    },
    {
      id: 'romantic',
      name: 'Romantic',
      description: 'Connection and intimacy',
      primaryEmotion: 'love',
      intensity: 'strong',
      colorPalette: {
        primary: 'var(--emotion-rose-600)',
        secondary: 'var(--soul-purple-600)',
        accent: 'var(--warmth-sunset-600)',
        background: 'var(--mood-romantic-background)',
        shadow: 'var(--shadow-emotional-soft)',
        glow: 'var(--emotion-love-glow)'
      },
      psychologicalEffects: [
        'Stimulates emotional connection',
        'Enhances feelings of warmth',
        'Promotes intimacy and closeness'
      ]
    },
    {
      id: 'energetic',
      name: 'Energetic',
      description: 'Excitement and adventure',
      primaryEmotion: 'joy',
      intensity: 'intense',
      colorPalette: {
        primary: 'var(--warmth-sunset-600)',
        secondary: 'var(--emotion-rose-600)',
        accent: 'var(--trust-ocean-600)',
        background: 'var(--mood-energetic-background)',
        shadow: 'var(--shadow-emotional-medium)',
        glow: 'var(--emotion-joy-glow)'
      },
      psychologicalEffects: [
        'Increases energy and enthusiasm',
        'Promotes active engagement',
        'Stimulates creativity and spontaneity'
      ]
    },
    {
      id: 'peaceful',
      name: 'Peaceful',
      description: 'Calm and serenity',
      primaryEmotion: 'trust',
      intensity: 'subtle',
      colorPalette: {
        primary: 'var(--trust-forest-600)',
        secondary: 'var(--trust-ocean-600)',
        accent: 'var(--trust-sage-600)',
        background: 'var(--mood-peaceful-background)',
        shadow: 'var(--shadow-trust-soft)',
        glow: 'var(--emotion-trust-glow)'
      },
      psychologicalEffects: [
        'Reduces stress and anxiety',
        'Promotes sense of safety',
        'Encourages open communication'
      ]
    },
    {
      id: 'sophisticated',
      name: 'Sophisticated',
      description: 'Elegance and maturity',
      primaryEmotion: 'growth',
      intensity: 'moderate',
      colorPalette: {
        primary: 'var(--trust-sage-700)',
        secondary: 'var(--soul-purple-700)',
        accent: 'var(--trust-ocean-700)',
        background: 'var(--mood-sophisticated-background)',
        shadow: 'var(--shadow-soul-medium)',
        glow: 'var(--emotion-growth-glow)'
      },
      psychologicalEffects: [
        'Conveys wisdom and experience',
        'Builds trust through stability',
        'Promotes mature decision-making'
      ]
    }
  ];

  // Compatibility level color schemes
  private compatibilitySchemes: CompatibilityColorScheme[] = [
    {
      level: 'soulmate',
      score: 95,
      colors: {
        primary: '#ffd700',
        secondary: '#ff6b9d',
        gradient: 'var(--compatibility-soulmate-gradient)',
        glow: 'var(--compatibility-soulmate-glow)',
        shadowIntensity: 'strong'
      },
      emotionalImpact: 'Creates euphoric connection feeling'
    },
    {
      level: 'exceptional',
      score: 85,
      colors: {
        primary: 'var(--emotion-rose-500)',
        secondary: 'var(--soul-purple-500)',
        gradient: 'var(--compatibility-exceptional-gradient)',
        glow: 'var(--compatibility-exceptional-glow)',
        shadowIntensity: 'medium'
      },
      emotionalImpact: 'Builds strong emotional attraction'
    },
    {
      level: 'strong',
      score: 75,
      colors: {
        primary: 'var(--soul-purple-500)',
        secondary: 'var(--trust-ocean-500)',
        gradient: 'var(--compatibility-strong-gradient)',
        glow: 'var(--compatibility-strong-glow)',
        shadowIntensity: 'medium'
      },
      emotionalImpact: 'Encourages deeper exploration'
    },
    {
      level: 'good',
      score: 65,
      colors: {
        primary: 'var(--trust-ocean-500)',
        secondary: 'var(--trust-forest-500)',
        gradient: 'var(--compatibility-good-gradient)',
        glow: 'var(--compatibility-good-glow)',
        shadowIntensity: 'soft'
      },
      emotionalImpact: 'Provides stable foundation for growth'
    },
    {
      level: 'potential',
      score: 55,
      colors: {
        primary: 'var(--trust-forest-500)',
        secondary: 'var(--warmth-sunset-500)',
        gradient: 'var(--compatibility-potential-gradient)',
        glow: 'var(--compatibility-potential-glow)',
        shadowIntensity: 'soft'
      },
      emotionalImpact: 'Suggests opportunity for development'
    },
    {
      level: 'growing',
      score: 45,
      colors: {
        primary: 'var(--trust-sage-500)',
        secondary: 'var(--trust-ocean-400)',
        gradient: 'var(--compatibility-growing-gradient)',
        glow: 'var(--compatibility-growing-glow)',
        shadowIntensity: 'soft'
      },
      emotionalImpact: 'Maintains hope while managing expectations'
    }
  ];

  constructor() {
    this.initializeColorPersonality();
  }

  /**
   * Set the current mood state
   */
  setMood(moodId: string): void {
    const mood = this.moodStates.find(m => m.id === moodId);
    if (mood) {
      this.currentMoodSubject.next(mood);
      this.applyMoodColors(mood);
    }
  }

  /**
   * Get all available mood states
   */
  getAvailableMoods(): MoodState[] {
    return [...this.moodStates];
  }

  /**
   * Get current mood state
   */
  getCurrentMood(): MoodState {
    return this.currentMoodSubject.value;
  }

  /**
   * Get color scheme for compatibility score
   */
  getCompatibilityColors(score: number): CompatibilityColorScheme {
    if (score >= 90) return this.compatibilitySchemes[0]; // soulmate
    if (score >= 80) return this.compatibilitySchemes[1]; // exceptional
    if (score >= 70) return this.compatibilitySchemes[2]; // strong
    if (score >= 60) return this.compatibilitySchemes[3]; // good
    if (score >= 50) return this.compatibilitySchemes[4]; // potential
    return this.compatibilitySchemes[5]; // growing
  }

  /**
   * Analyze user color personality based on preferences
   */
  analyzeColorPersonality(preferences: {
    favoriteColors: string[];
    emotionalStyle: string;
    trustBuilding: string;
    communicationPreference: string;
  }): ColorPersonality {
    const personality: ColorPersonality = {
      dominant: this.analyzeDominantColorTemperature(preferences.favoriteColors),
      trustPreference: this.analyzeTrustPreference(preferences.trustBuilding),
      emotionalDepth: this.analyzeEmotionalDepth(preferences.emotionalStyle),
      communicationStyle: this.analyzeCommunicationStyle(preferences.communicationPreference)
    };

    this.colorPersonalitySubject.next(personality);
    return personality;
  }

  /**
   * Get personalized color recommendations
   */
  getPersonalizedColors(context: 'discovery' | 'conversation' | 'profile' | 'connection'): EmotionalColorPalette {
    const personality = this.colorPersonalitySubject.value;
    const currentMood = this.currentMoodSubject.value;
    
    return this.blendPersonalityWithMood(personality, currentMood, context);
  }

  /**
   * Apply contextual color theme to page
   */
  applyContextTheme(context: 'discovery' | 'conversation' | 'profile' | 'connection'): void {
    const colors = this.getPersonalizedColors(context);
    
    // Apply CSS custom properties to document root
    document.documentElement.style.setProperty('--dynamic-primary', colors.primary);
    document.documentElement.style.setProperty('--dynamic-secondary', colors.secondary);
    document.documentElement.style.setProperty('--dynamic-accent', colors.accent);
    document.documentElement.style.setProperty('--dynamic-background', colors.background);
    document.documentElement.style.setProperty('--dynamic-shadow', colors.shadow);
    document.documentElement.style.setProperty('--dynamic-glow', colors.glow);

    // Add context class to body
    document.body.classList.remove('discovery-theme', 'conversation-theme', 'profile-theme', 'connection-theme');
    document.body.classList.add(`${context}-theme`);
  }

  /**
   * Get optimal colors for time of day
   */
  getTimeBasedColors(): EmotionalColorPalette {
    const hour = new Date().getHours();
    
    if (hour >= 6 && hour < 12) {
      // Morning - energetic and optimistic
      return this.moodStates.find(m => m.id === 'energetic')!.colorPalette;
    } else if (hour >= 12 && hour < 17) {
      // Afternoon - focused and trust-building
      return this.moodStates.find(m => m.id === 'sophisticated')!.colorPalette;
    } else if (hour >= 17 && hour < 20) {
      // Evening - romantic and connection-focused
      return this.moodStates.find(m => m.id === 'romantic')!.colorPalette;
    } else {
      // Night - contemplative and deep
      return this.moodStates.find(m => m.id === 'contemplative')!.colorPalette;
    }
  }

  /**
   * Toggle adaptive color mode
   */
  toggleAdaptiveColors(enabled: boolean): void {
    this.adaptiveColorsSubject.next(enabled);
    
    if (enabled) {
      this.enableAdaptiveMode();
    } else {
      this.disableAdaptiveMode();
    }
  }

  /**
   * Get emotional color for specific feeling
   */
  getEmotionalColor(emotion: 'joy' | 'love' | 'trust' | 'growth' | 'mystery'): string {
    const emotionMap = {
      joy: 'var(--emotion-joy-color)',
      love: 'var(--emotion-love-color)',
      trust: 'var(--emotion-trust-color)',
      growth: 'var(--emotion-growth-color)',
      mystery: 'var(--emotion-mystery-color)'
    };
    
    return emotionMap[emotion];
  }

  /**
   * Create custom mood from user preferences
   */
  createCustomMood(preferences: {
    name: string;
    primaryColor: string;
    secondaryColor: string;
    intensity: 'subtle' | 'moderate' | 'strong' | 'intense';
    emotions: string[];
  }): MoodState {
    const customMood: MoodState = {
      id: `custom-${Date.now()}`,
      name: preferences.name,
      description: `Custom mood: ${preferences.emotions.join(', ')}`,
      primaryEmotion: 'mystery', // Default for custom moods
      intensity: preferences.intensity,
      colorPalette: {
        primary: preferences.primaryColor,
        secondary: preferences.secondaryColor,
        accent: this.generateAccentColor(preferences.primaryColor, preferences.secondaryColor),
        background: this.generateGradientBackground(preferences.primaryColor, preferences.secondaryColor),
        shadow: this.generateShadow(preferences.primaryColor, preferences.intensity),
        glow: this.generateGlow(preferences.primaryColor, preferences.intensity)
      },
      psychologicalEffects: [
        'Custom emotional experience',
        `${preferences.intensity} intensity impact`,
        'Personalized psychological response'
      ]
    };

    this.moodStates.push(customMood);
    return customMood;
  }

  // Private helper methods

  private getDefaultMood(): MoodState {
    return this.moodStates[0]; // contemplative
  }

  private getDefaultPersonality(): ColorPersonality {
    return {
      dominant: 'neutral',
      trustPreference: 'balance',
      emotionalDepth: 'moderate',
      communicationStyle: 'calm'
    };
  }

  private initializeColorPersonality(): void {
    // Try to load saved personality from localStorage
    const saved = localStorage.getItem('color-personality');
    if (saved) {
      try {
        const personality = JSON.parse(saved);
        this.colorPersonalitySubject.next(personality);
      } catch (error) {
        console.warn('Failed to load color personality:', error);
      }
    }
  }

  private applyMoodColors(mood: MoodState): void {
    const palette = mood.colorPalette;
    
    // Apply mood colors to CSS custom properties
    document.documentElement.style.setProperty('--mood-primary', palette.primary);
    document.documentElement.style.setProperty('--mood-secondary', palette.secondary);
    document.documentElement.style.setProperty('--mood-accent', palette.accent);
    document.documentElement.style.setProperty('--mood-background', palette.background);
    document.documentElement.style.setProperty('--mood-shadow', palette.shadow);
    document.documentElement.style.setProperty('--mood-glow', palette.glow);

    // Add mood class to body
    document.body.classList.remove(...this.moodStates.map(m => `mood-${m.id}`));
    document.body.classList.add(`mood-${mood.id}`);
  }

  private analyzeDominantColorTemperature(colors: string[]): 'warm' | 'cool' | 'neutral' {
    // Simplified analysis - in real implementation, this would be more sophisticated
    const warmColors = ['red', 'orange', 'yellow', 'pink'];
    const coolColors = ['blue', 'green', 'purple', 'teal'];
    
    const warmCount = colors.filter(c => warmColors.some(w => c.includes(w))).length;
    const coolCount = colors.filter(c => coolColors.some(w => c.includes(w))).length;
    
    if (warmCount > coolCount) return 'warm';
    if (coolCount > warmCount) return 'cool';
    return 'neutral';
  }

  private analyzeTrustPreference(trustStyle: string): 'security' | 'adventure' | 'balance' {
    if (trustStyle.includes('security') || trustStyle.includes('stable')) return 'security';
    if (trustStyle.includes('adventure') || trustStyle.includes('exciting')) return 'adventure';
    return 'balance';
  }

  private analyzeEmotionalDepth(style: string): 'surface' | 'moderate' | 'deep' | 'profound' {
    if (style.includes('casual') || style.includes('light')) return 'surface';
    if (style.includes('meaningful') || style.includes('deep')) return 'deep';
    if (style.includes('intense') || style.includes('profound')) return 'profound';
    return 'moderate';
  }

  private analyzeCommunicationStyle(style: string): 'vibrant' | 'calm' | 'sophisticated' | 'playful' {
    if (style.includes('vibrant') || style.includes('energetic')) return 'vibrant';
    if (style.includes('calm') || style.includes('peaceful')) return 'calm';
    if (style.includes('sophisticated') || style.includes('elegant')) return 'sophisticated';
    return 'playful';
  }

  private blendPersonalityWithMood(
    personality: ColorPersonality, 
    mood: MoodState, 
    context: string
  ): EmotionalColorPalette {
    // Complex blending logic that considers personality, mood, and context
    // This would be more sophisticated in a real implementation
    
    const basePalette = mood.colorPalette;
    
    // Adjust intensity based on personality
    const intensityMultiplier = this.getIntensityMultiplier(personality.emotionalDepth);
    
    return {
      primary: basePalette.primary,
      secondary: basePalette.secondary,
      accent: basePalette.accent,
      background: basePalette.background,
      shadow: basePalette.shadow,
      glow: this.adjustGlowIntensity(basePalette.glow, intensityMultiplier)
    };
  }

  private getIntensityMultiplier(depth: string): number {
    const multipliers = {
      surface: 0.6,
      moderate: 0.8,
      deep: 1.0,
      profound: 1.2
    };
    return multipliers[depth as keyof typeof multipliers] || 1.0;
  }

  private adjustGlowIntensity(glow: string, multiplier: number): string {
    // Simplified glow adjustment - would be more sophisticated in real implementation
    return glow;
  }

  private enableAdaptiveMode(): void {
    // Enable automatic mood switching based on time, context, etc.
    setInterval(() => {
      if (this.adaptiveColorsSubject.value) {
        const timeBasedMood = this.getTimeBasedMoodId();
        this.setMood(timeBasedMood);
      }
    }, 30 * 60 * 1000); // Check every 30 minutes
  }

  private disableAdaptiveMode(): void {
    // Disable automatic switching - implementation would track intervals
  }

  private getTimeBasedMoodId(): string {
    const hour = new Date().getHours();
    
    if (hour >= 6 && hour < 12) return 'energetic';
    if (hour >= 12 && hour < 17) return 'sophisticated';
    if (hour >= 17 && hour < 20) return 'romantic';
    return 'contemplative';
  }

  private generateAccentColor(primary: string, secondary: string): string {
    // Simplified accent generation - would use color theory in real implementation
    return 'var(--trust-ocean-600)';
  }

  private generateGradientBackground(primary: string, secondary: string): string {
    return `linear-gradient(135deg, ${primary}22 0%, ${secondary}22 100%)`;
  }

  private generateShadow(color: string, intensity: string): string {
    const intensityMap = {
      subtle: 'soft',
      moderate: 'soft',
      strong: 'medium',
      intense: 'strong'
    };
    
    return `var(--shadow-emotional-${intensityMap[intensity as keyof typeof intensityMap]})`;
  }

  private generateGlow(color: string, intensity: string): string {
    // Simplified glow generation
    return 'rgba(255, 107, 157, 0.3)';
  }
}