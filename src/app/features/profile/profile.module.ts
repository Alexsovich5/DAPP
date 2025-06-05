import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ProfileViewComponent } from './profile-view/profile-view.component';
import { ProfileEditComponent } from './profile-edit/profile-edit.component';

const routes: Routes = [
  { path: '', component: ProfileViewComponent },
  { path: 'edit', component: ProfileEditComponent }
];

@NgModule({
  imports: [
    ProfileViewComponent,
    ProfileEditComponent,
    RouterModule.forChild(routes)
  ]
})
export class ProfileModule { }
