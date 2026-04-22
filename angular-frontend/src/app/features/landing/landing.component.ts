import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { DfButtonDirective } from '../../shared/ui';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterLink, MatIconModule, DfButtonDirective],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss'],
})
export class LandingComponent {
  readonly steps = [
    { icon: 'psychology',   title: 'Discover souls',    body: 'Match on what you value — not what you look like.' },
    { icon: 'auto_stories', title: 'Reveal slowly',     body: 'Seven days of progressive revelation. One prompt a day.' },
    { icon: 'restaurant',   title: 'Meet over dinner',  body: 'If it still feels right, you plan one meal together.' },
  ];
}
