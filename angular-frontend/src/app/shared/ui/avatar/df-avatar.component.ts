import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

export type DfAvatarSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'df-avatar',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ng-container *ngIf="photoUrl; else monogramTpl">
      <img [src]="photoUrl" [alt]="name" />
    </ng-container>
    <ng-template #monogramTpl>
      <span class="df-avatar__monogram">{{ monogram }}</span>
    </ng-template>
  `,
})
export class DfAvatarComponent {
  @Input() name = '';
  @Input() size: DfAvatarSize = 'md';
  @Input() photoUrl?: string;

  @HostBinding('class')
  get hostClasses(): string {
    return `df-avatar df-avatar--${this.size}`;
  }

  get monogram(): string {
    const parts = (this.name || '').trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return '?';
    return parts.slice(0, 2).map(p => p[0]).join('').toUpperCase();
  }
}
