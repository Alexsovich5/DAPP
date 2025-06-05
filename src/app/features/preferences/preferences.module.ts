import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PreferencesComponent } from './preferences.component';

const routes: Routes = [
  { path: '', component: PreferencesComponent }
];

@NgModule({
  imports: [
    PreferencesComponent,
    RouterModule.forChild(routes)
  ]
})
export class PreferencesModule { }
