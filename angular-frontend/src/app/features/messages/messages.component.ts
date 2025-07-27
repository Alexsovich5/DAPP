import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { ChatService } from '../../core/services/chat.service';
import { HapticFeedbackService } from '../../core/services/haptic-feedback.service';
import { ConversationsEmptyStateComponent } from './conversations-empty-state.component';
import { SwipeDirective } from '../../shared/directives/swipe.directive';
import { SwipeEvent, SwipeConfig } from '../../core/services/swipe-gesture.service';
import { Subscription } from 'rxjs';

interface MessagePreview {
  connectionId: number;
  partnerName: string;
  partnerAvatar?: string;
  lastMessage: string;
  lastMessageTime: Date;
  unreadCount: number;
  connectionStage: string;
  revelationDay: number;
  compatibilityScore: number | undefined;
  isOnline?: boolean;
  isTyping?: boolean; // Added typing indicator support
}

@Component({
  selector: 'app-messages',
  standalone: true,
  imports: [CommonModule, ConversationsEmptyStateComponent, SwipeDirective],
  template: `
    <div class="messages-container">
      <header class="messages-header">
        <h1>Messages</h1>
        <div class="header-actions">
          <button class="filter-btn" [class.active]="filter === 'all'" (click)="setFilter('all')">
            All
          </button>
          <button class="filter-btn" [class.active]="filter === 'unread'" (click)="setFilter('unread')">
            Unread ({{totalUnread}})
          </button>
          <button class="filter-btn" [class.active]="filter === 'revealing'" (click)="setFilter('revealing')">
            Revealing
          </button>
        </div>
      </header>

      <div class="messages-stats" *ngIf="messagesPreviews.length > 0">
        <div class="stat-item">
          <span class="stat-number">{{activeChats}}</span>
          <span class="stat-label">Active Chats</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{totalUnread}}</span>
          <span class="stat-label">Unread</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{revelingConnections}}</span>
          <span class="stat-label">In Revelation</span>
        </div>
      </div>

      <div class="messages-list" *ngIf="filteredMessages.length > 0; else noMessages">
        <div 
          *ngFor="let message of filteredMessages" 
          class="message-item conversation-item"
          [class.unread]="message.unreadCount > 0"
          [class.revealing]="message.revelationDay > 1 && message.revelationDay <= 7"
          appSwipe
          [swipeConfig]="getConversationSwipeConfig()"
          [swipeEnabled]="true"
          (swipeLeft)="onSwipeLeft(message, $event)"
          (swipeRight)="onSwipeRight(message, $event)"
          (click)="openChat(message)"
        >
          <div class="message-avatar">
            <div class="avatar-circle" [class.online]="message.isOnline">
              <span>{{message.partnerName.charAt(0)}}</span>
            </div>
            <div class="revelation-indicator" *ngIf="message.revelationDay > 1 && message.revelationDay <= 7">
              <span class="day-badge">Day {{message.revelationDay}}</span>
            </div>
          </div>

          <div class="message-content">
            <div class="message-header">
              <h3 class="partner-name">{{message.partnerName}}</h3>
              <span class="compatibility-score">{{message.compatibilityScore}}% match</span>
            </div>
            
            <div class="message-preview">
              <p class="last-message" [class.typing-message]="message.isTyping">
                <span *ngIf="!message.isTyping">{{message.lastMessage}}</span>
                <span *ngIf="message.isTyping" class="typing-indicator-text">
                  <span class="typing-dots">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </span>
                  soul is connecting...
                </span>
              </p>
              <span class="connection-stage">{{formatConnectionStage(message.connectionStage)}}</span>
            </div>
            
            <div class="message-meta">
              <span class="timestamp">{{formatTime(message.lastMessageTime)}}</span>
              <div class="message-indicators">
                <span class="unread-badge" *ngIf="message.unreadCount > 0">
                  {{message.unreadCount}}
                </span>
                <span class="revelation-badge" *ngIf="message.revelationDay === 7">
                  ✨ Photo Day!
                </span>
              </div>
            </div>
          </div>

          <div class="message-actions">
            <button class="action-btn" (click)="quickReply(message, $event)" title="Quick Reply">
              💬
            </button>
            <button 
              class="action-btn revelation" 
              (click)="viewRevelations(message, $event)"
              *ngIf="message.revelationDay > 1"
              title="View Revelations"
            >
              ✨
            </button>
            <button class="action-btn" (click)="toggleMute(message, $event)" title="Mute">
              🔔
            </button>
          </div>
        </div>
      </div>

      <ng-template #noMessages>
        <app-conversations-empty-state
          (discoverMatches)="goToDiscover()"
          (learnConversationTips)="showConversationTips()">
        </app-conversations-empty-state>
      </ng-template>

      <div class="floating-action">
        <button class="fab" (click)="newMessage()" title="New Message">
          <span>✍️</span>
        </button>
      </div>

      <div class="loading-spinner" *ngIf="loading">
        <div class="spinner"></div>
        <p>Loading messages...</p>
      </div>
    </div>
  `,
  styles: [`
    .messages-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 1rem;
      min-height: 100vh;
      position: relative;
    }

    .messages-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #e2e8f0;
    }

    .messages-header h1 {
      font-size: 2rem;
      font-weight: 600;
      color: #2d3748;
      margin: 0;
    }

    .header-actions {
      display: flex;
      gap: 0.5rem;
    }

    .filter-btn {
      padding: 0.5rem 1rem;
      border: 1px solid #e2e8f0;
      background: white;
      border-radius: 20px;
      color: #718096;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 0.9rem;
    }

    .filter-btn:hover {
      border-color: #667eea;
      color: #667eea;
    }

    .filter-btn.active {
      background: #667eea;
      border-color: #667eea;
      color: white;
    }

    .messages-stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      margin-bottom: 1.5rem;
    }

    .stat-item {
      background: white;
      padding: 1rem;
      border-radius: 12px;
      text-align: center;
      border: 1px solid #e2e8f0;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .stat-number {
      display: block;
      font-size: 1.5rem;
      font-weight: bold;
      color: #667eea;
      margin-bottom: 0.25rem;
    }

    .stat-label {
      font-size: 0.8rem;
      color: #718096;
    }

    .messages-list {
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    }

    .message-item {
      display: flex;
      align-items: center;
      padding: 1rem;
      border-bottom: 1px solid #f7fafc;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
    }

    .message-item:hover {
      background: #f7fafc;
    }

    .message-item:last-child {
      border-bottom: none;
    }

    .message-item.unread {
      background: linear-gradient(90deg, rgba(102, 126, 234, 0.03) 0%, rgba(102, 126, 234, 0.01) 100%);
      border-left: 4px solid #667eea;
    }

    .message-item.revealing {
      background: linear-gradient(90deg, rgba(255, 215, 0, 0.05) 0%, rgba(255, 215, 0, 0.01) 100%);
      border-left: 4px solid #ffd700;
    }

    .message-avatar {
      position: relative;
      margin-right: 1rem;
    }

    .avatar-circle {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: bold;
      font-size: 1.2rem;
      position: relative;
    }

    .avatar-circle.online::after {
      content: '';
      position: absolute;
      bottom: 2px;
      right: 2px;
      width: 12px;
      height: 12px;
      background: #48bb78;
      border: 2px solid white;
      border-radius: 50%;
    }

    .revelation-indicator {
      position: absolute;
      top: -5px;
      right: -5px;
    }

    .day-badge {
      background: #ffd700;
      color: #744210;
      font-size: 0.7rem;
      font-weight: bold;
      padding: 0.2rem 0.4rem;
      border-radius: 10px;
      white-space: nowrap;
    }

    .message-content {
      flex: 1;
      min-width: 0;
    }

    .message-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }

    .partner-name {
      font-size: 1.1rem;
      font-weight: 600;
      color: #2d3748;
      margin: 0;
    }

    .compatibility-score {
      font-size: 0.8rem;
      color: #48bb78;
      font-weight: 600;
    }

    .message-preview {
      margin-bottom: 0.5rem;
    }

    .last-message {
      color: #4a5568;
      margin: 0 0 0.25rem 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 0.95rem;

      &.typing-message {
        color: #667eea;
        font-style: italic;
      }
    }

    .typing-indicator-text {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #667eea;
      font-style: italic;
    }

    .typing-dots {
      display: flex;
      gap: 0.15rem;
      align-items: center;
    }

    .typing-dots .dot {
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background: #667eea;
      animation: typing-dot-bounce 1.4s ease-in-out infinite;
    }

    .typing-dots .dot:nth-child(1) {
      animation-delay: 0s;
    }

    .typing-dots .dot:nth-child(2) {
      animation-delay: 0.2s;
    }

    .typing-dots .dot:nth-child(3) {
      animation-delay: 0.4s;
    }

    @keyframes typing-dot-bounce {
      0%, 80%, 100% {
        transform: scale(1) translateY(0);
        opacity: 0.7;
      }
      40% {
        transform: scale(1.2) translateY(-2px);
        opacity: 1;
      }
    }

    .connection-stage {
      font-size: 0.8rem;
      color: #718096;
      font-style: italic;
    }

    .message-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .timestamp {
      font-size: 0.8rem;
      color: #a0aec0;
    }

    .message-indicators {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .unread-badge {
      background: #667eea;
      color: white;
      font-size: 0.7rem;
      font-weight: bold;
      padding: 0.2rem 0.5rem;
      border-radius: 10px;
      min-width: 18px;
      text-align: center;
    }

    .revelation-badge {
      background: #ffd700;
      color: #744210;
      font-size: 0.7rem;
      font-weight: bold;
      padding: 0.2rem 0.5rem;
      border-radius: 10px;
    }

    .message-actions {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-left: 1rem;
    }

    .action-btn {
      width: 32px;
      height: 32px;
      border: none;
      border-radius: 50%;
      background: #f7fafc;
      color: #718096;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.9rem;
    }

    .action-btn:hover {
      background: #edf2f7;
      transform: scale(1.05);
    }

    .action-btn.revelation {
      background: #fff5cd;
      color: #b7791f;
    }

    .action-btn.revelation:hover {
      background: #fef5e7;
    }

    .empty-state {
      text-align: center;
      padding: 4rem 2rem;
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }

    .empty-icon {
      font-size: 4rem;
      margin-bottom: 1rem;
    }

    .empty-state h2 {
      font-size: 1.5rem;
      font-weight: 600;
      color: #2d3748;
      margin-bottom: 0.5rem;
    }

    .empty-state p {
      color: #718096;
      margin-bottom: 2rem;
    }

    .cta-button {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }

    .cta-button:hover {
      transform: translateY(-1px);
    }

    .floating-action {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      z-index: 1000;
    }

    .fab {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
      cursor: pointer;
      transition: transform 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
    }

    .fab:hover {
      transform: scale(1.1);
    }

    .loading-spinner {
      text-align: center;
      padding: 2rem;
    }

    .spinner {
      width: 32px;
      height: 32px;
      border: 3px solid #e2e8f0;
      border-top: 3px solid #667eea;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 0 auto 1rem;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    @media (max-width: 768px) {
      .messages-container {
        padding: 0.5rem;
      }
      
      .messages-header {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
      }
      
      .header-actions {
        justify-content: center;
      }
      
      .messages-stats {
        grid-template-columns: 1fr;
      }
      
      .message-item {
        padding: 0.75rem;
      }
      
      .message-actions {
        flex-direction: row;
        gap: 0.25rem;
      }
      
      .floating-action {
        bottom: 1rem;
        right: 1rem;
      }
    }
  `]
})
export class MessagesComponent implements OnInit, OnDestroy {
  messagesPreviews: MessagePreview[] = [];
  filteredMessages: MessagePreview[] = [];
  filter: 'all' | 'unread' | 'revealing' = 'all';
  loading = true;
  
  private subscriptions = new Subscription();

  constructor(
    private soulConnectionService: SoulConnectionService,
    private chatService: ChatService,
    private hapticFeedbackService: HapticFeedbackService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadMessages();
    this.setupTypingIndicators();
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
  }

  loadMessages() {
    this.loading = true;
    
    // Get active connections and their latest messages
    this.soulConnectionService.getActiveConnections().subscribe({
      next: (connections) => {
        this.messagesPreviews = connections.map(connection => ({
          connectionId: connection.id,
          partnerName: this.getPartnerName(connection),
          lastMessage: this.getLastMessage(connection),
          lastMessageTime: new Date(connection.updated_at || connection.created_at),
          unreadCount: Math.floor(Math.random() * 3), // Mock unread count
          connectionStage: connection.connection_stage,
          revelationDay: connection.reveal_day,
          compatibilityScore: connection.compatibility_score,
          isOnline: Math.random() > 0.5, // Mock online status
          isTyping: false // Initialize typing status
        }));

        // Sort by last message time
        this.messagesPreviews.sort((a, b) => 
          b.lastMessageTime.getTime() - a.lastMessageTime.getTime()
        );

        this.applyFilter();
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading messages:', error);
        this.loading = false;
      }
    });
  }

  setFilter(filter: 'all' | 'unread' | 'revealing') {
    this.filter = filter;
    this.applyFilter();
  }

  applyFilter() {
    switch (this.filter) {
      case 'unread':
        this.filteredMessages = this.messagesPreviews.filter(m => m.unreadCount > 0);
        break;
      case 'revealing':
        this.filteredMessages = this.messagesPreviews.filter(m => 
          m.revelationDay > 1 && m.revelationDay <= 7
        );
        break;
      default:
        this.filteredMessages = this.messagesPreviews;
    }
  }

  get activeChats(): number {
    return this.messagesPreviews.length;
  }

  get totalUnread(): number {
    return this.messagesPreviews.reduce((sum, m) => sum + m.unreadCount, 0);
  }

  get revelingConnections(): number {
    return this.messagesPreviews.filter(m => 
      m.revelationDay > 1 && m.revelationDay <= 7
    ).length;
  }

  getPartnerName(connection: any): string {
    return connection.user2_profile?.first_name || 
           connection.user1_profile?.first_name || 
           'Soul Connection';
  }

  getLastMessage(connection: any): string {
    // Mock last message - in real app, fetch from messages API
    const mockMessages = [
      "Thanks for sharing that beautiful revelation...",
      "I'm excited to get to know you better 💫",
      "Your perspective on life is so refreshing",
      "Looking forward to our photo reveal day!",
      "What a meaningful conversation we had yesterday"
    ];
    return mockMessages[Math.floor(Math.random() * mockMessages.length)];
  }

  formatConnectionStage(stage: string): string {
    switch (stage) {
      case 'soul_discovery': return 'Soul Discovery';
      case 'revelation_sharing': return 'Sharing Revelations';
      case 'photo_reveal': return 'Photo Reveal';
      case 'deeper_connection': return 'Deeper Connection';
      default: return 'New Connection';
    }
  }

  formatTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = diff / (1000 * 60 * 60);
    
    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60));
      return `${minutes}m ago`;
    } else if (hours < 24) {
      return `${Math.floor(hours)}h ago`;
    } else {
      const days = Math.floor(hours / 24);
      return `${days}d ago`;
    }
  }


  quickReply(message: MessagePreview, event: Event) {
    event.stopPropagation();
    this.openChat(message);
  }

  viewRevelations(message: MessagePreview, event: Event) {
    event.stopPropagation();
    this.router.navigate(['/revelations'], {
      queryParams: { connectionId: message.connectionId }
    });
  }

  toggleMute(message: MessagePreview, event: Event) {
    event.stopPropagation();
    // Implement mute functionality
    console.log('Toggle mute for connection:', message.connectionId);
  }

  goToMatches() {
    this.router.navigate(['/matches']);
  }

  goToDiscover() {
    this.router.navigate(['/discover']);
  }

  showConversationTips() {
    // Navigate to a tips/help page or show modal
    this.router.navigate(['/help/conversations']);
  }

  newMessage() {
    this.router.navigate(['/discover']);
  }

  // === TYPING INDICATORS ===

  private setupTypingIndicators() {
    // Subscribe to typing users updates
    this.subscriptions.add(
      this.chatService.getTypingUsers().subscribe(typingUsers => {
        this.updateTypingStatus(typingUsers);
      })
    );
  }

  private updateTypingStatus(typingUsers: any[]) {
    // Update typing status for each message preview
    this.messagesPreviews.forEach(message => {
      const isTyping = typingUsers.some(user => 
        // In real implementation, you'd match by user ID or connection ID
        user.name === message.partnerName
      );
      
      if (message.isTyping !== isTyping) {
        message.isTyping = isTyping;
        
        // Update last message display when typing status changes
        if (isTyping) {
          // Store original message to restore later
          (message as any).originalLastMessage = message.lastMessage;
        } else {
          // Restore original message
          if ((message as any).originalLastMessage) {
            message.lastMessage = (message as any).originalLastMessage;
          }
        }
      }
    });

    // Re-apply filter to update display
    this.applyFilter();
  }

  // === SWIPE GESTURE HANDLERS ===

  getConversationSwipeConfig(): Partial<SwipeConfig> {
    return {
      threshold: 80, // Require 80px swipe for conversations
      velocityThreshold: 0.4,
      timeThreshold: 600,
      enabledDirections: ['left', 'right'],
      hapticFeedback: true,
      preventDefaultEvents: true
    };
  }

  onSwipeLeft(message: MessagePreview, event: SwipeEvent): void {
    // Swipe left to archive/delete conversation
    const element = event.element;
    element.classList.add('swipe-archive', 'swipe-left-preview');
    
    // Trigger haptic feedback
    this.hapticFeedbackService.triggerSelectionFeedback();
    
    // Show confirmation and archive
    setTimeout(() => {
      this.archiveConversation(message);
      element.classList.remove('swipe-archive', 'swipe-left-preview');
    }, 300);
  }

  onSwipeRight(message: MessagePreview, event: SwipeEvent): void {
    // Swipe right to mark as read/prioritize
    const element = event.element;
    element.classList.add('swipe-priority', 'swipe-right-preview');
    
    // Trigger haptic feedback
    this.hapticFeedbackService.triggerSuccessFeedback();
    
    // Mark as priority/read
    setTimeout(() => {
      this.prioritizeConversation(message);
      element.classList.remove('swipe-priority', 'swipe-right-preview');
    }, 300);
  }

  private archiveConversation(message: MessagePreview): void {
    // Remove from current list with animation
    const index = this.messagesPreviews.findIndex(m => m.connectionId === message.connectionId);
    if (index > -1) {
      this.messagesPreviews.splice(index, 1);
      this.applyFilter();
      
      // Announce action for accessibility
      this.announceAction(`Archived conversation with ${message.partnerName}`);
      
      // TODO: Call API to archive conversation
      console.log('Archived conversation:', message.connectionId);
    }
  }

  private prioritizeConversation(message: MessagePreview): void {
    // Mark as read and move to top
    message.unreadCount = 0;
    
    // Move to top of list
    const index = this.messagesPreviews.findIndex(m => m.connectionId === message.connectionId);
    if (index > -1) {
      const [prioritizedMessage] = this.messagesPreviews.splice(index, 1);
      this.messagesPreviews.unshift(prioritizedMessage);
      this.applyFilter();
      
      // Announce action for accessibility
      this.announceAction(`Prioritized conversation with ${message.partnerName}`);
      
      // TODO: Call API to mark as priority
      console.log('Prioritized conversation:', message.connectionId);
    }
  }

  private announceAction(message: string): void {
    // Create temporary element for screen reader announcement
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.position = 'absolute';
    announcement.style.left = '-9999px';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }

  // Enhanced openChat to stop typing indicators  
  openChat(message: MessagePreview) {
    // Stop typing indicator for this conversation
    this.chatService.clearAllTypingIndicators();
    
    this.router.navigate(['/chat'], {
      queryParams: { connectionId: message.connectionId }
    });
  }
}