import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
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
import { ChatService } from '../../core/services/chat.service';

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
    MatProgressSpinnerModule
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

  constructor(
    private fb: FormBuilder,
    private chatService: ChatService,
    private route: ActivatedRoute,
    private router: Router
  ) {
    this.chatForm = this.fb.group({
      message: ['', [Validators.required]]
    });
  }

  ngOnInit(): void {
    this.userId = this.route.snapshot.paramMap.get('id');
    if (this.userId) {
      this.loadChatData();
    } else {
      this.error = 'Invalid chat. Please go back to matches.';
      this.isLoading = false;
    }
  }

  ngOnDestroy(): void {
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

  onSendMessage(): void {
    if (!this.chatForm.valid || this.isSending) return;

    const message = this.chatForm.get('message')?.value.trim();
    if (!message) return;

    this.isSending = true;

    this.chatService.sendMessage(this.userId!, message).subscribe({
      next: (newMessage) => {
        this.messages = [...this.messages, newMessage];
        this.chatForm.reset();
        this.scrollToBottom();
      },
      error: (err) => {
        this.error = 'Failed to send message. Please try again.';
      },
      complete: () => {
        this.isSending = false;
      }
    });
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      try {
        this.messageContainer.nativeElement.scrollTop =
          this.messageContainer.nativeElement.scrollHeight;
      } catch (err) {}
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

  navigateToPreferences(): void {
    this.router.navigate(['/preferences']);
  }
}
