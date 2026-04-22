import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

export interface PhotoRevealConsentData {
  partnerName: string;
}

@Component({
  selector: 'app-photo-reveal-consent-dialog',
  standalone: true,
  imports: [MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <div class="consent-dialog">
      <div class="dialog-icon">
        <mat-icon aria-hidden="true">photo_camera</mat-icon>
      </div>
      <h2 mat-dialog-title id="consent-title">Day 7 — Photo Reveal</h2>
      <mat-dialog-content>
        <p id="consent-desc">
          You and <strong>{{ data.partnerName }}</strong> have completed your 7-day soul journey.
          Would you like to reveal your photos to each other?
        </p>
        <p class="consent-note">
          Both of you must consent before photos are shown. This moment is mutual.
        </p>
      </mat-dialog-content>
      <mat-dialog-actions align="end">
        <button mat-stroked-button type="button" (click)="onDecline()">Not yet</button>
        <button mat-raised-button color="primary" type="button" (click)="onConsent()">
          <mat-icon>favorite</mat-icon>
          Yes, reveal photos
        </button>
      </mat-dialog-actions>
    </div>
  `,
  styles: [`
    .consent-dialog {
      padding: 8px;
      text-align: center;
      max-width: 360px;
    }
    .dialog-icon mat-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: var(--interactive-primary);
      margin-bottom: 8px;
    }
    h2 { margin: 0 0 8px; }
    .consent-note {
      font-size: 0.85rem;
      color: var(--color-text-muted);
      margin-top: 8px;
    }
    mat-dialog-actions {
      gap: 8px;
      padding-bottom: 8px;
    }
    button[mat-raised-button] mat-icon {
      margin-right: 4px;
      font-size: 18px;
      vertical-align: middle;
    }
  `]
})
export class PhotoRevealConsentDialogComponent {
  constructor(
    private dialogRef: MatDialogRef<PhotoRevealConsentDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public readonly data: PhotoRevealConsentData
  ) {}

  onConsent(): void {
    this.dialogRef.close(true);
  }

  onDecline(): void {
    this.dialogRef.close(false);
  }
}
