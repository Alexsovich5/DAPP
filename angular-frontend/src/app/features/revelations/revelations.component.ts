import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { RevelationService } from '../../core/services/revelation.service';
import { SoulConnectionService } from '../../core/services/soul-connection.service';
import { HapticFeedbackService } from '../../core/services/haptic-feedback.service';
import { RevelationKeyboardNavigationService } from './revelation-keyboard-navigation.service';
import { RevelationsEmptyStateComponent } from './revelations-empty-state.component';
import { PhotoRevealConsentDialogComponent } from '../../shared/components/photo-reveal-consent/photo-reveal-consent-dialog.component';
import {
  RevelationPrompt,
  DailyRevelation,
  RevelationTimelineResponse,
  RevelationTimelineResponse as RevelationTimeline,
  RevelationType
} from '../../core/interfaces/revelation.interfaces';

@Component({
  selector: 'app-revelations',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RevelationsEmptyStateComponent, MatDialogModule],
  template: `
    <div class="revelations-container" #revelationContainer>
      <header class="revelations-header">
        <button class="back-btn" (click)="goBack()">
          <span>←</span> Back
        </button>
        <div class="header-content">
          <h1>Daily Revelations</h1>
          <p class="subtitle">Your 7-day journey to deeper connection</p>
        </div>
      </header>

      <div class="revelation-progress" *ngIf="timeline">
        <div class="progress-header">
          <h2>Day {{timeline.current_day}} of 7</h2>
          <span class="completion-status" [class.complete]="timeline.is_cycle_complete">
            {{timeline.is_cycle_complete ? 'Cycle Complete! 🎉' : 'In Progress...'}}
          </span>
          <span class="streak-badge" *ngIf="streakCount > 0">🔥 {{streakCount}} day streak</span>
        </div>

        <div class="progress-visual">
          <div class="day-circles" role="tablist" aria-label="Revelation journey progress">
            <div
              *ngFor="let day of [1,2,3,4,5,6,7]"
              class="day-circle"
              [class.completed]="day < timeline.current_day"
              [class.current]="day === timeline.current_day"
              [class.future]="day > timeline.current_day"
              [attr.id]="'day-' + day"
              role="tab"
              [attr.aria-selected]="day === timeline.current_day"
              [attr.aria-controls]="'day-panel-' + day"
              [attr.tabindex]="day === timeline.current_day ? 0 : -1"
              [attr.aria-label]="'Day ' + day + ': ' + getDayLabel(day) + (day < timeline.current_day ? ' (completed)' : day === timeline.current_day ? ' (current)' : ' (upcoming)')"
              (click)="navigateToDay(day)"
              (keydown.enter)="navigateToDay(day)"
              (keydown.space)="navigateToDay(day); $event.preventDefault()"
            >
              <span class="day-number" aria-hidden="true">{{day}}</span>
              <div class="day-label" aria-hidden="true">{{getDayLabel(day)}}</div>
            </div>
          </div>
          <div class="progress-line">
            <div
              class="progress-fill"
              [style.width.%]="((timeline.current_day - 1) / 6) * 100"
            ></div>
          </div>
        </div>
      </div>

      <!-- Celebration overlay -->
      <div class="confetti-overlay" *ngIf="showCelebrate || timeline?.is_cycle_complete">
        <div class="confetti" *ngFor="let i of confettiPieces"></div>
      </div>

      <!-- Current Day Prompt -->
      <div class="current-prompt" *ngIf="currentPrompt && !timeline?.is_cycle_complete">
        <div class="prompt-card">
          <div class="prompt-header">
            <h3>Today's Revelation Prompt</h3>
            <span class="prompt-type">{{formatRevelationType(currentPrompt.revelation_type)}}</span>
          </div>

          <div class="prompt-content">
            <p class="prompt-text">{{currentPrompt.prompt_text}}</p>
            <div class="example-response">
              <h4>Example Response:</h4>
              <p>"{{currentPrompt.example_response}}"</p>
            </div>
          </div>

          <form [formGroup]="revelationForm" (ngSubmit)="shareRevelation()" class="revelation-form" role="form" aria-labelledby="current-prompt-title">
            <div class="form-group">
              <label for="revelation-content">Your Revelation:</label>
              <textarea
                id="revelation-content"
                formControlName="content"
                placeholder="Share something meaningful from your heart..."
                rows="4"
                [class.error]="revelationForm.get('content')?.invalid && revelationForm.get('content')?.touched"
                [attr.aria-describedby]="revelationForm.get('content')?.invalid && revelationForm.get('content')?.touched ? 'revelation-error' : 'revelation-help'"
                aria-required="true"
                (keydown)="handleFormKeydown($event)"
              ></textarea>
              <div class="error-message" *ngIf="revelationForm.get('content')?.invalid && revelationForm.get('content')?.touched">
                Please share your revelation (minimum 20 characters)
              </div>
            </div>

            <div class="form-actions">
              <button
                type="submit"
                class="share-btn"
                [disabled]="revelationForm.invalid || submitting"
              >
                <span *ngIf="!submitting">✨ Share Revelation</span>
                <span *ngIf="submitting">Sharing... 💫</span>
              </button>
            </div>
          </form>

          <!-- What's next tip -->
          <div class="whats-next" *ngIf="whatsNext">
            <h4>What’s next?</h4>
            <p>{{whatsNext}}</p>
          </div>
        </div>
      </div>

      <!-- Revelations Timeline -->
      <div class="revelations-timeline" *ngIf="timeline && timeline.revelations.length > 0">
        <h3>Your Revelation Journey</h3>

        <div class="timeline-container" role="log" aria-label="Revelation timeline">
          <div
            *ngFor="let revelation of sortedRevelations; let i = index"
            class="revelation-item"
            [class.sent]="revelation.sender_id === currentUserId"
            [class.received]="revelation.sender_id !== currentUserId"
            [attr.id]="'revelation-' + revelation.id"
            role="article"
            [attr.aria-label]="'Revelation ' + (i + 1) + ' of ' + sortedRevelations.length + ' from ' + (revelation.sender_id === currentUserId ? 'you' : revelation.sender_name)"
            [attr.tabindex]="0"
            (keydown)="handleTimelineItemKeydown($event, revelation)"
          >
            <div class="revelation-meta">
              <div class="day-badge">Day {{revelation.day_number}}</div>
              <div class="sender-info">
                <span class="sender-name">{{revelation.sender_name || 'Unknown'}}</span>
                <span class="revelation-type">{{formatRevelationType(revelation.revelation_type)}}</span>
              </div>
              <span class="timestamp">{{formatDate(revelation.created_at)}}</span>
            </div>

            <div class="revelation-content">
              <p>{{revelation.content}}</p>
            </div>

            <div class="revelation-actions" *ngIf="revelation.sender_id !== currentUserId">
              <button class="action-btn" (click)="markAsRead(revelation)">
                <span>👀</span> Read
              </button>
              <button class="action-btn" (click)="reactToRevelation(revelation)">
                <span>💝</span> React
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Photo Reveal Special Section -->
      <div class="photo-reveal-section" *ngIf="timeline?.current_day === 7 || timeline?.is_cycle_complete">
        <div class="photo-reveal-card">
          <div class="photo-reveal-header">
            <h3>🎉 Photo Reveal Day!</h3>
            <p>You've completed your 7-day revelation journey. Ready to see each other?</p>
          </div>

          <div class="mutual-consent" *ngIf="!photoRevealed">
            <div class="consent-status">
              <div class="consent-item">
                <span class="user">You</span>
                <span class="status" [class.agreed]="userConsent">
                  {{userConsent ? '✅ Ready' : '⏳ Pending'}}
                </span>
              </div>
              <div class="consent-item">
                <span class="user">{{partnerName}}</span>
                <span class="status" [class.agreed]="partnerConsent">
                  {{partnerConsent ? '✅ Ready' : '⏳ Pending'}}
                </span>
              </div>
            </div>

            <button
              class="consent-btn"
              [class.agreed]="userConsent"
              (click)="togglePhotoConsent()"
              [disabled]="submitting"
            >
              {{userConsent ? '✅ You agreed to reveal' : '🤔 Agree to photo reveal'}}
            </button>
          </div>

          <div class="photo-revealed" *ngIf="photoRevealed">
            <h4>🌟 Photos Revealed!</h4>
            <p>You can now see each other's photos and continue your connection journey.</p>
            <button class="view-profile-btn" (click)="viewFullProfile()">
              <span>👀</span> View Full Profile
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State for No Connections -->
      <div class="empty-revelations" *ngIf="!loading && !connectionId">
        <app-revelations-empty-state
          (startJourney)="startRevelationJourney()"
          (learnAboutRevelations)="learnAboutRevelations()">
        </app-revelations-empty-state>
      </div>

      <div class="loading-spinner" *ngIf="loading">
        <div class="spinner"></div>
        <p>Loading revelations...</p>
      </div>
    </div>
  `,
  styles: [`
    .revelations-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 1rem;
      min-height: 100vh;
    }

    .revelations-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #e2e8f0;
    }

    .back-btn {
      padding: 0.5rem;
      border: 1px solid #e2e8f0;
      background: white;
      border-radius: 8px;
      cursor: pointer;
      color: #718096;
      transition: all 0.2s ease;
    }

    .back-btn:hover {
      border-color: #667eea;
      color: #667eea;
    }

    .header-content h1 {
      font-size: 2rem;
      font-weight: 600;
      color: #2d3748;
      margin: 0 0 0.25rem 0;
    }

    .subtitle {
      color: #718096;
      margin: 0;
    }

    .revelation-progress {
      background: white;
      border-radius: 16px;
      padding: 2rem;
      margin-bottom: 2rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    }

    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
    }

    .progress-header h2 {
      color: #2d3748;
      margin: 0;
      font-size: 1.5rem;
    }

    .completion-status {
      font-weight: 600;
      color: #f56565;
    }

    .completion-status.complete {
      color: #48bb78;
    }

    .streak-badge {
      background: #fff5f5;
      color: #c53030;
      border: 1px solid #fed7d7;
      padding: 0.25rem 0.5rem;
      border-radius: 999px;
      font-size: 0.85rem;
    }

    .progress-visual {
      position: relative;
    }

    .day-circles {
      display: flex;
      justify-content: space-between;
      position: relative;
      z-index: 2;
    }

    .day-circle {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;
    }

    .day-number {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 1.1rem;
      border: 3px solid #e2e8f0;
      background: white;
      color: #a0aec0;
      transition: all 0.3s ease;
    }

    .day-circle.completed .day-number {
      background: #48bb78;
      border-color: #48bb78;
      color: white;
    }

    .day-circle.current .day-number {
      background: #667eea;
      border-color: #667eea;
      color: white;
      box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
    }

    .day-label {
      font-size: 0.8rem;
      color: #718096;
      text-align: center;
      max-width: 80px;
    }

    .progress-line {
      position: absolute;
      top: 25px;
      left: 25px;
      right: 25px;
      height: 3px;
      background: #e2e8f0;
      z-index: 1;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #48bb78 0%, #667eea 100%);
      transition: width 0.5s ease;
    }

    /* Celebration overlay */
    .confetti-overlay {
      position: fixed;
      inset: 0;
      pointer-events: none;
      overflow: hidden;
      z-index: 2000;
    }
    .confetti {
      position: absolute;
      top: -10px;
      left: calc(50% - 2px);
      width: 6px;
      height: 12px;
      background: hsl(var(--hue, 200), 80%, 60%);
      opacity: 0.9;
      transform: translateX(var(--x, 0));
      animation: confetti-fall 1200ms ease-out forwards;
    }
    @keyframes confetti-fall {
      0% { transform: translate(var(--x, 0), 0) rotate(0deg); }
      100% { transform: translate(var(--x, 0), 110vh) rotate(540deg); opacity: 0.7; }
    }

    .current-prompt {
      margin-bottom: 2rem;
    }

    .prompt-card {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
      border: 1px solid rgba(102, 126, 234, 0.1);
      border-radius: 16px;
      padding: 2rem;
    }

    .prompt-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
    }

    .prompt-header h3 {
      color: #2d3748;
      margin: 0;
      font-size: 1.3rem;
    }

    .prompt-type {
      background: #667eea;
      color: white;
      padding: 0.5rem 1rem;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 600;
    }

    .prompt-content {
      margin-bottom: 2rem;
    }

    .prompt-text {
      font-size: 1.1rem;
      color: #2d3748;
      margin-bottom: 1rem;
      font-weight: 500;
    }

    .example-response {
      background: white;
      padding: 1rem;
      border-radius: 8px;
      border-left: 4px solid #667eea;
    }

    .example-response h4 {
      margin: 0 0 0.5rem 0;
      font-size: 0.9rem;
      color: #718096;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .example-response p {
      margin: 0;
      font-style: italic;
      color: #4a5568;
    }

    .whats-next {
      margin-top: 1rem;
      background: #f7fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1rem;
    }
    .whats-next h4 {
      margin: 0 0 0.5rem 0;
      color: #2d3748;
    }

    .revelation-form {
      background: white;
      padding: 1.5rem;
      border-radius: 12px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }

    .form-group {
      margin-bottom: 1.5rem;
    }

    .form-group label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 600;
      color: #2d3748;
    }

    .form-group textarea {
      width: 100%;
      padding: 1rem;
      border: 2px solid #e2e8f0;
      border-radius: 8px;
      font-size: 1rem;
      line-height: 1.5;
      transition: border-color 0.2s ease;
      resize: vertical;
      min-height: 120px;
    }

    .form-group textarea:focus {
      outline: none;
      border-color: #667eea;
    }

    .form-group textarea.error {
      border-color: #f56565;
    }

    .error-message {
      color: #f56565;
      font-size: 0.8rem;
      margin-top: 0.5rem;
    }

    .form-actions {
      text-align: center;
    }

    .share-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      padding: 1rem 2rem;
      border-radius: 12px;
      font-size: 1.1rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease;
      min-width: 200px;
    }

    .share-btn:hover:not(:disabled) {
      transform: translateY(-1px);
    }

    .share-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .revelations-timeline {
      background: white;
      border-radius: 16px;
      padding: 2rem;
      margin-bottom: 2rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    }

    .revelations-timeline h3 {
      color: #2d3748;
      margin: 0 0 2rem 0;
      font-size: 1.3rem;
    }

    .timeline-container {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .revelation-item {
      border-radius: 12px;
      padding: 1.5rem;
      position: relative;
    }

    .revelation-item.sent {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(102, 126, 234, 0.02) 100%);
      border-left: 4px solid #667eea;
      margin-left: 2rem;
    }

    .revelation-item.received {
      background: linear-gradient(135deg, rgba(72, 187, 120, 0.05) 0%, rgba(72, 187, 120, 0.02) 100%);
      border-left: 4px solid #48bb78;
      margin-right: 2rem;
    }

    .revelation-meta {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .day-badge {
      background: #667eea;
      color: white;
      padding: 0.25rem 0.75rem;
      border-radius: 12px;
      font-size: 0.8rem;
      font-weight: bold;
    }

    .sender-info {
      display: flex;
      flex-direction: column;
      flex: 1;
    }

    .sender-name {
      font-weight: 600;
      color: #2d3748;
    }

    .revelation-type {
      font-size: 0.8rem;
      color: #718096;
    }

    .timestamp {
      font-size: 0.8rem;
      color: #a0aec0;
    }

    .revelation-content p {
      color: #4a5568;
      line-height: 1.6;
      margin: 0;
      font-size: 1rem;
    }

    .revelation-actions {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    .action-btn {
      padding: 0.5rem 1rem;
      border: 1px solid #e2e8f0;
      background: white;
      border-radius: 20px;
      cursor: pointer;
      font-size: 0.8rem;
      color: #718096;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .action-btn:hover {
      border-color: #667eea;
      color: #667eea;
    }

    .photo-reveal-section {
      margin-bottom: 2rem;
    }

    .photo-reveal-card {
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 215, 0, 0.05) 100%);
      border: 2px solid #ffd700;
      border-radius: 16px;
      padding: 2rem;
      text-align: center;
    }

    .photo-reveal-header h3 {
      color: #2d3748;
      margin: 0 0 0.5rem 0;
      font-size: 1.5rem;
    }

    .photo-reveal-header p {
      color: #718096;
      margin: 0 0 2rem 0;
    }

    .mutual-consent {
      margin-bottom: 2rem;
    }

    .consent-status {
      display: flex;
      justify-content: center;
      gap: 2rem;
      margin-bottom: 1.5rem;
    }

    .consent-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.5rem;
    }

    .consent-item .user {
      font-weight: 600;
      color: #2d3748;
    }

    .consent-item .status {
      padding: 0.5rem 1rem;
      border-radius: 20px;
      font-size: 0.9rem;
      background: #f7fafc;
      color: #718096;
    }

    .consent-item .status.agreed {
      background: #c6f6d5;
      color: #22543d;
    }

    .consent-btn {
      background: #ffd700;
      color: #744210;
      border: none;
      padding: 1rem 2rem;
      border-radius: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease;
    }

    .consent-btn:hover:not(:disabled) {
      transform: translateY(-1px);
    }

    .consent-btn.agreed {
      background: #48bb78;
      color: white;
    }

    .photo-revealed h4 {
      color: #2d3748;
      margin: 0 0 1rem 0;
    }

    .photo-revealed p {
      color: #718096;
      margin: 0 0 2rem 0;
    }

    .view-profile-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      padding: 1rem 2rem;
      border-radius: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }

    .view-profile-btn:hover {
      transform: translateY(-1px);
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
      .revelations-container {
        padding: 0.5rem;
      }

      .revelation-progress {
        padding: 1rem;
      }

      .day-circles {
        overflow-x: auto;
        gap: 0.5rem;
      }

      .revelation-item.sent {
        margin-left: 0;
      }

      .revelation-item.received {
        margin-right: 0;
      }

      .consent-status {
        flex-direction: column;
        gap: 1rem;
      }
    }

    /* Keyboard navigation styles */
    .keyboard-focused {
      outline: 2px solid var(--primary-color, #ec4899) !important;
      outline-offset: 2px;
      box-shadow: 0 0 0 4px rgba(236, 72, 153, 0.2);
      transition: all 0.2s ease;
    }

    .keyboard-highlighted {
      background-color: var(--highlight-bg, rgba(236, 72, 153, 0.1));
      border: 2px solid var(--primary-color, #ec4899);
      transform: scale(1.02);
      transition: all 0.3s ease;
    }

    .day-circle {
      cursor: pointer;
      transition: all 0.3s ease;
      position: relative;
    }

    .day-circle:hover,
    .day-circle:focus {
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .day-circle.keyboard-highlighted {
      transform: scale(1.08);
      box-shadow: 0 6px 20px rgba(236, 72, 153, 0.3);
    }

    .day-circle:focus-visible {
      outline: 2px solid var(--primary-color, #ec4899);
      outline-offset: 4px;
    }

    .revelation-item {
      transition: all 0.3s ease;
      cursor: pointer;
    }

    .revelation-item:hover,
    .revelation-item:focus {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }

    .revelation-item.keyboard-highlighted {
      transform: translateY(-4px);
      box-shadow: 0 12px 35px rgba(236, 72, 153, 0.2);
      border-left: 4px solid var(--primary-color, #ec4899);
    }

    .revelation-item:focus-visible {
      outline: 2px solid var(--primary-color, #ec4899);
      outline-offset: 2px;
    }

    /* Enhanced focus styles for form elements */
    #revelation-content:focus {
      outline: 2px solid var(--primary-color, #ec4899);
      outline-offset: 2px;
      box-shadow: 0 0 0 4px rgba(236, 72, 153, 0.1);
      border-color: var(--primary-color, #ec4899);
    }

    .share-btn:focus,
    .action-btn:focus,
    .consent-btn:focus {
      outline: 2px solid var(--primary-color, #ec4899);
      outline-offset: 2px;
      box-shadow: 0 0 0 4px rgba(236, 72, 153, 0.2);
    }

    /* Screen reader only content */
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }

    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
      .keyboard-focused,
      .keyboard-highlighted,
      .day-circle,
      .revelation-item {
        transition: none !important;
        animation: none !important;
      }
    }

    /* High contrast mode support */
    @media (prefers-contrast: high) {
      .keyboard-focused,
      .keyboard-highlighted {
        outline-width: 3px;
        outline-style: solid;
        outline-color: ButtonText;
      }
    }
  `]
})
export class RevelationsComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('revelationContainer', { static: false }) revelationContainer!: ElementRef;
  connectionId: number | null = null;
  timeline: RevelationTimeline | null = null;
  currentPrompt: RevelationPrompt | null = null;
  revelationForm: FormGroup;
  loading = true;
  submitting = false;
  currentUserId = 1; // Mock current user ID
  partnerName = 'Alex'; // Mock partner name
  userConsent = false;
  partnerConsent = false;
  photoRevealed = false;
  streakCount = 0;
  showCelebrate = false;
  confettiPieces = Array.from({ length: 24 }).map((_, i) => i);
  whatsNext: string | null = null;

  // Keyboard navigation
  private keyboardNavSubscription?: Subscription;
  private isKeyboardNavigationEnabled = true;

  constructor(
    private revelationService: RevelationService,
    private soulConnectionService: SoulConnectionService,
    private route: ActivatedRoute,
    private router: Router,
    private formBuilder: FormBuilder,
    private hapticFeedbackService: HapticFeedbackService,
    private keyboardNavigationService: RevelationKeyboardNavigationService,
    private dialog: MatDialog
  ) {
    this.revelationForm = this.formBuilder.group({
      content: ['', [Validators.required, Validators.minLength(20)]]
    });
  }

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      if (params['connectionId']) {
        this.connectionId = +params['connectionId'];
        this.loadRevelationData();
      } else {
        // No connectionId provided - show empty state
        this.loading = false;
      }
    });
  }

  ngAfterViewInit() {
    this.initializeKeyboardNavigation();
  }

  ngOnDestroy() {
    this.keyboardNavigationService.destroy();
    if (this.keyboardNavSubscription) {
      this.keyboardNavSubscription.unsubscribe();
    }
  }

  loadRevelationData() {
    if (!this.connectionId) return;

    this.loading = true;

    // Load timeline and current prompt
    const timeline$ = this.revelationService.getRevelationTimeline(this.connectionId);
    const prompts$ = this.revelationService.getRevelationPrompts();

    timeline$.subscribe({
      next: (timeline) => {
        this.timeline = timeline;
        this.updateStreakAndTips();
        this.checkForPhotoReveal(timeline);

        if (!timeline.is_cycle_complete && timeline.current_day <= 7) {
          prompts$.subscribe({
            next: (prompts) => {
              this.currentPrompt = prompts.find(p => p.day_number === timeline.current_day) || null;
            },
            error: (error) => {
              console.error('Error loading revelation prompts:', error);
            }
          });
        }

        // Mock photo reveal status for day 7
        if (timeline.current_day === 7 || timeline.is_cycle_complete) {
          this.userConsent = Math.random() > 0.5;
          this.partnerConsent = Math.random() > 0.5;
          this.photoRevealed = this.userConsent && this.partnerConsent;
        }

        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading revelation data:', error);
        this.loading = false;
      }
    });
  }

  private updateStreakAndTips(): void {
    if (!this.timeline) return;
    const day = this.timeline.current_day;
    this.streakCount = Math.max(0, day - 1);
    // Show celebration on day edges and completion
    this.showCelebrate = day === 7 || this.timeline.is_cycle_complete || day === 1;
    // Minimal reduced-motion guard via CSS is assumed; could be toggled via settings service

    // Provide contextual next-step tips
    const tips: Record<number, string> = {
      1: 'Reflect on your core values and keep it authentic. Tomorrow builds on this.',
      2: 'Share a story with a feeling. Specifics create connection.',
      3: 'Dreams reveal alignment. Be bold about where you’re headed.',
      4: 'Lightness matters. A moment that made you truly laugh works great.',
      5: 'Vulnerability is strength. Keep it respectful and honest.',
      6: 'Describe your ideal connection in everyday terms.',
      7: 'If you both consent, photos reveal today. Keep the good vibes going.'
    };
    this.whatsNext = tips[day] || null;
  }

  get sortedRevelations(): DailyRevelation[] {
    if (!this.timeline) return [];
    return [...this.timeline.revelations].sort((a, b) =>
      a.day_number - b.day_number || new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
  }

  getDayLabel(day: number): string {
    const labels = {
      1: 'Personal Value',
      2: 'Life Experience',
      3: 'Hope & Dream',
      4: 'What Makes You Laugh',
      5: 'Challenge Overcome',
      6: 'Ideal Connection',
      7: 'Photo Reveal'
    };
    return labels[day as keyof typeof labels] || '';
  }

  formatRevelationType(type: string): string {
    return type.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  shareRevelation() {
    if (this.revelationForm.invalid || !this.connectionId || !this.currentPrompt) {
      return;
    }

    this.submitting = true;

    const revelationData = {
      connection_id: this.connectionId,
      day_number: this.currentPrompt.day_number,
      revelation_type: this.currentPrompt.revelation_type as RevelationType,
      content: this.revelationForm.get('content')?.value
    };

    this.revelationService.createRevelation(revelationData).subscribe({
      next: () => {
        // Enhanced haptic feedback for revelation step completion
        const dayNumber = this.currentPrompt?.day_number || 1;
        this.hapticFeedbackService.triggerRevelationStepCelebration(dayNumber);

        // Reset form and reload data
        this.revelationForm.reset();
        this.loadRevelationData();
        this.submitting = false;
      },
      error: (error) => {
        console.error('Error sharing revelation:', error);
        this.submitting = false;
      }
    });
  }

  markAsRead(revelation: DailyRevelation) {
    this.revelationService.updateRevelation(revelation.id, { is_read: true }).subscribe({
      next: () => {
        revelation.is_read = true;
      },
      error: (error) => {
        console.error('Error marking revelation as read:', error);
      }
    });
  }

  async reactToRevelation(revelation: DailyRevelation, emoji: string = '❤️') {
    try {
      await this.revelationService.reactToRevelation(revelation.id, emoji).toPromise();

      // Update local state if needed
      if (!revelation.reactions) {
        revelation.reactions = {};
      }
      revelation.reactions[this.currentUserId.toString()] = {
        emoji,
        timestamp: new Date().toISOString()
      };

      // Enhanced haptic feedback for revelation reactions
      this.hapticFeedbackService.triggerSelectionFeedback();

      console.log(`Reacted to revelation ${revelation.id} with ${emoji}`);
    } catch (error) {
      console.error('Error reacting to revelation:', error);
    }
  }

  async togglePhotoConsent() {
    if (!this.connectionId || this.userConsent) return;

    try {
      const response = await this.revelationService.givePhotoConsent(this.connectionId).toPromise() as Record<string, unknown> | undefined;

      this.userConsent = true;
      this.photoRevealed = (response?.['mutualConsent'] as boolean) || false;

      if (this.photoRevealed) {
        this.showCelebrate = true;

        // Enhanced haptic feedback for photo reveal celebration
        this.hapticFeedbackService.triggerPhotoRevealCelebration();

        // Hide celebration after animation
        setTimeout(() => {
          this.showCelebrate = false;
        }, 3000);
      }
    } catch (error) {
      console.error('Error giving photo consent:', error);
    }
  }

  viewFullProfile() {
    // Navigate to partner's full profile
    this.router.navigate(['/profile'], {
      queryParams: { userId: 'partner' }
    });
  }

  startRevelationJourney() {
    this.router.navigate(['/discover']);
  }

  learnAboutRevelations() {
    this.router.navigate(['/help/revelations']);
  }

  checkForPhotoReveal(timeline: RevelationTimelineResponse): void {
    if (timeline.current_day < 7 || !timeline.is_cycle_complete) return;

    const partnerName = this.partnerName ?? 'your match';
    const dialogRef = this.dialog.open(PhotoRevealConsentDialogComponent, {
      width: '380px',
      disableClose: true,
      data: { partnerName }
    });

    dialogRef.afterClosed().subscribe((consented: boolean) => {
      if (consented && this.connectionId) {
        this.soulConnectionService.updateSoulConnection(
          this.connectionId,
          { mutual_reveal_consent: true }
        ).subscribe();
      }
    });
  }

  goBack() {
    this.router.navigate(['/matches']);
  }

  /**
   * Handle keyboard events in the revelation form
   */
  handleFormKeydown(event: KeyboardEvent): void {
    const { key, ctrlKey, metaKey } = event;

    // Ctrl/Cmd + Enter to submit form
    if ((ctrlKey || metaKey) && key === 'Enter') {
      event.preventDefault();
      if (this.revelationForm.valid) {
        this.shareRevelation();
      }
    }

    // Escape to blur form
    if (key === 'Escape') {
      (event.target as HTMLElement).blur();
    }
  }

  /**
   * Handle keyboard events on timeline items
   */
  handleTimelineItemKeydown(event: KeyboardEvent, revelation: DailyRevelation): void {
    const { key } = event;

    switch (key) {
      case 'Enter':
      case ' ':
        {
          event.preventDefault();
          // Focus on the first action button if available
          const actionButtons = (event.target as HTMLElement).querySelectorAll('.action-btn');
          if (actionButtons.length > 0) {
            (actionButtons[0] as HTMLElement).focus();
          }
        }
        break;
      case 'r':
        // Quick read action
        if (revelation.sender_id !== this.currentUserId) {
          this.markAsRead(revelation);
        }
        break;
      case 'h':
        // Quick react action
        if (revelation.sender_id !== this.currentUserId) {
          this.reactToRevelation(revelation);
        }
        break;
    }
  }

  /**
   * Initialize keyboard navigation for the revelations component
   */
  private initializeKeyboardNavigation(): void {
    if (!this.revelationContainer || !this.isKeyboardNavigationEnabled) return;

    this.keyboardNavigationService.initialize(this.revelationContainer, {
      enableArrowKeys: true,
      enableTabTrapping: true,
      enableShortcuts: true,
      announceChanges: true
    });

    // Listen to navigation events
    this.keyboardNavSubscription = this.keyboardNavigationService.navigationEvents$.subscribe(
      event => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        this.handleKeyboardNavigationEvent(event as any);
      }
    );

    // Update navigable elements when the view changes
    setTimeout(() => {
      this.keyboardNavigationService.updateNavigableElements();
    }, 100);
  }

  /**
   * Handle keyboard navigation events
   */
  private handleKeyboardNavigationEvent(event: {action: string; element?: HTMLElement; index?: number}): void {
    const { action, element } = event;

    switch (action) {
      case 'navigate':
        // Trigger haptic feedback for navigation
        // Removed call to non-existent method: this.hapticFeedbackService.triggerRevelationStepCelebration();

        // Update UI state based on navigation
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        if (element && (element as any).type === 'step') {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          this.highlightCurrentDay((element as any).element);
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } else if (element && (element as any).type === 'timeline-item') {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          this.highlightTimelineItem((element as any).element);
        }
        break;
    }
  }

  /**
   * Highlight the current day being focused
   */
  private highlightCurrentDay(dayElement: HTMLElement): void {
    // Remove previous highlights
    const allDayCircles = this.revelationContainer.nativeElement.querySelectorAll('.day-circle');
    allDayCircles.forEach((circle: Element) => circle.classList.remove('keyboard-highlighted'));

    // Add highlight to current day
    dayElement.classList.add('keyboard-highlighted');

    // Announce day information
    const dayNumber = dayElement.querySelector('.day-number')?.textContent;
    const dayLabel = dayElement.querySelector('.day-label')?.textContent;
    if (dayNumber && dayLabel) {
      this.announceToScreenReader(`Day ${dayNumber}: ${dayLabel}`);
    }
  }

  /**
   * Highlight the current timeline item being focused
   */
  private highlightTimelineItem(itemElement: HTMLElement): void {
    // Remove previous highlights
    const allTimelineItems = this.revelationContainer.nativeElement.querySelectorAll('.revelation-item');
    allTimelineItems.forEach((item: Element) => item.classList.remove('keyboard-highlighted'));

    // Add highlight to current item
    itemElement.classList.add('keyboard-highlighted');

    // Announce timeline item information
    const dayBadge = itemElement.querySelector('.day-badge')?.textContent;
    const senderName = itemElement.querySelector('.sender-name')?.textContent;
    const revelationType = itemElement.querySelector('.revelation-type')?.textContent;

    if (dayBadge && senderName && revelationType) {
      this.announceToScreenReader(`${dayBadge} revelation from ${senderName}: ${revelationType}`);
    }
  }

  /**
   * Update keyboard navigation when the view changes
   */
  updateKeyboardNavigation(): void {
    if (this.keyboardNavigationService) {
      setTimeout(() => {
        this.keyboardNavigationService.updateNavigableElements();
      }, 50);
    }
  }

  /**
   * Navigate to a specific day programmatically
   */
  navigateToDay(day: number): void {
    this.keyboardNavigationService.navigateToDay(day);
  }

  /**
   * Focus the revelation form for immediate input
   */
  focusRevelationForm(): void {
    this.keyboardNavigationService.focusRevelationForm();
  }

  /**
   * Navigate through timeline items
   */
  navigateTimeline(direction: 'next' | 'previous'): void {
    this.keyboardNavigationService.navigateTimelineItems(direction);
  }

  /**
   * Toggle keyboard navigation on/off
   */
  toggleKeyboardNavigation(): void {
    this.isKeyboardNavigationEnabled = !this.isKeyboardNavigationEnabled;

    if (this.isKeyboardNavigationEnabled) {
      this.initializeKeyboardNavigation();
    } else {
      this.keyboardNavigationService.destroy();
    }

    this.announceToScreenReader(
      `Keyboard navigation ${this.isKeyboardNavigationEnabled ? 'enabled' : 'disabled'}`
    );
  }

  /**
   * Get keyboard navigation help text
   */
  getKeyboardHelpText(): string {
    return `
      Keyboard Navigation Help:
      • Arrow Keys: Navigate between elements
      • Tab/Shift+Tab: Move forward/backward
      • Enter/Space: Activate buttons
      • Home/End: Go to first/last element
      • Ctrl+F: Focus revelation form
      • Ctrl+T: Navigate timeline items
      • Ctrl+1-7: Jump to specific day
      • Escape: Exit navigation mode
    `;
  }

  /**
   * Announce messages to screen readers
   */
  private announceToScreenReader(message: string): void {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    setTimeout(() => {
      if (announcement.parentNode) {
        document.body.removeChild(announcement);
      }
    }, 1000);
  }
}
