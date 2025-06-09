import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { MatchesComponent } from './matches.component';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    RouterModule,
    MatchesComponent
  ],
  exports: [MatchesComponent]
})
export class MatchesModule { }