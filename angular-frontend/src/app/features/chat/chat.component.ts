import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ChatService, TypingUser } from '../../core/services/chat.service';
import { AuthService } from '../../core/services/auth.service';
import { RevelationService } from '../../core/services/revelation.service';
import { DailyRevelation, RevelationTimelineResponse } from '../../core/interfaces/revelation.interfaces';
import { SoulConnectionService } from '@core/services/soul-connection.service';
import { ConnectionStage } from '@core/interfaces/soul-connection.interfaces';
import { TypingIndicatorComponent } from '../../shared/components/typing-indicator/typing-indicator.component';
import { Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

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
  lastActive?: string; // Changed from Date to string to match service response
}

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatProgressBarModule,
    MatToolbarModule,
    MatDividerModule,
    MatProgressSpinnerModule,
    TypingIndicatorComponent,
    RouterModule
  ]
})
export class ChatComponent implements OnInit, OnDestroy {
  @ViewChild('messageContainer') private messageContainer!: ElementRef;

  chatForm: FormGroup;
  messages: Message[] = [];
  chatPartner: ChatUser | null = null;
  isLoading = true;
  isSending = false;
  error: string | null = null;
  userId: string | null = null;

  // Typing indicator properties
  typingUsers: TypingUser[] = [];
  private typingHandler?: (inputValue: string) => void;
  private subscriptions = new Subscription();
  private currentUserId: string | null = null;

  // Revelation preview banner
  revelationDay = 0;
  latestPartnerRevelation: DailyRevelation | null = null;
  revelationTimelineLoaded = false;

  // Connection stage chip
  connectionStage: ConnectionStage | null = null;

  readonly STAGE_LABELS: Record<ConnectionStage, string> = {
    soul_discovery:   'Soul Discovery',
    revelation_phase: 'Revelation Phase',
    photo_reveal:     'Photo Reveal',
    dinner_planning:  'Dinner Planning',
    completed:        'Completed'
  };

  get connectionStageLabel(): string {
    return this.connectionStage ? (this.STAGE_LABELS[this.connectionStage] ?? '') : '';
  }

  constructor(
    private fb: FormBuilder,
    private chatService: ChatService,
    private authService: AuthService,
    private revelationService: RevelationService,
    private soulConnectionService: SoulConnectionService,
    private route: ActivatedRoute,
    private router: Router
  ) {
    this.chatForm = this.fb.group({
      message: ['', [Validators.required]]
    });
  }

  ngOnInit(): void {
    // Get connectionId from query params (not route params)
    this.userId = this.route.snapshot.queryParamMap.get('connectionId');

    // Get current user ID from auth service
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        this.currentUserId = user.id.toString();
        this.chatService.setCurrentUser(this.currentUserId);
        // Load revelation preview now that currentUserId is set
        if (this.userId && !this.revelationTimelineLoaded) {
          this.loadRevelationPreview(Number(this.userId));
        }
      }
    });

    if (this.userId) {
      this.loadChatData();
      this.setupTypingIndicators();
      this.loadConnectionStage(Number(this.userId));
    } else {
      this.error = 'Invalid chat. Please go back to matches.';
      this.isLoading = false;
    }
  }

  ngOnDestroy(): void {
    // Cleanup subscriptions
    this.subscriptions.unsubscribe();

    // Stop any active typing indicators
    if (this.userId) {
      this.chatService.stopTyping(this.userId);
    }

    // Cleanup any subscriptions or WebSocket connections
    this.chatService.disconnect();
  }

  loadChatData(): void {
    this.isLoading = true;
    this.error = null;

    this.chatService.getChatData(this.userId!).subscribe({
      next: (data) => {
        this.chatPartner = data.user;
        this.messages = data.messages;
        this.scrollToBottom();
      },
      error: (err) => {
        console.error('Error fetching chat data:', err);
        this.error = 'Failed to load chat. Please try again later.';
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }


  private loadRevelationPreview(connectionId: number): void {
    this.subscriptions.add(
      this.revelationService.getRevelationTimeline(connectionId).subscribe({
        next: (timeline: RevelationTimelineResponse) => {
          this.revelationDay = timeline.current_day;
          const partnerRevelation = timeline.revelations
            .filter(r => r.sender_id !== Number(this.currentUserId))
            .sort((a, b) => b.day_number - a.day_number)[0] ?? null;
          this.latestPartnerRevelation = partnerRevelation;
          this.revelationTimelineLoaded = true;
        },
        error: () => { this.revelationTimelineLoaded = true; }
      })
    );
  }

  private loadConnectionStage(connectionId: number): void {
    this.subscriptions.add(
      this.soulConnectionService.getSoulConnection(connectionId).subscribe({
        next: (connection) => {
          this.connectionStage = connection.connection_stage;
        },
        error: () => { /* non-critical — stage chip simply won't show */ }
      })
    );
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      try {
        this.messageContainer.nativeElement.scrollTop =
          this.messageContainer.nativeElement.scrollHeight;
      } catch (err) {
        // Silently fail if message container is not available
      }
    });
  }

  calculateAge(dateOfBirth: string): number {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  }

  formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();

    // Today
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Yesterday
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

    // Older
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  }

  navigateToMatches(): void {
    this.router.navigate(['/matches']);
  }

  navigateToDinnerPlanning(): void {
    this.router.navigate(['/dinner-planning'], {
      queryParams: { connectionId: this.userId }
    });
  }

  // === TYPING INDICATOR METHODS ===

  private setupTypingIndicators(): void {
    // Set current user ID in chat service
    if (this.currentUserId) {
      this.chatService.setCurrentUserId(this.currentUserId);
    }

    // Subscribe to enhanced typing users for this chat
    this.subscriptions.add(
      this.chatService.getEnhancedTypingUsers().subscribe(users => {
        this.typingUsers = users;
        // Scroll to bottom when typing indicators appear/disappear
        if (users.length > 0) {
          setTimeout(() => this.scrollToBottom(), 100);
        }
      })
    );

    // Setup connection activity tracking
    this.setupConnectionActivity();

    // Setup typing detection for message input
    this.setupTypingDetection();
  }

  private setupConnectionActivity(): void {
    // Mock connection activity for demonstration
    // In real implementation, this would come from API/WebSocket
    if (this.userId && this.chatPartner) {
      this.chatService.updateConnectionActivity(this.userId, {
        connectionStage: 'soul_discovery', // This should come from actual connection data
        compatibilityScore: 85, // This should come from actual compatibility calculation
        lastActivity: new Date(),
        connectionEnergy: 'high'
      });

      // Set initial emotional state (could be determined by mood selector)
      this.chatService.setEmotionalState(this.userId, 'contemplative');
    }
  }

  private setupTypingDetection(): void {
    if (!this.userId) return;

    // Create enhanced current user data for typing indicators
    const currentUserData: TypingUser = {
      id: this.currentUserId || '',
      name: 'You', // This should come from user profile
      avatar: undefined, // Optional avatar URL
      connectionStage: 'soul_discovery', // Should come from connection data
      emotionalState: 'contemplative', // Should come from mood selector
      compatibilityScore: 85 // Should come from compatibility calculation
    };

    // Create typing handler
    this.typingHandler = this.chatService.createTypingHandler(this.userId, currentUserData);

    // Subscribe to form control changes
    this.subscriptions.add(
      this.chatForm.get('message')?.valueChanges.pipe(
        debounceTime(100), // Small debounce for performance
        distinctUntilChanged()
      ).subscribe(value => {
        if (this.typingHandler) {
          this.typingHandler(value || '');
        }
      }) || new Subscription()
    );
  }

  // Enhanced message sending to stop typing indicator
  onSendMessage(): void {
    if (!this.chatForm.valid || this.isSending) return;

    const message = this.chatForm.get('message')?.value.trim();
    if (!message) return;

    // Stop typing indicator before sending
    if (this.userId) {
      this.chatService.stopTyping(this.userId);
    }

    this.isSending = true;

    this.chatService.sendMessage(this.userId!, message).subscribe({
      next: (newMessage) => {
        this.messages = [...this.messages, newMessage];
        this.chatForm.reset();
        this.scrollToBottom();
      },
      error: (_err) => {
        this.error = 'Failed to send message. Please try again.';
      },
      complete: () => {
        this.isSending = false;
      }
    });
  }

  // Method to check if someone is typing
  get hasTypingUsers(): boolean {
    return this.typingUsers.length > 0;
  }

  // Method to get typing indicator position class
  get typingIndicatorClass(): string {
    return this.hasTypingUsers ? 'typing-visible' : 'typing-hidden';
  }
}
