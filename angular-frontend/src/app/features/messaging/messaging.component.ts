import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatButtonModule } from '@angular/material/button';
import { Subscription, take } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { Message, MessageService } from '../../core/services/message.service';
import {
  DfAvatarComponent,
  DfChipComponent,
  DfInputDirective,
  DfPageShellComponent,
} from '../../shared/ui';

const REVELATION_PROMPTS = [
  'A personal value',
  'A meaningful experience',
  'A hope or dream',
  'What makes you laugh',
  'A challenge overcome',
  'Your ideal connection',
  'Photo reveal',
];

@Component({
  selector: 'app-messaging',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatMenuModule,
    MatButtonModule,
    DfPageShellComponent,
    DfAvatarComponent,
    DfChipComponent,
    DfInputDirective,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './messaging.component.html',
  styleUrls: ['./messaging.component.scss'],
})
export class MessagingComponent implements OnInit, OnDestroy {
  connectionId = 0;
  currentUserId = 0;
  messages: Message[] = [];
  draft = '';
  connection: { id: number; otherUser?: { displayName: string }; dayNumber: number; compatibility: number } | null = null;

  private readonly subs = new Subscription();

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly messageService: MessageService,
    private readonly authService: AuthService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.subs.add(
      this.route.params.subscribe((params) => {
        this.connectionId = +params['connectionId'];
        if (this.connectionId) this.load();
      }),
    );
    this.subs.add(
      this.authService.currentUser$.pipe(take(1)).subscribe((user) => {
        if (user) this.currentUserId = user.id;
      }),
    );
  }

  ngOnDestroy(): void {
    this.subs.unsubscribe();
  }

  get revelationPrompt(): string {
    const day = Math.max(1, Math.min(7, this.connection?.dayNumber ?? 1));
    return REVELATION_PROMPTS[day - 1];
  }

  load(): void {
    this.subs.add(
      this.messageService.getMessages(this.connectionId).subscribe({
        next: (msgs) => {
          this.messages = msgs ?? [];
          // Minimal connection synthesis — replaced when a real connection endpoint is wired.
          this.connection = {
            id: this.connectionId,
            otherUser: { displayName: 'Your connection' },
            dayNumber: 1,
            compatibility: 0,
          };
          this.cdr.markForCheck();
        },
      }),
    );
  }

  sendMessage(): void {
    const text = (this.draft ?? '').trim();
    if (!text) return;
    this.subs.add(
      this.messageService.sendMessage(this.connectionId, text, 'text').subscribe({
        next: () => {
          this.draft = '';
          this.load();
        },
      }),
    );
  }

  goBack(): void {
    this.router.navigate(['/messages']);
  }

  openRevelation(): void {
    this.router.navigate(['/revelations/compose', this.connectionId]);
  }

  openAttachSheet(): void {
    // Future: open bottom sheet for revelation / photo attach.
  }

  onReport(): void {
    // Future: report flow.
  }

  onUnmatch(): void {
    // Future: unmatch flow.
  }

  trackById(_: number, m: Message): number {
    return m.id;
  }
}
