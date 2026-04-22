import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { SoulConnection, ConnectionStage } from '@core/interfaces/soul-connection.interfaces';
import { DfButtonDirective } from '../../shared/ui';

const STAGE_LABELS: Record<ConnectionStage, string> = {
  soul_discovery:   'Soul Discovery',
  revelation_phase: 'Revelation Phase',
  photo_reveal:     'Photo Reveal',
  dinner_planning:  'Dinner Planning',
  completed:        'Completed'
};

const STAGE_ICONS: Record<ConnectionStage, string> = {
  soul_discovery:   'psychology',
  revelation_phase: 'auto_stories',
  photo_reveal:     'photo_camera',
  dinner_planning:  'restaurant',
  completed:        'check_circle'
};

@Component({
  selector: 'app-connection-card',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatChipsModule, DfButtonDirective],
  template: `
    <mat-card class="connection-card" role="article" [attr.aria-label]="partnerName + ' connection'">
      <mat-card-header>
        <div mat-card-avatar class="avatar" aria-hidden="true">
          <mat-icon>person</mat-icon>
        </div>
        <mat-card-title>{{ partnerName }}</mat-card-title>
        <mat-card-subtitle>
          <mat-chip class="stage-chip" [ngClass]="'stage-' + connection.connection_stage">
            <mat-icon matChipLeadingIcon aria-hidden="true">{{ stageIcon }}</mat-icon>
            {{ stageLabel }}
          </mat-chip>
        </mat-card-subtitle>
      </mat-card-header>

      <mat-card-content>
        <div class="stats-row">
          <span class="stat" aria-label="Compatibility score">
            <mat-icon aria-hidden="true">favorite</mat-icon>
            {{ connection.compatibility_score ?? 0 }}%
          </span>
          <span class="stat" *ngIf="connection.connection_stage === 'revelation_phase'" aria-label="Revelation day">
            <mat-icon aria-hidden="true">calendar_today</mat-icon>
            Day {{ connection.reveal_day }} of 7
          </span>
          <span class="stat" *ngIf="connection.mutual_reveal_consent" aria-label="Photos revealed">
            <mat-icon aria-hidden="true">photo_camera</mat-icon>
            Photos revealed
          </span>
        </div>
      </mat-card-content>

      <mat-card-actions>
        <button
          dfButton
          variant="primary"
          size="md"
          type="button"
          data-testid="open-chat-btn"
          [attr.aria-label]="'Open chat with ' + partnerName"
          (click)="openChat.emit(connection)">
          <mat-icon>chat</mat-icon>
          Open Chat
        </button>
      </mat-card-actions>
    </mat-card>
  `,
  styles: [`
    .connection-card { margin-bottom: 12px; }
    .avatar {
      display: flex; align-items: center; justify-content: center;
      background: var(--color-surface-alt);
      border-radius: 50%;
    }
    .stats-row { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 4px; }
    .stat { display: flex; align-items: center; gap: 4px; font-size: 0.875rem; color: var(--color-text-muted); }
    .stat mat-icon { font-size: 16px; width: 16px; height: 16px; }
    .stage-chip { font-size: 0.75rem; }
    .stage-revelation_phase { background: var(--color-accent-soft); }
    .stage-photo_reveal     { background: var(--color-surface-alt); }
    .stage-dinner_planning  { background: var(--color-accent); color: var(--color-text); }
    .stage-completed        { background: var(--color-surface-alt); }
    button[dfButton] mat-icon { margin-right: 4px; }
  `]
})
export class ConnectionCardComponent {
  @Input({ required: true }) connection!: SoulConnection;
  @Input({ required: true }) currentUserId!: number;
  @Output() openChat = new EventEmitter<SoulConnection>();

  get partnerName(): string {
    if (this.connection.user1_id === this.currentUserId) {
      return this.connection.user2_profile?.first_name ?? 'Unknown';
    }
    return this.connection.user1_profile?.first_name ?? 'Unknown';
  }

  get stageLabel(): string {
    return STAGE_LABELS[this.connection.connection_stage] ?? this.connection.connection_stage;
  }

  get stageIcon(): string {
    return STAGE_ICONS[this.connection.connection_stage] ?? 'circle';
  }
}
