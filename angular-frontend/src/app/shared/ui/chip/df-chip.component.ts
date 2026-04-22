import { ChangeDetectionStrategy, Component, HostBinding, Input } from '@angular/core';

export type DfChipPurpose = 'stage' | 'interest' | 'counter';

@Component({
  selector: 'df-chip',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<ng-content></ng-content>`,
})
export class DfChipComponent {
  @Input() purpose: DfChipPurpose = 'interest';

  @HostBinding('class')
  get hostClasses(): string {
    return `df-chip df-chip--${this.purpose}`;
  }
}
