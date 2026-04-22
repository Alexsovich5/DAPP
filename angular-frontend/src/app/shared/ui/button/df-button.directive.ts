import { Directive, HostBinding, Input } from '@angular/core';

export type DfButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type DfButtonSize = 'sm' | 'md' | 'lg';

@Directive({
  selector: 'button[dfButton], a[dfButton]',
  standalone: true,
})
export class DfButtonDirective {
  @Input() variant: DfButtonVariant = 'primary';
  @Input() size: DfButtonSize = 'md';

  @HostBinding('class.df-btn') readonly baseClass = true;

  @HostBinding('class')
  get hostClasses(): string {
    return `df-btn df-btn--${this.variant} df-btn--${this.size}`;
  }
}
