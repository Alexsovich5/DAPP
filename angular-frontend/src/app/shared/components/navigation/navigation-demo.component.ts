import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavigationComponent } from './navigation.component';
import { LoadingScreenComponent } from '../loading-screen/loading-screen.component';
import { SkeletonLoaderComponent } from '../skeleton-loader/skeleton-loader.component';
import { SoulOrbComponent } from '../soul-orb/soul-orb.component';
import { SoulConnectionComponent } from '../soul-connection/soul-connection.component';
import { CompatibilityRadarComponent } from '../compatibility-radar/compatibility-radar.component';
import { MatchCelebrationComponent } from '../match-celebration/match-celebration.component';

@Component({
  selector: 'app-navigation-demo',
  standalone: true,
  imports: [CommonModule, NavigationComponent, LoadingScreenComponent, SkeletonLoaderComponent, SoulOrbComponent, SoulConnectionComponent, CompatibilityRadarComponent, MatchCelebrationComponent],
  template: `
    <div class="demo-container">
      <!-- Force show navigation by setting authenticated state -->
      <div style="position: relative; z-index: 1000;">
        <app-navigation></app-navigation>
      </div>
      
      <div class="demo-content">
        <h1>Navigation & Loading Components Demo</h1>
        
        <section class="demo-section">
          <h2>Updated Navigation</h2>
          <p>Navigation now has 3 main sections instead of 5:</p>
          <ul>
            <li>🔍 Discover</li>
            <li>💬 Conversations (merged Connections + Messages with notification badge)</li>
            <li>✨ Revelations</li>
          </ul>
          <p>Improved mobile typography with larger touch targets (min 44px) and better font sizes.</p>
        </section>

        <section class="demo-section">
          <h2>Loading Screens</h2>
          <div class="loading-demos">
            <div class="loading-demo">
              <h3>Discovery Loading</h3>
              <app-loading-screen 
                screenType="discovery" 
                loadingText="Finding your perfect soul matches...">
              </app-loading-screen>
            </div>
            
            <div class="loading-demo">
              <h3>Conversations Loading</h3>
              <app-loading-screen 
                screenType="conversations" 
                loadingText="Loading your heart connections...">
              </app-loading-screen>
            </div>
            
            <div class="loading-demo">
              <h3>Profile Loading</h3>
              <app-loading-screen 
                screenType="profile" 
                loadingText="Revealing your soul story...">
              </app-loading-screen>
            </div>
          </div>
        </section>

        <section class="demo-section">
          <h2>Skeleton Components</h2>
          <div class="skeleton-demos">
            <app-skeleton-loader type="card"></app-skeleton-loader>
            <app-skeleton-loader type="text" width="70%"></app-skeleton-loader>
            <app-skeleton-loader type="button"></app-skeleton-loader>
            <div style="display: flex; gap: 1rem; align-items: center;">
              <app-skeleton-loader type="avatar"></app-skeleton-loader>
              <app-skeleton-loader type="text" width="60%"></app-skeleton-loader>
            </div>
          </div>
        </section>

        <section class="demo-section">
          <h2>🌟 Enhanced Soul Visualizations</h2>
          <p>Revolutionary soul connection graphics that replace basic emojis with sophisticated animations.</p>
          
          <h3>Soul Orbs</h3>
          <div class="soul-orbs-demo">
            <app-soul-orb 
              type="primary" 
              size="large" 
              state="active" 
              [energyLevel]="4"
              [compatibilityScore]="85"
              [showCompatibility]="true">
            </app-soul-orb>
            <app-soul-orb 
              type="secondary" 
              size="large" 
              state="matched" 
              [energyLevel]="5"
              [compatibilityScore]="92"
              [showCompatibility]="true">
            </app-soul-orb>
            <app-soul-orb 
              type="neutral" 
              size="medium" 
              state="connecting" 
              [energyLevel]="2">
            </app-soul-orb>
          </div>

          <h3>Soul Connection Animation</h3>
          <div class="soul-connection-demo">
            <app-soul-connection
              [leftSoul]="{type: 'primary', state: 'matched', energy: 4, label: 'You', showParticles: true, showSparkles: true}"
              [rightSoul]="{type: 'secondary', state: 'matched', energy: 5, label: 'Sarah', showParticles: true, showSparkles: true}"
              [compatibilityScore]="88"
              [connectionState]="'strong-match'"
              [orbSize]="'medium'"
              [showCompatibility]="true"
              [statusMessage]="'Soul connection established ✨'">
            </app-soul-connection>
          </div>
        </section>

        <section class="demo-section">
          <h2>📊 Compatibility Analysis</h2>
          <p>Advanced radar visualization showing multi-dimensional soul compatibility.</p>
          
          <div class="compatibility-demo">
            <app-compatibility-radar
              [compatibilityData]="{values: 92, interests: 76, communication: 88, lifestyle: 73, goals: 85, personality: 91}"
              size="medium"
              [showHeader]="true"
              [showLegend]="true"
              [showInsights]="true"
              [animateChart]="true">
            </app-compatibility-radar>
          </div>
        </section>

        <section class="demo-section">
          <h2>🎉 Match Celebration</h2>
          <p>Immersive celebration experience for successful soul connections.</p>
          
          <div class="celebration-demo">
            <button 
              class="demo-button celebration-trigger"
              (click)="showCelebration = true">
              ✨ Trigger Soul Match Celebration
            </button>
            
            <app-match-celebration
              [isActive]="showCelebration"
              [compatibilityScore]="91"
              [leftSoul]="{type: 'primary', state: 'matched', energy: 5, label: 'You'}"
              [rightSoul]="{type: 'secondary', state: 'matched', energy: 5, label: 'Emma'}"
              [showConfetti]="true"
              [showSparkles]="true"
              [showHearts]="true"
              [showHighlights]="true"
              [showInsights]="true"
              (startConversation)="onStartConversation()"
              (viewProfile)="onViewProfile()"
              (dismiss)="showCelebration = false">
            </app-match-celebration>
          </div>
        </section>
      </div>
    </div>
  `,
  styles: [`
    .demo-container {
      min-height: 100vh;
      background: var(--background-color, #ffffff);
      color: var(--text-primary, #1f2937);
    }

    .demo-content {
      padding: 2rem;
      max-width: 1200px;
      margin: 0 auto;
      margin-top: 80px; // Account for fixed navigation
    }

    .demo-section {
      margin-bottom: 3rem;
      padding: 2rem;
      background: var(--card-background, #ffffff);
      border-radius: 12px;
      box-shadow: 0 2px 8px var(--shadow-color, rgba(0, 0, 0, 0.1));
    }

    .loading-demos {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 2rem;
    }

    .loading-demo {
      border: 1px solid var(--border-color, #e5e7eb);
      border-radius: 8px;
      padding: 1rem;
    }

    .skeleton-demos {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      max-width: 400px;
    }

    h1 {
      color: var(--primary-color, #ec4899);
      margin-bottom: 2rem;
    }

    h2 {
      color: var(--accent-color, #8b5cf6);
      margin-bottom: 1rem;
    }

    ul {
      list-style: none;
      padding: 0;
    }

    li {
      padding: 0.5rem 0;
      border-bottom: 1px solid var(--border-color, #e5e7eb);
    }

    .soul-orbs-demo {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 2rem;
      flex-wrap: wrap;
      padding: 2rem;
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.05), rgba(255, 107, 157, 0.05));
      border-radius: 16px;
      margin: 1rem 0;
    }

    .soul-connection-demo {
      padding: 2rem;
      background: var(--surface-color, #f8fafc);
      border-radius: 16px;
      margin: 1rem 0;
    }

    .compatibility-demo {
      display: flex;
      justify-content: center;
      padding: 1rem;
      background: var(--surface-color, #f8fafc);
      border-radius: 16px;
      margin: 1rem 0;
    }

    .celebration-demo {
      text-align: center;
      padding: 2rem;
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 107, 157, 0.1));
      border-radius: 16px;
      margin: 1rem 0;
    }

    .demo-button {
      padding: 1rem 2rem;
      background: linear-gradient(135deg, #ffd700, #ff6b9d);
      color: white;
      border: none;
      border-radius: 12px;
      font-size: 1.1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      box-shadow: 0 4px 15px rgba(255, 107, 157, 0.3);
    }

    .demo-button:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(255, 107, 157, 0.4);
    }

    @media (max-width: 768px) {
      .demo-content {
        padding: 1rem;
        margin-top: 70px;
      }
      
      .loading-demos {
        grid-template-columns: 1fr;
      }

      .soul-orbs-demo {
        gap: 1rem;
        padding: 1rem;
      }

      .soul-connection-demo,
      .compatibility-demo,
      .celebration-demo {
        padding: 1rem;
      }

      .demo-button {
        padding: 0.875rem 1.5rem;
        font-size: 1rem;
      }
    }
  `]
})
export class NavigationDemoComponent {
  showCelebration = false;

  onStartConversation() {
    console.log('Starting soul conversation...');
    // In real app, navigate to conversations
  }

  onViewProfile() {
    console.log('Viewing soul profile...');
    // In real app, navigate to profile
  }
}