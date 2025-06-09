import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { NotificationsComponent } from './notifications.component';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    RouterModule,
    NotificationsComponent
  ],
  exports: [NotificationsComponent]
})
export class NotificationsModule { }