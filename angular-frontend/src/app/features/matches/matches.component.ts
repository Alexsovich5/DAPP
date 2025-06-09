import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { RevelationService } from '../../core/services/revelation.service';

interface SoulConnection {
  id: number;
  user1_id: number;
  user2_id: number;
  compatibility_score: number;
  compatibility_breakdown: any;
  connection_stage: string;
  reveal_day: number;
  status: string;
  user1_profile?: any;
  user2_profile?: any;
  created_at: string;
}

@Component({
  selector: 'app-matches',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="matches-container">
      <header class="matches-header">
        <h1>Your Soul Connections</h1>
        <p class="subtitle">Meaningful connections beyond the surface</p>
      </header>

      <div class="connection-stats" *ngIf="connections.length > 0">
        <div class="stat-card">
          <span class="stat-number">{{activeConnections}}</span>
          <span class="stat-label">Active Connections</span>
        </div>
        <div class="stat-card">
          <span class="stat-number">{{averageCompatibility}}%</span>
          <span class="stat-label">Avg Compatibility</span>
        </div>
        <div class="stat-card">
          <span class="stat-number">{{connectionsWithRevelations}}</span>
          <span class="stat-label">Sharing Revelations</span>
        </div>
      </div>

      <div class="connections-grid" *ngIf="connections.length > 0; else noConnections">
        <div 
          *ngFor="let connection of connections" 
          class="connection-card"
          [class.highlight]="shouldHighlight(connection)"
          (click)="viewConnection(connection)"
        >
          <div class="connection-header">
            <div class="profile-info">
              <div class="avatar">
                <span>{{getPartnerName(connection).charAt(0)}}</span>
              </div>
              <div class="basic-info">
                <h3>{{getPartnerName(connection)}}</h3>
                <p class="stage">{{formatConnectionStage(connection.connection_stage)}}</p>
              </div>
            </div>
            <div class="compatibility-badge">
              {{connection.compatibility_score}}%
            </div>
          </div>

          <div class="connection-body">
            <div class="revelation-progress">
              <div class="progress-header">
                <span>Revelation Journey</span>
                <span class="day-indicator">Day {{connection.reveal_day}}/7</span>
              </div>
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  [style.width.%]="(connection.reveal_day / 7) * 100"
                ></div>
              </div>
            </div>

            <div class="compatibility-breakdown" *ngIf="connection.compatibility_breakdown">
              <h4>Why you connect:</h4>
              <div class="breakdown-items">
                <div class="breakdown-item">
                  <span class="category">Interests</span>
                  <span class="score">{{connection.compatibility_breakdown.breakdown?.interests || 0}}%</span>
                </div>
                <div class="breakdown-item">
                  <span class="category">Values</span>
                  <span class="score">{{connection.compatibility_breakdown.breakdown?.values || 0}}%</span>
                </div>
                <div class="breakdown-item">
                  <span class="category">Lifestyle</span>
                  <span class="score">{{connection.compatibility_breakdown.breakdown?.demographics || 0}}%</span>
                </div>
              </div>
            </div>
          </div>

          <div class="connection-actions">
            <button class="action-btn primary" (click)="startConversation(connection, $event)">
              <span>💬</span> Continue Chat
            </button>
            <button 
              class="action-btn secondary" 
              (click)="viewRevelations(connection, $event)"
              *ngIf="connection.reveal_day > 1"
            >
              <span>✨</span> View Revelations
            </button>
          </div>
        </div>
      </div>

      <ng-template #noConnections>
        <div class="empty-state">
          <div class="empty-icon">💫</div>
          <h2>No Soul Connections Yet</h2>
          <p>Start discovering meaningful connections based on emotional compatibility</p>
          <button class="cta-button" (click)="goToDiscover()">
            <span>🔍</span> Discover Connections
          </button>
        </div>
      </ng-template>

      <div class="loading-spinner" *ngIf="loading">
        <div class="spinner"></div>
        <p>Loading your connections...</p>
      </div>
    </div>
  `,
  styles: [`
    .matches-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem 1rem;
      min-height: 100vh;
    }

    .matches-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .matches-header h1 {
      font-size: 2.5rem;
      font-weight: 600;
      color: #2d3748;
      margin-bottom: 0.5rem;
    }

    .subtitle {
      font-size: 1.1rem;
      color: #718096;
      margin: 0;
    }

    .connection-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }

    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 1.5rem;
      border-radius: 12px;
      text-align: center;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }

    .stat-number {
      display: block;
      font-size: 2rem;
      font-weight: bold;
      margin-bottom: 0.5rem;
    }

    .stat-label {
      font-size: 0.9rem;
      opacity: 0.9;
    }

    .connections-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 1.5rem;
    }

    .connection-card {
      background: white;
      border-radius: 16px;
      padding: 1.5rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
      border: 1px solid #e2e8f0;
      transition: all 0.3s ease;
      cursor: pointer;
    }

    .connection-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }

    .connection-card.highlight {
      border-color: #667eea;
      box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
    }

    .connection-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }

    .profile-info {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .avatar {
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
    }

    .basic-info h3 {
      margin: 0;
      font-size: 1.2rem;
      font-weight: 600;
      color: #2d3748;
    }

    .stage {
      margin: 0.25rem 0 0 0;
      font-size: 0.9rem;
      color: #718096;
    }

    .compatibility-badge {
      background: #48bb78;
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 20px;
      font-weight: 600;
      font-size: 0.9rem;
    }

    .connection-body {
      margin-bottom: 1.5rem;
    }

    .revelation-progress {
      margin-bottom: 1rem;
    }

    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
      font-size: 0.9rem;
      color: #4a5568;
    }

    .day-indicator {
      font-weight: 600;
      color: #667eea;
    }

    .progress-bar {
      height: 6px;
      background: #e2e8f0;
      border-radius: 3px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      transition: width 0.3s ease;
    }

    .compatibility-breakdown h4 {
      margin: 0 0 0.75rem 0;
      font-size: 1rem;
      color: #2d3748;
    }

    .breakdown-items {
      display: grid;
      gap: 0.5rem;
    }

    .breakdown-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.5rem;
      background: #f7fafc;
      border-radius: 8px;
    }

    .category {
      font-size: 0.9rem;
      color: #4a5568;
    }

    .score {
      font-weight: 600;
      color: #48bb78;
    }

    .connection-actions {
      display: flex;
      gap: 1rem;
    }

    .action-btn {
      flex: 1;
      padding: 0.75rem 1rem;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }

    .action-btn.primary {
      background: #667eea;
      color: white;
    }

    .action-btn.primary:hover {
      background: #5a67d8;
    }

    .action-btn.secondary {
      background: #edf2f7;
      color: #4a5568;
    }

    .action-btn.secondary:hover {
      background: #e2e8f0;
    }

    .empty-state {
      text-align: center;
      padding: 4rem 2rem;
      max-width: 500px;
      margin: 0 auto;
    }

    .empty-icon {
      font-size: 4rem;
      margin-bottom: 1rem;
    }

    .empty-state h2 {
      font-size: 1.8rem;
      font-weight: 600;
      color: #2d3748;
      margin-bottom: 1rem;
    }

    .empty-state p {
      font-size: 1.1rem;
      color: #718096;
      margin-bottom: 2rem;
      line-height: 1.6;
    }

    .cta-button {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      padding: 1rem 2rem;
      border-radius: 12px;
      font-size: 1.1rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }

    .cta-button:hover {
      transform: translateY(-2px);
    }

    .loading-spinner {
      text-align: center;
      padding: 4rem;
    }

    .spinner {
      width: 40px;
      height: 40px;
      border: 4px solid #e2e8f0;
      border-top: 4px solid #667eea;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 0 auto 1rem;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    @media (max-width: 768px) {
      .matches-container {
        padding: 1rem;
      }
      
      .connections-grid {
        grid-template-columns: 1fr;
      }
      
      .connection-stats {
        grid-template-columns: 1fr;
      }
      
      .connection-actions {
        flex-direction: column;
      }
    }
  `]
})
export class MatchesComponent implements OnInit {
  connections: SoulConnection[] = [];
  loading = true;

  constructor(
    private soulConnectionService: SoulConnectionService,
    private revelationService: RevelationService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadConnections();
  }

  async loadConnections() {
    try {
      this.loading = true;
      this.connections = await this.soulConnectionService.getActiveConnections();
    } catch (error) {
      console.error('Error loading connections:', error);
    } finally {
      this.loading = false;
    }
  }

  get activeConnections(): number {
    return this.connections.filter(c => c.status === 'active').length;
  }

  get averageCompatibility(): number {
    if (this.connections.length === 0) return 0;
    const total = this.connections.reduce((sum, c) => sum + c.compatibility_score, 0);
    return Math.round(total / this.connections.length);
  }

  get connectionsWithRevelations(): number {
    return this.connections.filter(c => c.reveal_day > 1).length;
  }

  getPartnerName(connection: SoulConnection): string {
    // Get the other user's name based on current user
    if (connection.user1_profile && connection.user2_profile) {
      // Logic to determine which profile belongs to the partner
      return connection.user2_profile.first_name || 'Unknown';
    }
    return 'Soul Connection';
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

  shouldHighlight(connection: SoulConnection): boolean {
    // Highlight connections with high compatibility or at photo reveal stage
    return connection.compatibility_score >= 80 || connection.connection_stage === 'photo_reveal';
  }

  viewConnection(connection: SoulConnection) {
    this.router.navigate(['/chat'], { 
      queryParams: { connectionId: connection.id }
    });
  }

  startConversation(connection: SoulConnection, event: Event) {
    event.stopPropagation();
    this.router.navigate(['/chat'], { 
      queryParams: { connectionId: connection.id }
    });
  }

  viewRevelations(connection: SoulConnection, event: Event) {
    event.stopPropagation();
    this.router.navigate(['/revelations'], { 
      queryParams: { connectionId: connection.id }
    });
  }

  goToDiscover() {
    this.router.navigate(['/discover']);
  }
}