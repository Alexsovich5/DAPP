/**
 * Connection Management Component - Soul connection lifecycle management
 */

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-connection-management',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule
  ],
  template: `
    <div class="connection-management">
      <h2>Soul Connections</h2>
      <mat-tab-group>
        <mat-tab label="Active">
          <div class="connections-list">
            <!-- TODO: Implement active connections list -->
          </div>
        </mat-tab>
        <mat-tab label="Pending">
          <div class="connections-list">
            <!-- TODO: Implement pending connections list -->
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .connection-management {
      padding: 20px;
    }
    .connections-list {
      padding: 20px;
    }
  `]
})
export class ConnectionManagementComponent implements OnInit {
  ngOnInit(): void {
    this.loadConnections();
  }

  private loadConnections(): void {
    // Future implementation: Load user connections
  }
}
