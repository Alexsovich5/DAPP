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
    <nav 
      class="main-navigation" 
      *ngIf="isLoggedIn$ | async"
      role="navigation"
      aria-label="Main navigation">
      <div class="nav-container">
        <div class="nav-brand">
          <a 
            routerLink="/" 
            class="brand-link"
            aria-label="Dinner First home page">
            <span class="brand-icon" aria-hidden="true">💫</span>
            <span class="brand-text">Dinner First</span>
          </a>
        </div>

        <div 
          class="nav-menu" 
          [class.mobile-open]="mobileMenuOpen"
          role="menubar"
          [attr.aria-expanded]="mobileMenuOpen"
          aria-label="Main menu">
          <a 
            routerLink="/discover" 
            routerLinkActive="active"
            class="nav-link"
            role="menuitem"
            aria-label="Discover soul connections"
            [attr.aria-current]="isActiveRoute('/discover') ? 'page' : null"
            (click)="closeMobileMenu()"
            (keydown.enter)="closeMobileMenu()"
            (keydown.space)="closeMobileMenu()"
          >
            <span class="nav-icon" aria-hidden="true">🔍</span>
            <span class="nav-text">Discover</span>
          </a>

          <a 
            routerLink="/conversations" 
            routerLinkActive="active"
            class="nav-link"
            role="menuitem"
            [attr.aria-label]="getConversationsAriaLabel()"
            [attr.aria-current]="isActiveRoute('/conversations') ? 'page' : null"
            (click)="closeMobileMenu()"
            (keydown.enter)="closeMobileMenu()"
            (keydown.space)="closeMobileMenu()"
          >
            <span class="nav-icon" aria-hidden="true">💬</span>
            <span class="nav-text">Conversations</span>
            <span 
              class="notification-badge" 
              *ngIf="(unreadCount$ | async) && (unreadCount$ | async)! > 0"
              [attr.aria-label]="(unreadCount$ | async) + ' unread messages'"
              role="status">
              {{unreadCount$ | async}}
            </span>
          </a>

          <a 
            routerLink="/revelations" 
            routerLinkActive="active"
            class="nav-link revelation-link"
            role="menuitem"
            aria-label="Daily revelations journey"
            [attr.aria-current]="isActiveRoute('/revelations') ? 'page' : null"
            (click)="closeMobileMenu()"
            (keydown.enter)="closeMobileMenu()"
            (keydown.space)="closeMobileMenu()"
          >
            <span class="nav-icon" aria-hidden="true">✨</span>
            <span class="nav-text">Revelations</span>
          </a>

        </div>

        <div class="nav-actions">
          <div 
            class="user-menu" 
            [class.open]="userMenuOpen"
            role="button"
            tabindex="0"
            [attr.aria-expanded]="userMenuOpen"
            aria-haspopup="true"
            aria-label="User menu"
            (click)="toggleUserMenu()"
            (keydown.enter)="toggleUserMenu()"
            (keydown.space)="toggleUserMenu(); $event.preventDefault()"
            (keydown.escape)="closeUserMenu()"
            (keydown.arrowdown)="openUserMenuAndFocus()"
            (blur)="onUserMenuBlur($event)">
            <div class="user-avatar" [attr.aria-label]="'User avatar for ' + getUserInitial()">
              <span aria-hidden="true">{{getUserInitial()}}</span>
            </div>
            <div 
              class="user-dropdown" 
              *ngIf="userMenuOpen"
              role="menu"
              aria-label="User menu options"
              (keydown)="handleDropdownKeydown($event)">
              <a 
                routerLink="/profile" 
                class="dropdown-item" 
                role="menuitem"
                tabindex="0"
                aria-label="View and edit your profile"
                (click)="closeUserMenu()"
                (keydown.enter)="closeUserMenu()">
                <span aria-hidden="true">👤</span> Profile
              </a>
              <a 
                routerLink="/settings" 
                class="dropdown-item" 
                role="menuitem"
                tabindex="0"
                aria-label="Application settings and preferences"
                (click)="closeUserMenu()"
                (keydown.enter)="closeUserMenu()">
                <span aria-hidden="true">⚙️</span> Settings
              </a>
              <div class="dropdown-divider" role="separator"></div>
              <button 
                class="dropdown-item logout-btn" 
                role="menuitem"
                tabindex="0"
                aria-label="Sign out of your account"
                (click)="logout()"
                (keydown.enter)="logout()">
                <span aria-hidden="true">🚪</span> Logout
              </button>
            </div>
          </div>

          <button 
            class="mobile-menu-btn" 
            type="button"
            [attr.aria-expanded]="mobileMenuOpen"
            aria-controls="mobile-navigation-menu"
            aria-label="Toggle mobile navigation menu"
            (click)="toggleMobileMenu()"
            (keydown.enter)="toggleMobileMenu()"
            (keydown.space)="toggleMobileMenu(); $event.preventDefault()">
            <span 
              class="hamburger" 
              [class.open]="mobileMenuOpen"
              aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </span>
            <span class="sr-only">
              {{mobileMenuOpen ? 'Close' : 'Open'}} navigation menu
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

    .nav-link {
      position: relative;
    }

    .notification-badge {
      position: absolute;
      top: -2px;
      right: -2px;
      background: #f56565;
      color: white;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      font-size: 0.75rem;
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid white;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
        padding: 1.5rem;
        border-bottom: 1px solid #e2e8f0;
        transform: translateY(-100%);
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        gap: 0.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
        padding: 1.25rem 1rem;
        gap: 1rem;
        min-height: 56px;
        border-radius: 12px;
        font-size: 1.1rem;
      }

      .nav-icon {
        font-size: 1.5rem;
        min-width: 24px;
      }

      .mobile-menu-btn {
        display: block;
        padding: 0.75rem;
        min-height: 44px;
        min-width: 44px;
      }

      .brand-text {
        display: none;
      }

      .nav-text {
        font-size: 1.1rem;
        font-weight: 500;
      }

      .notification-badge {
        position: static;
        margin-left: auto;
        width: 24px;
        height: 24px;
        font-size: 0.85rem;
      }
    }

    @media (max-width: 480px) {
      .nav-container {
        padding: 0.75rem 1rem;
      }

      .brand-link {
        font-size: 1.1rem;
      }

      .brand-icon {
        font-size: 1.4rem;
      }

      .brand-text {
        display: none;
      }

      .nav-link {
        padding: 1.5rem 1rem;
        min-height: 60px;
      }

      .nav-text {
        font-size: 1.2rem;
      }

      .nav-icon {
        font-size: 1.6rem;
      }
    }

    /* Accessibility styles */
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }

    /* Focus styles for keyboard navigation */
    .nav-link:focus,
    .brand-link:focus,
    .user-menu:focus,
    .mobile-menu-btn:focus,
    .dropdown-item:focus {
      outline: 2px solid #667eea;
      outline-offset: 2px;
      border-radius: 4px;
    }

    /* High contrast focus indicator */
    @media (prefers-contrast: high) {
      .nav-link:focus,
      .brand-link:focus,
      .user-menu:focus,
      .mobile-menu-btn:focus,
      .dropdown-item:focus {
        outline: 3px solid #000000;
        outline-offset: 2px;
      }
    }

    /* Ensure interactive elements meet minimum size requirements */
    .nav-link,
    .user-menu,
    .mobile-menu-btn,
    .dropdown-item {
      min-height: 44px;
      min-width: 44px;
    }

    /* Improve color contrast for text */
    .nav-link {
      color: #4a5568; /* Improved contrast ratio */
    }

    .nav-link:hover {
      color: #2d3748; /* Higher contrast on hover */
    }

    .nav-link.active {
      color: #2d3748; /* Higher contrast for active state */
      font-weight: 600;
    }

    /* Ensure notification badge has sufficient contrast */
    .notification-badge {
      background: #e53e3e; /* Improved contrast */
      color: #ffffff;
      font-weight: 700;
    }

    /* Focus management for dropdown */
    .user-dropdown {
      outline: none;
    }

    .user-dropdown:focus-within {
      box-shadow: 0 0 0 2px #667eea;
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

  isActiveRoute(route: string): boolean {
    return this.router.url === route;
  }

  getConversationsAriaLabel(): string {
    const unreadCount = this.notificationService.getCurrentUnreadCount();
    return unreadCount > 0 
      ? `Conversations with ${unreadCount} unread messages`
      : 'Conversations';
  }

  toggleMobileMenu() {
    this.mobileMenuOpen = !this.mobileMenuOpen;
    
    // Announce state change to screen readers
    this.announceToScreenReader(
      this.mobileMenuOpen ? 'Mobile menu opened' : 'Mobile menu closed'
    );
  }

  closeMobileMenu() {
    this.mobileMenuOpen = false;
  }

  toggleUserMenu() {
    this.userMenuOpen = !this.userMenuOpen;
    
    // Focus first menu item when opening
    if (this.userMenuOpen) {
      setTimeout(() => {
        const firstMenuItem = document.querySelector('.user-dropdown .dropdown-item') as HTMLElement;
        firstMenuItem?.focus();
      }, 0);
    }
  }

  openUserMenuAndFocus() {
    this.userMenuOpen = true;
    setTimeout(() => {
      const firstMenuItem = document.querySelector('.user-dropdown .dropdown-item') as HTMLElement;
      firstMenuItem?.focus();
    }, 0);
  }

  closeUserMenu() {
    this.userMenuOpen = false;
  }

  onUserMenuBlur(event: FocusEvent) {
    // Close menu if focus moves outside the user menu area
    setTimeout(() => {
      const activeElement = document.activeElement;
      const userMenu = document.querySelector('.user-menu');
      
      if (!userMenu?.contains(activeElement)) {
        this.closeUserMenu();
      }
    }, 0);
  }

  handleDropdownKeydown(event: KeyboardEvent) {
    const menuItems = Array.from(document.querySelectorAll('.user-dropdown .dropdown-item')) as HTMLElement[];
    const currentIndex = menuItems.findIndex(item => item === document.activeElement);
    
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        const nextIndex = (currentIndex + 1) % menuItems.length;
        menuItems[nextIndex]?.focus();
        break;
        
      case 'ArrowUp':
        event.preventDefault();
        const prevIndex = currentIndex <= 0 ? menuItems.length - 1 : currentIndex - 1;
        menuItems[prevIndex]?.focus();
        break;
        
      case 'Escape':
        event.preventDefault();
        this.closeUserMenu();
        (document.querySelector('.user-menu') as HTMLElement)?.focus();
        break;
        
      case 'Home':
        event.preventDefault();
        menuItems[0]?.focus();
        break;
        
      case 'End':
        event.preventDefault();
        menuItems[menuItems.length - 1]?.focus();
        break;
    }
  }

  private announceToScreenReader(message: string) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }

  async logout() {
    try {
      await this.authService.logout();
      this.announceToScreenReader('You have been logged out successfully');
      this.router.navigate(['/']);
    } catch (error) {
      console.error('Logout failed:', error);
      this.announceToScreenReader('Logout failed. Please try again.');
    }
  }
}