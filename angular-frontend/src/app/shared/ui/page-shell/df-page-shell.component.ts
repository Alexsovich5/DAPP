import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

export type DfPageShellVariant = 'chat' | 'reading' | 'grid';

@Component({
  selector: 'df-page-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<ng-content></ng-content>`,
})
export class DfPageShellComponent {
  @Input() variant: DfPageShellVariant = 'grid';

  @HostBinding('class')
  get hostClasses(): string {
    return `df-page-shell df-page-shell--${this.variant}`;
  }
}
