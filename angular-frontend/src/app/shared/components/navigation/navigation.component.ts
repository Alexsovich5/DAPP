import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-navigation',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <nav class="main-navigation" *ngIf="isLoggedIn$ | async">
      <div class="nav-container">
        <div class="nav-brand">
          <a routerLink="/" class="brand-link">
            <span class="brand-icon">💫</span>
            <span class="brand-text">Dinner1</span>
          </a>
        </div>

        <div class="nav-menu" [class.mobile-open]="mobileMenuOpen">
          <a 
            routerLink="/discover" 
            routerLinkActive="active"
            class="nav-link"
            (click)="closeMobileMenu()"
          >
            <span class="nav-icon">🔍</span>
            <span class="nav-text">Discover</span>
          </a>

          <a 
            routerLink="/matches" 
            routerLinkActive="active"
            class="nav-link"
            (click)="closeMobileMenu()"
          >
            <span class="nav-icon">💫</span>
            <span class="nav-text">Connections</span>
          </a>

          <a 
            routerLink="/messages" 
            routerLinkActive="active"
            class="nav-link"
            (click)="closeMobileMenu()"
          >
            <span class="nav-icon">💬</span>
            <span class="nav-text">Messages</span>
          </a>

          <a 
            routerLink="/revelations" 
            routerLinkActive="active"
            class="nav-link revelation-link"
            (click)="closeMobileMenu()"
          >
            <span class="nav-icon">✨</span>
            <span class="nav-text">Revelations</span>
          </a>

          <a 
            routerLink="/notifications" 
            routerLinkActive="active"
            class="nav-link notification-link"
            (click)="closeMobileMenu()"
          >
            <span class="nav-icon">🔔</span>
            <span class="nav-text">Notifications</span>
            <span class="notification-badge" *ngIf="(unreadCount$ | async) as unreadCount; and unreadCount > 0">
              {{unreadCount}}
            </span>
          </a>
        </div>

        <div class="nav-actions">
          <div class="user-menu" [class.open]="userMenuOpen" (click)="toggleUserMenu()">
            <div class="user-avatar">
              <span>{{getUserInitial()}}</span>
            </div>
            <div class="user-dropdown" *ngIf="userMenuOpen">
              <a routerLink="/profile" class="dropdown-item" (click)="closeUserMenu()">
                <span>👤</span> Profile
              </a>
              <a routerLink="/settings" class="dropdown-item" (click)="closeUserMenu()">
                <span>⚙️</span> Settings
              </a>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item logout-btn" (click)="logout()">
                <span>🚪</span> Logout
              </button>
            </div>
          </div>

          <button class="mobile-menu-btn" (click)="toggleMobileMenu()">
            <span class="hamburger" [class.open]="mobileMenuOpen">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </button>
        </div>
      </div>
    </nav>
  `,
  styles: [`
    .main-navigation {
      background: white;
      border-bottom: 1px solid #e2e8f0;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
      position: sticky;
      top: 0;
      z-index: 1000;
    }

    .nav-container {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1rem;
    }

    .nav-brand {
      display: flex;
      align-items: center;
    }

    .brand-link {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      text-decoration: none;
      color: #2d3748;
      font-weight: 700;
      font-size: 1.2rem;
      transition: color 0.2s ease;
    }

    .brand-link:hover {
      color: #667eea;
    }

    .brand-icon {
      font-size: 1.5rem;
    }

    .nav-menu {
      display: flex;
      align-items: center;
      gap: 2rem;
    }

    .nav-link {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.25rem;
      text-decoration: none;
      color: #718096;
      transition: all 0.2s ease;
      padding: 0.5rem;
      border-radius: 8px;
      position: relative;
    }

    .nav-link:hover {
      color: #667eea;
      background: rgba(102, 126, 234, 0.05);
    }

    .nav-link.active {
      color: #667eea;
      background: rgba(102, 126, 234, 0.1);
    }

    .nav-icon {
      font-size: 1.2rem;
    }

    .nav-text {
      font-size: 0.8rem;
      font-weight: 500;
    }

    .revelation-link:hover,
    .revelation-link.active {
      color: #ffd700;
      background: rgba(255, 215, 0, 0.1);
    }

    .notification-link {
      position: relative;
    }

    .notification-badge {
      position: absolute;
      top: -2px;
      right: -2px;
      background: #f56565;
      color: white;
      border-radius: 50%;
      width: 18px;
      height: 18px;
      font-size: 0.7rem;
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid white;
    }

    .nav-actions {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .user-menu {
      position: relative;
      cursor: pointer;
    }

    .user-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: bold;
      transition: transform 0.2s ease;
    }

    .user-menu:hover .user-avatar {
      transform: scale(1.05);
    }

    .user-dropdown {
      position: absolute;
      top: 100%;
      right: 0;
      margin-top: 0.5rem;
      background: white;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
      min-width: 180px;
      overflow: hidden;
      z-index: 1001;
    }

    .dropdown-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      text-decoration: none;
      color: #4a5568;
      transition: background 0.2s ease;
      border: none;
      background: none;
      width: 100%;
      text-align: left;
      cursor: pointer;
      font-size: 0.9rem;
    }

    .dropdown-item:hover {
      background: #f7fafc;
    }

    .logout-btn:hover {
      background: #fed7d7;
      color: #c53030;
    }

    .dropdown-divider {
      height: 1px;
      background: #e2e8f0;
      margin: 0.5rem 0;
    }

    .mobile-menu-btn {
      display: none;
      background: none;
      border: none;
      cursor: pointer;
      padding: 0.5rem;
    }

    .hamburger {
      display: flex;
      flex-direction: column;
      gap: 3px;
      transition: transform 0.3s ease;
    }

    .hamburger span {
      width: 20px;
      height: 2px;
      background: #718096;
      transition: all 0.3s ease;
    }

    .hamburger.open {
      transform: rotate(45deg);
    }

    .hamburger.open span:first-child {
      transform: rotate(90deg) translate(5px, 0);
    }

    .hamburger.open span:nth-child(2) {
      opacity: 0;
    }

    .hamburger.open span:last-child {
      transform: rotate(-90deg) translate(5px, 0);
    }

    @media (max-width: 768px) {
      .nav-menu {
        position: fixed;
        top: 70px;
        left: 0;
        right: 0;
        background: white;
        flex-direction: column;
        padding: 1rem;
        border-bottom: 1px solid #e2e8f0;
        transform: translateY(-100%);
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        gap: 1rem;
      }

      .nav-menu.mobile-open {
        transform: translateY(0);
        opacity: 1;
        visibility: visible;
      }

      .nav-link {
        flex-direction: row;
        justify-content: flex-start;
        width: 100%;
        padding: 1rem;
        gap: 1rem;
      }

      .mobile-menu-btn {
        display: block;
      }

      .brand-text {
        display: none;
      }

      .nav-text {
        font-size: 1rem;
      }
    }

    @media (max-width: 480px) {
      .nav-container {
        padding: 0.5rem 1rem;
      }

      .brand-text {
        display: none;
      }
    }
  `]
})
export class NavigationComponent implements OnInit {
  isLoggedIn$: Observable<boolean>;
  unreadCount$: Observable<number>;
  mobileMenuOpen = false;
  userMenuOpen = false;

  constructor(
    private authService: AuthService,
    private notificationService: NotificationService,
    private router: Router
  ) {
    this.isLoggedIn$ = this.authService.isLoggedIn();
    this.unreadCount$ = this.notificationService.getUnreadCount();
  }

  ngOnInit() {
    // Close menus when route changes
    this.router.events.subscribe(() => {
      this.closeMobileMenu();
      this.closeUserMenu();
    });

    // Close menus when clicking outside
    document.addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.user-menu')) {
        this.closeUserMenu();
      }
      if (!target.closest('.nav-menu') && !target.closest('.mobile-menu-btn')) {
        this.closeMobileMenu();
      }
    });
  }

  getUserInitial(): string {
    // Mock user initial - in real app, get from user service
    return 'U';
  }

  toggleMobileMenu() {
    this.mobileMenuOpen = !this.mobileMenuOpen;
  }

  closeMobileMenu() {
    this.mobileMenuOpen = false;
  }

  toggleUserMenu() {
    this.userMenuOpen = !this.userMenuOpen;
  }

  closeUserMenu() {
    this.userMenuOpen = false;
  }

  async logout() {
    try {
      await this.authService.logout();
      this.router.navigate(['/']);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }
}