import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { SoulConnectionService } from '@core/services/soul-connection.service';
import { DiscoveryResponse } from '../../core/interfaces/soul-connection.interfaces';
import {
  DfAvatarComponent,
  DfButtonDirective,
  DfCardComponent,
  DfChipComponent,
} from '../../shared/ui';

@Component({
  selector: 'app-discover',
  standalone: true,
  imports: [
    CommonModule,
    DfAvatarComponent,
    DfButtonDirective,
    DfCardComponent,
    DfChipComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './discover.component.html',
  styleUrls: ['./discover.component.scss'],
})
export class DiscoverComponent implements OnInit {
  potentialMatches: DiscoveryResponse[] = [];
  focalIndex = 0;
  isLoading = false;
  error: string | null = null;

  constructor(
    private readonly soulConnectionService: SoulConnectionService,
    private readonly router: Router,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.load();
  }

  get focalCard(): DiscoveryResponse | null {
    return this.potentialMatches[this.focalIndex] ?? null;
  }

  get peekCards(): DiscoveryResponse[] {
    return this.potentialMatches
      .filter((_, i) => i !== this.focalIndex)
      .slice(0, 2);
  }

  load(): void {
    this.isLoading = true;
    this.error = null;
    this.soulConnectionService.discoverSoulConnections({}).subscribe({
      next: (data) => {
        this.potentialMatches = data ?? [];
        this.focalIndex = 0;
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.error = err?.message ?? 'Could not load matches.';
        this.isLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  promotePeek(userId: number): void {
    const idx = this.potentialMatches.findIndex((m) => m.user_id === userId);
    if (idx >= 0) {
      this.focalIndex = idx;
      this.cdr.markForCheck();
    }
  }

  beginConnection(match: DiscoveryResponse): void {
    this.soulConnectionService.initiateSoulConnection({ user2_id: match.user_id }).subscribe({
      next: (connection) => this.router.navigate(['/messages', connection.id]),
      error: () => { /* surfaced via toast service in future; keep form simple here */ },
    });
  }

  pass(match: DiscoveryResponse): void {
    this.potentialMatches = this.potentialMatches.filter((m) => m.user_id !== match.user_id);
    if (this.focalIndex >= this.potentialMatches.length) {
      this.focalIndex = Math.max(0, this.potentialMatches.length - 1);
    }
    this.cdr.markForCheck();
  }
}
