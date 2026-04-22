import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

export type DfCardLayout = 'connection' | 'revelation';

@Component({
  selector: 'df-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<ng-content></ng-content>`,
})
export class DfCardComponent {
  @Input() layout: DfCardLayout = 'connection';

  @HostBinding('class')
  get hostClasses(): string {
    return `df-card df-card--${this.layout}`;
  }
}
