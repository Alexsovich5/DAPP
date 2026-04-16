import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { Message, MessageService } from '../../core/services/message.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';

interface ConnectionInfo {
  id: number;
  partner_id: number;
  partner_name: string;
  compatibility_score: number;
  connection_stage: string;
  current_day: number;
  is_online: boolean;
  last_seen?: string;
}

interface TypingIndicator {
  connection_id: number;
  user_id: number;
  user_name: string;
  is_typing: boolean;
  started_at: string;
}

@Component({
  selector: 'app-messaging',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatIconModule,
    MatProgressSpinnerModule,
    ScrollingModule
  ],
  templateUrl: './messaging.component.html',
  styleUrls: ['./messaging.component.scss']
})
export class MessagingComponent implements OnInit, OnDestroy {
  @ViewChild('messagesContainer') messagesContainer?: ElementRef;
  @ViewChild('messageInput') messageInput?: ElementRef;

  connectionId = 0;
  messages: Message[] = [];
  connectionInfo?: ConnectionInfo;
  isLoading = true;
  connectionNotFound = false;
  isMobile = false;
  highContrastMode = false;
  showNotificationHistory = false;

  messageControl = new FormControl('');
  typingIndicators: TypingIndicator[] = [];
  partnerTyping = false;
  currentUserId = 0;

  replyingTo?: Message;
  editingMessageId?: number;
  showEmojiPicker = false;
  showQuickResponses = false;
  showConnectionInsights = false;
  currentEmotionalTone = '';
  currentPage = 1;
  messagesPerPage = 50;

  private subscriptions = new Subscription();
  private typingTimeout?: ReturnType<typeof setTimeout>;
  private readonly CHARACTER_LIMIT = 2000;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly messageService: MessageService,
    private readonly webSocketService: WebSocketService,
    private readonly soulConnectionService: SoulConnectionService,
    private readonly authService: AuthService,
    private readonly notificationService: NotificationService
  ) {
    this.isMobile = window.innerWidth <= 768;
  }

  ngOnInit(): void {
    this.subscriptions.add(
      this.route.params.subscribe(params => {
        this.connectionId = +params['connectionId'];
        this.loadConnectionData();
      })
    );

    this.subscriptions.add(
      this.authService.currentUser$.subscribe(user => {
        if (user) {
          this.currentUserId = user.id;
        }
      })
    );

    this.subscriptions.add(
      this.messageControl.valueChanges.pipe(
        debounceTime(500),
        distinctUntilChanged()
      ).subscribe(() => {
        this.handleTypingIndicator();
      })
    );

    // TODO: Pass token to connect when authentication is implemented
    // this.webSocketService.connect();
    // this.subscribeToWebSocketMessages();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    if (this.typingTimeout) {
      clearTimeout(this.typingTimeout);
    }
  }

  private loadConnectionData(): void {
    this.isLoading = true;

    // TODO: Implement getConnectionInfo method in SoulConnectionService
    this.connectionNotFound = false;
    this.isLoading = false;
    // this.subscriptions.add(
    //   this.soulConnectionService.getConnectionInfo(this.connectionId).subscribe({
    //     next: (info: ConnectionInfo) => {
    //       this.connectionInfo = info;
    //       this.loadMessages();
    //     },
    //     error: () => {
    //       this.connectionNotFound = true;
    //       this.isLoading = false;
    //       this.notificationService.showError(
    //         'Connection not found or you don\'t have access to it.'
    //       );
    //     }
    //   })
    // );
  }

  private loadMessages(): void {
    this.subscriptions.add(
      this.messageService.getMessages(this.connectionId).subscribe({
        next: (messages) => {
          this.messages = messages;
          this.isLoading = false;
          setTimeout(() => this.scrollToBottom(), 100);
          this.markVisibleMessagesAsRead();
        },
        error: () => {
          this.isLoading = false;
          this.notificationService.showError('Failed to load messages');
        }
      })
    );
  }

  private subscribeToWebSocketMessages(): void {
    // TODO: Implement onMessage and onTypingIndicator methods in WebSocketService
    // this.subscriptions.add(
    //   this.webSocketService.onMessage().subscribe((data: any) => {
    //     if (data.type === 'new_message' && data.message) {
    //       this.handleNewMessage(data.message);
    //     }
    //   })
    // );

    // this.subscriptions.add(
    //   this.webSocketService.onTypingIndicator().subscribe((indicator: TypingIndicator) => {
    //     if (indicator.connection_id === this.connectionId) {
    //       this.handleTypingIndicatorUpdate(indicator);
    //     }
    //   })
    // );
  }

  handleNewMessage(message: Message): void {
    if (message.connection_id === this.connectionId) {
      this.messages.push(message);
      setTimeout(() => this.scrollToBottom(), 50);
      if (!message.is_own_message) {
        this.markVisibleMessagesAsRead();
      }
    }
  }

  private handleTypingIndicatorUpdate(indicator: TypingIndicator): void {
    if (indicator.user_id !== this.currentUserId) {
      this.partnerTyping = indicator.is_typing;
      if (this.partnerTyping) {
        setTimeout(() => {
          this.partnerTyping = false;
        }, 3000);
      }
    }
  }

  private handleTypingIndicator(): void {
    const value = this.messageControl.value;
    if (value && value.trim()) {
      // TODO: Implement sendTypingIndicator and stopTypingIndicator methods in WebSocketService
      // this.webSocketService.sendTypingIndicator(this.connectionId, true);

      if (this.typingTimeout) {
        clearTimeout(this.typingTimeout);
      }

      this.typingTimeout = setTimeout(() => {
        // this.webSocketService.stopTypingIndicator(this.connectionId);
      }, 3000);
    }
  }

  sendMessage(messageText?: string): void {
    const text = messageText || this.messageControl.value?.trim();
    if (!text || this.isMessageTooLong()) {
      return;
    }

    const messageType = this.replyingTo ? 'text' : 'text';

    this.messageService.sendMessage(this.connectionId, text, messageType).subscribe({
      next: () => {
        this.messageControl.setValue('');
        this.replyingTo = undefined;
        this.notificationService.showSuccess('Message sent successfully');
        // TODO: Implement stopTypingIndicator method in WebSocketService
        // this.webSocketService.stopTypingIndicator(this.connectionId);
      },
      error: (error) => {
        this.notificationService.showError(
          `Failed to send message: ${error.error?.detail || 'Unknown error'}`
        );
      }
    });
  }

  isMessageTooLong(): boolean {
    const text = this.messageControl.value || '';
    return text.length > this.CHARACTER_LIMIT;
  }

  markVisibleMessagesAsRead(): void {
    const unreadMessageIds = this.messages
      .filter(m => !m.is_read && !m.is_own_message)
      .map(m => m.id);

    if (unreadMessageIds.length > 0) {
      this.messageService.markAsRead(unreadMessageIds).subscribe();
    }
  }

  insertEmoji(emoji: string): void {
    const currentValue = this.messageControl.value || '';
    this.messageControl.setValue(currentValue + emoji);
    this.showEmojiPicker = false;
  }

  copyMessageText(message: Message): void {
    navigator.clipboard.writeText(message.message_text).then(() => {
      this.notificationService.showSuccess('Message copied to clipboard');
    });
  }

  trackByMessageId(index: number, message: Message): number {
    return message.id;
  }

  scrollToBottom(): void {
    if (this.messagesContainer) {
      const container = this.messagesContainer.nativeElement;
      container.scrollTop = container.scrollHeight;
    }
  }

  analyzeEmotionalTone(text: string): void {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('grateful') || lowerText.includes('thank')) {
      this.currentEmotionalTone = 'grateful';
    } else if (lowerText.includes('appreciate') || lowerText.includes('value')) {
      this.currentEmotionalTone = 'appreciative';
    } else if (lowerText.includes('excited') || lowerText.includes('happy')) {
      this.currentEmotionalTone = 'joyful';
    } else {
      this.currentEmotionalTone = '';
    }
  }

  toggleHighContrast(): void {
    this.highContrastMode = !this.highContrastMode;
  }

  loadNextPage(): void {
    this.currentPage++;
  }

  showMessageActions(_message: Message): void {
    // Implementation for mobile swipe actions
  }

  adjustForVirtualKeyboard(): void {
    // Implementation for mobile keyboard adjustment
  }

  downloadAsFile(): void {
    const data = JSON.stringify(this.messages, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `messages-${this.connectionId}.json`;
    link.click();
  }
}
