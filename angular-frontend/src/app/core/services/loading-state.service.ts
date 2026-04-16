import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface LoadingState {
  key: string;
  isLoading: boolean;
  message?: string;
  error?: string;
  progress?: number; // 0-100 for progress indicators
}

@Injectable({
  providedIn: 'root'
})
export class LoadingStateService {
  private loadingStates = new BehaviorSubject<Map<string, LoadingState>>(new Map());

  /**
   * Get all loading states as an observable
   */
  get loadingStates$(): Observable<Map<string, LoadingState>> {
    return this.loadingStates.asObservable();
  }

  /**
   * Get a specific loading state by key
   */
  getLoadingState$(key: string): Observable<LoadingState | undefined> {
    return this.loadingStates$.pipe(
      map(states => states.get(key))
    );
  }

  /**
   * Check if any loading state is active
   */
  get isAnyLoading$(): Observable<boolean> {
    return this.loadingStates$.pipe(
      map(states => Array.from(states.values()).some(state => state.isLoading))
    );
  }

  /**
   * Get count of active loading states
   */
  get activeLoadingCount$(): Observable<number> {
    return this.loadingStates$.pipe(
      map(states => Array.from(states.values()).filter(state => state.isLoading).length)
    );
  }

  /**
   * Check if a specific key is loading
   */
  isLoading$(key: string): Observable<boolean> {
    return this.getLoadingState$(key).pipe(
      map(state => state?.isLoading ?? false)
    );
  }

  /**
   * Get loading message for a specific key
   */
  getLoadingMessage$(key: string): Observable<string | undefined> {
    return this.getLoadingState$(key).pipe(
      map(state => state?.message)
    );
  }

  /**
   * Get error message for a specific key
   */
  getError$(key: string): Observable<string | undefined> {
    return this.getLoadingState$(key).pipe(
      map(state => state?.error)
    );
  }

  /**
   * Get progress for a specific key
   */
  getProgress$(key: string): Observable<number | undefined> {
    return this.getLoadingState$(key).pipe(
      map(state => state?.progress)
    );
  }

  /**
   * Start loading for a specific key
   */
  startLoading(key: string, message?: string): void {
    const currentStates = this.loadingStates.value;
    const newStates = new Map(currentStates);

    newStates.set(key, {
      key,
      isLoading: true,
      message,
      error: undefined,
      progress: undefined
    });

    this.loadingStates.next(newStates);
  }

  /**
   * Stop loading for a specific key
   */
  stopLoading(key: string): void {
    const currentStates = this.loadingStates.value;
    const newStates = new Map(currentStates);

    const existingState = newStates.get(key);
    if (existingState) {
      newStates.set(key, {
        ...existingState,
        isLoading: false,
        message: undefined,
        progress: undefined
      });
    }

    this.loadingStates.next(newStates);
  }

  /**
   * Set error for a specific key
   */
  setError(key: string, error: string): void {
    const currentStates = this.loadingStates.value;
    const newStates = new Map(currentStates);

    const existingState = newStates.get(key);
    newStates.set(key, {
      key,
      isLoading: false,
      message: undefined,
      error,
      progress: undefined,
      ...existingState
    });

    this.loadingStates.next(newStates);
  }

  /**
   * Update progress for a specific key
   */
  updateProgress(key: string, progress: number, message?: string): void {
    const currentStates = this.loadingStates.value;
    const newStates = new Map(currentStates);

    const existingState = newStates.get(key);
    if (existingState && existingState.isLoading) {
      newStates.set(key, {
        ...existingState,
        progress: Math.max(0, Math.min(100, progress)),
        message: message || existingState.message
      });

      this.loadingStates.next(newStates);
    }
  }

  /**
   * Update loading message for a specific key
   */
  updateMessage(key: string, message: string): void {
    const currentStates = this.loadingStates.value;
    const newStates = new Map(currentStates);

    const existingState = newStates.get(key);
    if (existingState && existingState.isLoading) {
      newStates.set(key, {
        ...existingState,
        message
      });

      this.loadingStates.next(newStates);
    }
  }

  /**
   * Clear a specific loading state completely
   */
  clearLoadingState(key: string): void {
    const currentStates = this.loadingStates.value;
    const newStates = new Map(currentStates);

    newStates.delete(key);
    this.loadingStates.next(newStates);
  }

  /**
   * Clear all loading states
   */
  clearAllLoadingStates(): void {
    this.loadingStates.next(new Map());
  }

  /**
   * Get all loading states for debugging
   */
  getAllLoadingStates(): LoadingState[] {
    return Array.from(this.loadingStates.value.values());
  }

  /**
   * Predefined loading keys for consistency across the app
   */
  static readonly LOADING_KEYS = {
    // Discovery and matching
    DISCOVER_SOULS: 'discover-souls',
    COMPATIBILITY_ANALYSIS: 'compatibility-analysis',
    SOUL_CONNECTION: 'soul-connection',

    // Profile and onboarding
    PROFILE_LOADING: 'profile-loading',
    ONBOARDING_PROGRESS: 'onboarding-progress',
    EMOTIONAL_ASSESSMENT: 'emotional-assessment',

    // Messaging and communication
    SENDING_MESSAGE: 'sending-message',
    LOADING_MESSAGES: 'loading-messages',
    TYPING_INDICATOR: 'typing-indicator',

    // Revelations
    LOADING_REVELATIONS: 'loading-revelations',
    SENDING_REVELATION: 'sending-revelation',
    PHOTO_REVEAL: 'photo-reveal',

    // Data operations
    SAVING_PREFERENCES: 'saving-preferences',
    UPDATING_PROFILE: 'updating-profile',
    FETCHING_DATA: 'fetching-data',

    // Real-time features
    WEBSOCKET_CONNECTING: 'websocket-connecting',
    SYNCING_DATA: 'syncing-data'
  } as const;

  /**
   * Predefined loading messages for soul-specific features
   */
  static readonly LOADING_MESSAGES = {
    [LoadingStateService.LOADING_KEYS.DISCOVER_SOULS]: 'Discovering kindred souls...',
    [LoadingStateService.LOADING_KEYS.COMPATIBILITY_ANALYSIS]: 'Analyzing soul compatibility...',
    [LoadingStateService.LOADING_KEYS.SOUL_CONNECTION]: 'Establishing soul connection...',
    [LoadingStateService.LOADING_KEYS.PROFILE_LOADING]: 'Loading soul profile...',
    [LoadingStateService.LOADING_KEYS.ONBOARDING_PROGRESS]: 'Mapping your soul journey...',
    [LoadingStateService.LOADING_KEYS.EMOTIONAL_ASSESSMENT]: 'Assessing emotional depth...',
    [LoadingStateService.LOADING_KEYS.SENDING_MESSAGE]: 'Sending soul message...',
    [LoadingStateService.LOADING_KEYS.LOADING_MESSAGES]: 'Loading conversation history...',
    [LoadingStateService.LOADING_KEYS.TYPING_INDICATOR]: 'User is typing...',
    [LoadingStateService.LOADING_KEYS.LOADING_REVELATIONS]: 'Loading daily revelations...',
    [LoadingStateService.LOADING_KEYS.SENDING_REVELATION]: 'Sharing your revelation...',
    [LoadingStateService.LOADING_KEYS.PHOTO_REVEAL]: 'Preparing photo revelation...',
    [LoadingStateService.LOADING_KEYS.SAVING_PREFERENCES]: 'Saving soul preferences...',
    [LoadingStateService.LOADING_KEYS.UPDATING_PROFILE]: 'Updating soul profile...',
    [LoadingStateService.LOADING_KEYS.FETCHING_DATA]: 'Fetching soul data...',
    [LoadingStateService.LOADING_KEYS.WEBSOCKET_CONNECTING]: 'Connecting to soul network...',
    [LoadingStateService.LOADING_KEYS.SYNCING_DATA]: 'Syncing soul data...'
  } as const;

  /**
   * Helper method to start loading with predefined message
   */
  startPredefinedLoading(key: keyof typeof LoadingStateService.LOADING_KEYS): void {
    const loadingKey = LoadingStateService.LOADING_KEYS[key];
    const message = LoadingStateService.LOADING_MESSAGES[loadingKey];
    this.startLoading(loadingKey, message);
  }

  /**
   * Helper method to stop predefined loading
   */
  stopPredefinedLoading(key: keyof typeof LoadingStateService.LOADING_KEYS): void {
    const loadingKey = LoadingStateService.LOADING_KEYS[key];
    this.stopLoading(loadingKey);
  }

  /**
   * Helper method to check if predefined loading is active
   */
  isPredefinedLoading$(key: keyof typeof LoadingStateService.LOADING_KEYS): Observable<boolean> {
    const loadingKey = LoadingStateService.LOADING_KEYS[key];
    return this.isLoading$(loadingKey);
  }
}
