import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';

import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatCheckboxModule,
    MatProgressSpinnerModule,
    MatDividerModule
  ]
})
export class LoginComponent implements OnInit {
  loginForm: FormGroup;
  isLoading = false;
  error: string | null = null;
  hidePassword = true;
  returnUrl: string = '/discover';
  currentYear = new Date().getFullYear();

  constructor(
    private readonly fb: FormBuilder,
    private readonly authService: AuthService,
    private readonly router: Router
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      rememberMe: [false]
    });

    // Get return url from route parameters or default to '/discover'
    const navigation = this.router.getCurrentNavigation();
    if (navigation?.extras.state) {
      this.returnUrl = navigation.extras.state['returnUrl'] ?? '/discover';
    }
  }

  ngOnInit(): void {
    // Reset any existing auth errors on component init
    this.error = null;
  }

  onSubmit(): void {
    if (this.loginForm.valid) {
      const { email, password, rememberMe } = this.loginForm.value;

      if (!email || !password) {
        this.error = 'Please enter both email and password';
        return;
      }

      this.isLoading = true;
      this.error = null;

      this.authService.login(email, password).subscribe({
        next: () => {
          // Store remember me preference if needed
          if (rememberMe) {
            localStorage.setItem('rememberMe', 'true');
          }
          this.router.navigate([this.returnUrl], { replaceUrl: true });
        },
        error: (err: HttpErrorResponse) => {
          console.error('Login error:', err);
          this.error = err.message ?? 'Invalid email or password';
          this.isLoading = false;
        }
      });
    } else {
      this.loginForm.markAllAsTouched();
    }
  }

  togglePasswordVisibility(): void {
    this.hidePassword = !this.hidePassword;
  }

  navigateToRegister(): void {
    this.router.navigate(['/register']);
  }

  navigateToForgotPassword(): void {
    this.router.navigate(['/forgot-password']);
  }

  // Social login methods temporarily disabled until backend implementation
  loginWithGoogle(): void {
    this.error = 'Google login is not implemented yet';
  }

  loginWithFacebook(): void {
    this.error = 'Facebook login is not implemented yet';
  }
}
