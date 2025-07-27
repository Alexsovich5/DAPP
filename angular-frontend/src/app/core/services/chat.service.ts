import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, BehaviorSubject, timer } from 'rxjs';
import { environment } from '../../../environments/environment';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { map, tap, debounceTime, distinctUntilChanged } from 'rxjs/operators';

interface Message {
  id: string;
  senderId: string;
  content: string;
  timestamp: string;
  isRead: boolean;
}

interface ChatUser {
  _id: string;
  firstName: string;
  lastName: string;
  profilePicture?: string;
  lastActive?: string;
}

interface ChatData {
  user: ChatUser;
  messages: Message[];
}

export interface TypingUser {
  id: string;
  name: string;
  avatar?: string;
  connectionStage?: 'soul_discovery' | 'revelation_sharing' | 'photo_reveal' | 'deeper_connection';
  emotionalState?: 'contemplative' | 'romantic' | 'energetic' | 'peaceful' | 'sophisticated';
  compatibilityScore?: number;
  lastActivity?: Date;
  connectionEnergy?: 'low' | 'medium' | 'high' | 'soulmate';
}

interface TypingIndicator {
  userId: string;
  isTyping: boolean;
  timestamp: number;
}

interface WebSocketMessage {
  type: 'message' | 'typing_start' | 'typing_stop' | 'online_users' | 'user_status';
  data: any;
  userId?: string;
  timestamp?: number;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private socket$!: WebSocketSubject<any>;
  private messageSubject = new Subject<Message>();
  private onlineUsers = new BehaviorSubject<string[]>([]);
  
  // Typing indicator management
  private typingUsers = new BehaviorSubject<Map<string, TypingUser>>(new Map());
  private typingSubject = new Subject<TypingIndicator>();
  private typingTimer = new Map<string, NodeJS.Timeout>();
  private currentUserId: string | null = null;
  
  // Typing detection
  private lastTypingTime = 0;
  private typingTimeout = 3000; // 3 seconds
  private isCurrentlyTyping = false;
  
  // Connection activity tracking
  private connectionActivity = new BehaviorSubject<Map<string, any>>(new Map());
  private emotionalStates = new BehaviorSubject<Map<string, string>>(new Map());

  constructor(private http: HttpClient) {
    this.setupWebSocket();
    this.setupTypingCleanup();
  }

  private setupWebSocket(): void {
    // In a real app, this would be your WebSocket server URL
    this.socket$ = webSocket(`${environment.socketUrl}/chat`);

    this.socket$.subscribe({
      next: (message) => this.handleWebSocketMessage(message),
      error: (err) => console.error('WebSocket error:', err)
    });
  }

  private handleWebSocketMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'message':
        this.messageSubject.next(message.data);
        // Stop typing indicator for sender when message is received
        if (message.userId) {
          this.handleTypingStop(message.userId);
        }
        break;
        
      case 'typing_start':
        if (message.userId && message.data) {
          this.handleTypingStart(message.userId, message.data);
        }
        break;
        
      case 'typing_stop':
        if (message.userId) {
          this.handleTypingStop(message.userId);
        }
        break;
        
      case 'online_users':
        this.onlineUsers.next(message.data);
        break;
        
      case 'user_status':
        // Handle user online/offline status changes
        if (message.data) {
          this.updateUserStatus(message.data);
        }
        break;
    }
  }

  private setupTypingCleanup(): void {
    // Clean up stale typing indicators every 30 seconds
    timer(0, 30000).subscribe(() => {
      this.cleanupStaleTypingIndicators();
    });
  }

  private handleTypingStart(userId: string, userData: TypingUser): void {
    // Don't show typing indicator for current user
    if (userId === this.currentUserId) return;

    const currentTyping = this.typingUsers.value;
    currentTyping.set(userId, userData);
    this.typingUsers.next(new Map(currentTyping));

    // Clear existing timer
    if (this.typingTimer.has(userId)) {
      clearTimeout(this.typingTimer.get(userId)!);
    }

    // Set auto-cleanup timer
    const timer = setTimeout(() => {
      this.handleTypingStop(userId);
    }, this.typingTimeout);
    
    this.typingTimer.set(userId, timer);
  }

  private handleTypingStop(userId: string): void {
    const currentTyping = this.typingUsers.value;
    if (currentTyping.has(userId)) {
      currentTyping.delete(userId);
      this.typingUsers.next(new Map(currentTyping));
    }

    // Clear timer
    if (this.typingTimer.has(userId)) {
      clearTimeout(this.typingTimer.get(userId)!);
      this.typingTimer.delete(userId);
    }
  }

  private cleanupStaleTypingIndicators(): void {
    const now = Date.now();
    const currentTyping = this.typingUsers.value;
    let hasChanges = false;

    currentTyping.forEach((user, userId) => {
      // Remove indicators older than timeout
      if (this.typingTimer.has(userId)) {
        const timer = this.typingTimer.get(userId)!;
        // Check if timer is still valid (simplified check)
        if (now - this.lastTypingTime > this.typingTimeout * 2) {
          this.handleTypingStop(userId);
          hasChanges = true;
        }
      }
    });

    if (hasChanges) {
      this.typingUsers.next(new Map(currentTyping));
    }
  }

  private updateUserStatus(statusData: any): void {
    // Handle user status updates (online/offline)
    // This could update online users or typing indicators
    if (statusData.type === 'online' && statusData.users) {
      this.onlineUsers.next(statusData.users);
    }
  }

  getChatData(userId: string): Observable<ChatData> {
    return this.http.get<ChatData>(`${environment.apiUrl}/chat/${userId}`).pipe(
      tap(data => {
        // Mark messages as read when loading chat
        if (data.messages.length > 0) {
          this.markMessagesAsRead(userId);
        }
      })
    );
  }

  sendMessage(userId: string, content: string): Observable<Message> {
    const message = {
      receiverId: userId,
      content,
      timestamp: new Date().toISOString()
    };

    return this.http.post<Message>(`${environment.apiUrl}/chat/send`, message);
  }

  markMessagesAsRead(userId: string): Observable<void> {
    return this.http.post<void>(`${environment.apiUrl}/chat/${userId}/read`, {});
  }

  getNewMessages(): Observable<Message> {
    return this.messageSubject.asObservable();
  }

  getOnlineUsers(): Observable<string[]> {
    return this.onlineUsers.asObservable();
  }

  disconnect(): void {
    // Clean up typing timers
    this.typingTimer.forEach(timer => clearTimeout(timer));
    this.typingTimer.clear();
    
    if (this.socket$) {
      this.socket$.complete();
    }
  }

  // === TYPING INDICATOR METHODS ===

  /**
   * Set current user ID for filtering own typing indicators
   */
  setCurrentUserId(userId: string): void {
    this.currentUserId = userId;
  }

  /**
   * Get observable of currently typing users
   */
  getTypingUsers(): Observable<TypingUser[]> {
    return this.typingUsers.asObservable().pipe(
      map(typingMap => Array.from(typingMap.values())),
      distinctUntilChanged((a, b) => 
        a.length === b.length && 
        a.every((user, index) => user.id === b[index]?.id)
      )
    );
  }

  /**
   * Get typing users for specific chat/conversation
   */
  getTypingUsersForChat(chatId: string): Observable<TypingUser[]> {
    return this.getTypingUsers().pipe(
      // In a real implementation, you'd filter by chatId
      // For now, return all typing users
      map(users => users)
    );
  }

  /**
   * Indicate that current user started typing
   */
  startTyping(chatId: string, userData: TypingUser): void {
    if (!this.isCurrentlyTyping) {
      this.isCurrentlyTyping = true;
      this.lastTypingTime = Date.now();
      
      // Send typing start event via WebSocket
      if (this.socket$ && !this.socket$.closed) {
        this.socket$.next({
          type: 'typing_start',
          chatId,
          data: userData,
          timestamp: this.lastTypingTime
        });
      }
    }
  }

  /**
   * Indicate that current user stopped typing
   */
  stopTyping(chatId: string): void {
    if (this.isCurrentlyTyping) {
      this.isCurrentlyTyping = false;
      
      // Send typing stop event via WebSocket
      if (this.socket$ && !this.socket$.closed) {
        this.socket$.next({
          type: 'typing_stop',
          chatId,
          timestamp: Date.now()
        });
      }
    }
  }

  /**
   * Handle typing detection from input changes
   * Should be called with debounced input changes
   */
  handleTypingInput(chatId: string, userData: TypingUser, isTyping: boolean): void {
    const now = Date.now();
    
    if (isTyping) {
      // User is actively typing
      if (!this.isCurrentlyTyping || (now - this.lastTypingTime) > 1000) {
        this.startTyping(chatId, userData);
      }
      this.lastTypingTime = now;
    } else {
      // User stopped typing
      if (this.isCurrentlyTyping && (now - this.lastTypingTime) > this.typingTimeout) {
        this.stopTyping(chatId);
      }
    }
  }

  /**
   * Create typing input handler for form controls
   * Returns a debounced function for input events
   */
  createTypingHandler(chatId: string, userData: TypingUser): (inputValue: string) => void {
    let typingSubject = new Subject<string>();
    
    // Debounce input to detect typing start/stop
    typingSubject.pipe(
      debounceTime(300),
      distinctUntilChanged()
    ).subscribe(value => {
      const isTyping = value.length > 0;
      this.handleTypingInput(chatId, userData, isTyping);
      
      // Auto-stop typing after timeout
      if (isTyping) {
        setTimeout(() => {
          if (Date.now() - this.lastTypingTime >= this.typingTimeout) {
            this.stopTyping(chatId);
          }
        }, this.typingTimeout);
      }
    });

    return (inputValue: string) => {
      typingSubject.next(inputValue);
    };
  }

  /**
   * Get current typing status
   */
  isUserTyping(): boolean {
    return this.isCurrentlyTyping;
  }

  /**
   * Force stop all typing indicators (useful for cleanup)
   */
  clearAllTypingIndicators(): void {
    const currentTyping = this.typingUsers.value;
    if (currentTyping.size > 0) {
      currentTyping.clear();
      this.typingUsers.next(new Map(currentTyping));
    }
    
    this.typingTimer.forEach(timer => clearTimeout(timer));
    this.typingTimer.clear();
    this.isCurrentlyTyping = false;
  }

  // === CONNECTION ACTIVITY & EMOTIONAL STATE METHODS ===

  /**
   * Update connection activity status for a user
   */
  updateConnectionActivity(userId: string, activity: {
    connectionStage?: string;
    compatibilityScore?: number;
    lastActivity?: Date;
    connectionEnergy?: string;
  }): void {
    const currentActivity = this.connectionActivity.value;
    currentActivity.set(userId, {
      ...currentActivity.get(userId),
      ...activity,
      lastUpdated: new Date()
    });
    this.connectionActivity.next(new Map(currentActivity));
  }

  /**
   * Set emotional state for a user
   */
  setEmotionalState(userId: string, emotionalState: string): void {
    const currentStates = this.emotionalStates.value;
    currentStates.set(userId, emotionalState);
    this.emotionalStates.next(new Map(currentStates));
  }

  /**
   * Get connection activity observable
   */
  getConnectionActivity(): Observable<Map<string, any>> {
    return this.connectionActivity.asObservable();
  }

  /**
   * Get emotional states observable
   */
  getEmotionalStates(): Observable<Map<string, string>> {
    return this.emotionalStates.asObservable();
  }

  /**
   * Enhanced typing users with connection context
   */
  getEnhancedTypingUsers(): Observable<TypingUser[]> {
    return this.typingUsers.asObservable().pipe(
      map(typingMap => {
        const activity = this.connectionActivity.value;
        const emotions = this.emotionalStates.value;
        
        return Array.from(typingMap.values()).map(user => ({
          ...user,
          connectionStage: activity.get(user.id)?.connectionStage,
          compatibilityScore: activity.get(user.id)?.compatibilityScore,
          lastActivity: activity.get(user.id)?.lastActivity,
          connectionEnergy: activity.get(user.id)?.connectionEnergy,
          emotionalState: emotions.get(user.id)
        }));
      }),
      distinctUntilChanged((a, b) => 
        a.length === b.length && 
        a.every((user, index) => 
          user.id === b[index]?.id && 
          user.emotionalState === b[index]?.emotionalState
        )
      )
    );
  }

  /**
   * Calculate connection energy based on activity
   */
  calculateConnectionEnergy(compatibilityScore: number, lastActivity: Date): string {
    const hoursSinceActivity = (Date.now() - lastActivity.getTime()) / (1000 * 60 * 60);
    
    if (compatibilityScore >= 90 && hoursSinceActivity < 1) return 'soulmate';
    if (compatibilityScore >= 80 && hoursSinceActivity < 2) return 'high';
    if (compatibilityScore >= 65 && hoursSinceActivity < 6) return 'medium';
    return 'low';
  }

  /**
   * Send emotional state update via WebSocket
   */
  broadcastEmotionalState(chatId: string, emotionalState: string): void {
    if (this.socket$ && !this.socket$.closed) {
      this.socket$.next({
        type: 'emotional_state_update',
        chatId,
        data: {
          userId: this.currentUserId,
          emotionalState,
          timestamp: Date.now()
        }
      });
    }
  }
}
