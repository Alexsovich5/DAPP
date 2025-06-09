import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { MessagesComponent } from './messages.component';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    RouterModule,
    MessagesComponent
  ],
  exports: [MessagesComponent]
})
export class MessagesModule { }