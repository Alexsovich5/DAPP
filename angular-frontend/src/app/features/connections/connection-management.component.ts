import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { Subscription, take } from 'rxjs';
import { SoulConnectionService } from '@core/services/soul-connection.service';
import { AuthService } from '@core/services/auth.service';
import { SoulConnection } from '@core/interfaces/soul-connection.interfaces';
import { ConnectionCardComponent } from './connection-card.component';

@Component({
  selector: 'app-connection-management',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    MatProgressSpinnerModule,
    MatIconModule,
    ConnectionCardComponent
  ],
  template: `
    <div class="connections-page">
      <header class="page-header">
        <h1>Soul Connections</h1>
        <p class="subtitle">Your active soul journeys</p>
      </header>

      <div *ngIf="isLoading" class="loading-state" role="status" aria-label="Loading connections">
        <mat-spinner diameter="40"></mat-spinner>
      </div>

      <div *ngIf="error && !isLoading" class="error-state" role="alert">
        <mat-icon>error</mat-icon>
        <p>{{ error }}</p>
      </div>

      <mat-tab-group *ngIf="!isLoading && !error" dynamicHeight>
        <mat-tab label="Active ({{ activeConnections.length }})">
          <div class="connections-list" role="list">
            <ng-container *ngIf="activeConnections.length > 0; else emptyActive">
              <app-connection-card
                *ngFor="let c of activeConnections; trackBy: trackById"
                [connection]="c"
                [currentUserId]="currentUserId"
                (openChat)="navigateToChat($event)">
              </app-connection-card>
            </ng-container>
            <ng-template #emptyActive>
              <div class="empty-state" role="status">
                <mat-icon>psychology</mat-icon>
                <p>No active connections yet. Start discovering!</p>
              </div>
            </ng-template>
          </div>
        </mat-tab>

        <mat-tab label="Revealing ({{ revealingConnections.length }})">
          <div class="connections-list" role="list">
            <ng-container *ngIf="revealingConnections.length > 0; else emptyRevealing">
              <app-connection-card
                *ngFor="let c of revealingConnections; trackBy: trackById"
                [connection]="c"
                [currentUserId]="currentUserId"
                (openChat)="navigateToChat($event)">
              </app-connection-card>
            </ng-container>
            <ng-template #emptyRevealing>
              <div class="empty-state" role="status">
                <mat-icon>auto_stories</mat-icon>
                <p>No connections in the revelation phase yet.</p>
              </div>
            </ng-template>
          </div>
        </mat-tab>

        <mat-tab label="Planning Dinner ({{ dinnerConnections.length }})">
          <div class="connections-list" role="list">
            <ng-container *ngIf="dinnerConnections.length > 0; else emptyDinner">
              <app-connection-card
                *ngFor="let c of dinnerConnections; trackBy: trackById"
                [connection]="c"
                [currentUserId]="currentUserId"
                (openChat)="navigateToChat($event)">
              </app-connection-card>
            </ng-container>
            <ng-template #emptyDinner>
              <div class="empty-state" role="status">
                <mat-icon>restaurant</mat-icon>
                <p>No dinner plans in progress yet.</p>
              </div>
            </ng-template>
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .connections-page { padding: 16px; max-width: 600px; margin: 0 auto; }
    .page-header { margin-bottom: 16px; }
    .page-header h1 { margin: 0 0 4px; font-size: 1.5rem; color: var(--text-primary); }
    .subtitle { margin: 0; color: var(--text-secondary); font-size: 0.875rem; }
    .connections-list { padding: 12px 0; }
    .loading-state, .error-state {
      display: flex; align-items: center; justify-content: center;
      flex-direction: column; gap: 8px; padding: 32px 0;
      color: var(--text-secondary);
    }
    .error-state mat-icon { color: var(--status-error); font-size: 32px; width: 32px; height: 32px; }
    .empty-state {
      display: flex; flex-direction: column; align-items: center;
      gap: 8px; padding: 32px 0; color: var(--text-secondary);
    }
    .empty-state mat-icon { font-size: 40px; width: 40px; height: 40px; }
  `]
})
export class ConnectionManagementComponent implements OnInit, OnDestroy {
  connections: SoulConnection[] = [];
  currentUserId = 0;
  isLoading = true;
  error: string | null = null;

  private sub = new Subscription();

  constructor(
    private soulConnectionService: SoulConnectionService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.sub.add(
      this.authService.currentUser$.pipe(take(1)).subscribe(user => {
        if (user) this.currentUserId = user.id;
        this.loadConnections();
      })
    );
  }

  ngOnDestroy(): void {
    this.sub.unsubscribe();
  }

  // Note: 'completed' stage connections are intentionally excluded — they have
  // already had their first dinner and no longer require active management.
  get activeConnections(): SoulConnection[] {
    return this.connections.filter(c => c.connection_stage === 'soul_discovery');
  }

  get revealingConnections(): SoulConnection[] {
    return this.connections.filter(c =>
      c.connection_stage === 'revelation_phase' || c.connection_stage === 'photo_reveal'
    );
  }

  get dinnerConnections(): SoulConnection[] {
    return this.connections.filter(c => c.connection_stage === 'dinner_planning');
  }

  trackById(_: number, c: SoulConnection): number {
    return c.id;
  }

  navigateToChat(connection: SoulConnection): void {
    this.router.navigate(['/chat'], { queryParams: { connectionId: connection.id } });
  }

  private loadConnections(): void {
    this.isLoading = true;
    this.error = null;
    this.sub.add(
      this.soulConnectionService.getActiveConnections().subscribe({
        next: (connections) => {
          this.connections = connections;
          this.isLoading = false;
        },
        error: (err) => {
          this.error = 'Unable to load connections. Please try again.';
          console.error('Connections load error:', err);
          this.isLoading = false;
        }
      })
    );
  }
}
