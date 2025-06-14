import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { ChatService } from '../../core/services/chat.service';

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
}

@Component({
  selector: 'app-messages',
  standalone: true,
  imports: [CommonModule],
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
          class="message-item"
          [class.unread]="message.unreadCount > 0"
          [class.revealing]="message.revelationDay > 1 && message.revelationDay <= 7"
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
              <p class="last-message">{{message.lastMessage}}</p>
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
        <div class="empty-state">
          <div class="empty-icon">💌</div>
          <h2>No Messages Yet</h2>
          <p *ngIf="filter === 'all'">Start conversations with your soul connections</p>
          <p *ngIf="filter === 'unread'">No unread messages</p>
          <p *ngIf="filter === 'revealing'">No active revelation conversations</p>
          <button class="cta-button" (click)="goToMatches()" *ngIf="filter === 'all'">
            <span>💫</span> View Your Connections
          </button>
        </div>
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
export class MessagesComponent implements OnInit {
  messagesPreviews: MessagePreview[] = [];
  filteredMessages: MessagePreview[] = [];
  filter: 'all' | 'unread' | 'revealing' = 'all';
  loading = true;

  constructor(
    private soulConnectionService: SoulConnectionService,
    private chatService: ChatService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadMessages();
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
          isOnline: Math.random() > 0.5 // Mock online status
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

  openChat(message: MessagePreview) {
    this.router.navigate(['/chat'], {
      queryParams: { connectionId: message.connectionId }
    });
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

  newMessage() {
    this.router.navigate(['/discover']);
  }
}