import { Directive, HostBinding } from '@angular/core';

@Directive({
  selector: 'input[dfInput], textarea[dfInput]',
  standalone: true,
})
export class DfInputDirective {
  @HostBinding('class.df-input') readonly baseClass = true;
}
