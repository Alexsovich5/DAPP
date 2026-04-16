/**
 * Dashboard Component - Main user dashboard
 */

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';

interface DashboardStats {
  active_connections: number;
  pending_connections: number;
  completed_revelations: number;
  total_messages: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule
  ],
  template: `
    <div class="dashboard">
      <h2>Dashboard</h2>
      <div class="stats-grid">
        <mat-card>
          <mat-card-content>
            <h3>Active Connections</h3>
            <p class="stat-value">{{ stats.active_connections }}</p>
          </mat-card-content>
        </mat-card>
        <mat-card>
          <mat-card-content>
            <h3>Pending Connections</h3>
            <p class="stat-value">{{ stats.pending_connections }}</p>
          </mat-card-content>
        </mat-card>
        <mat-card>
          <mat-card-content>
            <h3>Completed Revelations</h3>
            <p class="stat-value">{{ stats.completed_revelations }}</p>
          </mat-card-content>
        </mat-card>
        <mat-card>
          <mat-card-content>
            <h3>Total Messages</h3>
            <p class="stat-value">{{ stats.total_messages }}</p>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .dashboard {
      padding: 20px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }
    .stat-value {
      font-size: 2rem;
      font-weight: bold;
      margin: 10px 0;
    }
  `]
})
export class DashboardComponent implements OnInit {
  stats: DashboardStats = {
    active_connections: 0,
    pending_connections: 0,
    completed_revelations: 0,
    total_messages: 0
  };

  ngOnInit(): void {
    // Dashboard stats loading is handled by the service
    this.loadDashboardStats();
  }

  private loadDashboardStats(): void {
    // Future implementation: Load dashboard statistics
  }
}
