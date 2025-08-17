/**
 * Comprehensive Live Typing Indicators Tests - Maximum Coverage
 * Tests real-time typing indicators UI, animations, and user experience
 */

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { of, BehaviorSubject, Subject } from 'rxjs';

import { TypingIndicatorComponent } from './typing-indicator.component';
import { WebSocketService } from '../../../core/services/websocket.service';
import { AuthService } from '../../../core/services/auth.service';

interface TypingUser {
  user_id: number;
  user_name: string;
  connection_id: number;
  is_typing: boolean;
  started_at: string;
  avatar_url?: string;
}

interface TypingIndicatorConfig {
  showAvatars: boolean;
  showNames: boolean;
  maxVisibleUsers: number;
  animationDuration: number;
  timeoutDuration: number;
  enableSounds: boolean;
  compactMode: boolean;
}

describe('TypingIndicatorComponent', () => {
  let component: TypingIndicatorComponent;
  let fixture: ComponentFixture<TypingIndicatorComponent>;
  let webSocketService: jasmine.SpyObj<WebSocketService>;
  let authService: jasmine.SpyObj<AuthService>;
  let typingSubject: BehaviorSubject<TypingUser[]>;

  const mockCurrentUser = {
    id: 1,
    email: 'test@example.com',
    first_name: 'Test',
    avatar_url: 'https://example.com/avatar1.jpg'
  };

  const mockTypingUsers: TypingUser[] = [
    {
      user_id: 2,
      user_name: 'Emma',
      connection_id: 1,
      is_typing: true,
      started_at: new Date().toISOString(),
      avatar_url: 'https://example.com/avatar2.jpg'
    },
    {
      user_id: 3,
      user_name: 'Sofia',
      connection_id: 1,
      is_typing: true,
      started_at: new Date(Date.now() - 5000).toISOString(),
      avatar_url: 'https://example.com/avatar3.jpg'
    },
    {
      user_id: 4,
      user_name: 'Alexandra',
      connection_id: 1,
      is_typing: true,
      started_at: new Date(Date.now() - 2000).toISOString(),
      avatar_url: 'https://example.com/avatar4.jpg'
    }
  ];

  beforeEach(async () => {
    typingSubject = new BehaviorSubject<TypingUser[]>([]);

    const webSocketSpy = jasmine.createSpyObj('WebSocketService', [
      'onTypingIndicator',
      'sendTypingIndicator',
      'stopTypingIndicator',
      'getActiveTypingUsers'
    ]);

    const authSpy = jasmine.createSpyObj('AuthService', [
      'getCurrentUser'
    ]);

    await TestBed.configureTestingModule({
      declarations: [TypingIndicatorComponent],
      imports: [
        BrowserAnimationsModule,
        MatProgressSpinnerModule,
        MatChipsModule,
        MatIconModule
      ],
      providers: [
        { provide: WebSocketService, useValue: webSocketSpy },
        { provide: AuthService, useValue: authSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TypingIndicatorComponent);
    component = fixture.componentInstance;

    webSocketService = TestBed.inject(WebSocketService) as jasmine.SpyObj<WebSocketService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;

    // Default mocks
    authService.getCurrentUser.and.returnValue(of(mockCurrentUser));
    webSocketService.onTypingIndicator.and.returnValue(typingSubject.asObservable());
    webSocketService.getActiveTypingUsers.and.returnValue(mockTypingUsers);

    // Set default input
    component.connectionId = 1;
  });

  describe('Component Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should initialize with default configuration', () => {
      fixture.detectChanges();

      expect(component.config.showAvatars).toBe(true);
      expect(component.config.showNames).toBe(true);
      expect(component.config.maxVisibleUsers).toBe(3);
      expect(component.config.animationDuration).toBe(300);
    });

    it('should accept custom configuration', () => {
      const customConfig: Partial<TypingIndicatorConfig> = {
        maxVisibleUsers: 5,
        compactMode: true,
        enableSounds: false
      };

      component.config = { ...component.config, ...customConfig };
      fixture.detectChanges();

      expect(component.config.maxVisibleUsers).toBe(5);
      expect(component.config.compactMode).toBe(true);
      expect(component.config.enableSounds).toBe(false);
    });

    it('should subscribe to typing indicators on init', () => {
      fixture.detectChanges();

      expect(webSocketService.onTypingIndicator).toHaveBeenCalled();
      expect(component.typingUsers).toEqual([]);
    });

    it('should filter out current user from typing indicators', fakeAsync(() => {
      const usersWithSelf = [
        ...mockTypingUsers,
        {
          user_id: 1, // Current user
          user_name: 'Test',
          connection_id: 1,
          is_typing: true,
          started_at: new Date().toISOString()
        }
      ];

      fixture.detectChanges();
      tick();

      typingSubject.next(usersWithSelf);
      tick();

      // Should exclude current user
      expect(component.typingUsers.length).toBe(3);
      expect(component.typingUsers.every(user => user.user_id !== 1)).toBe(true);
    }));
  });

  describe('Typing Indicator Display', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should display single user typing', fakeAsync(() => {
      const singleUser = [mockTypingUsers[0]];
      typingSubject.next(singleUser);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(indicator).toBeTruthy();
      expect(indicator.nativeElement.textContent).toContain('Emma is typing');
    }));

    it('should display multiple users typing', fakeAsync(() => {
      typingSubject.next(mockTypingUsers);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(indicator).toBeTruthy();
      
      if (mockTypingUsers.length === 2) {
        expect(indicator.nativeElement.textContent).toContain('Emma and Sofia are typing');
      } else if (mockTypingUsers.length === 3) {
        expect(indicator.nativeElement.textContent).toContain('Emma, Sofia and Alexandra are typing');
      }
    }));

    it('should display animated typing dots', fakeAsync(() => {
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const typingDots = fixture.debugElement.query(By.css('.typing-dots'));
      expect(typingDots).toBeTruthy();

      const dots = typingDots.queryAll(By.css('.dot'));
      expect(dots.length).toBe(3);

      // Verify animation classes
      dots.forEach(dot => {
        expect(dot.nativeElement.classList).toContain('animate');
      });
    }));

    it('should show user avatars when enabled', fakeAsync(() => {
      component.config.showAvatars = true;
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const avatar = fixture.debugElement.query(By.css('.typing-avatar'));
      expect(avatar).toBeTruthy();
      expect(avatar.nativeElement.src).toBe(mockTypingUsers[0].avatar_url);
    }));

    it('should hide user avatars when disabled', fakeAsync(() => {
      component.config.showAvatars = false;
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const avatar = fixture.debugElement.query(By.css('.typing-avatar'));
      expect(avatar).toBeFalsy();
    }));

    it('should show user names when enabled', fakeAsync(() => {
      component.config.showNames = true;
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const userName = fixture.debugElement.query(By.css('.typing-user-name'));
      expect(userName).toBeTruthy();
      expect(userName.nativeElement.textContent).toContain('Emma');
    }));

    it('should hide user names in compact mode', fakeAsync(() => {
      component.config.compactMode = true;
      component.config.showNames = false;
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const userName = fixture.debugElement.query(By.css('.typing-user-name'));
      expect(userName).toBeFalsy();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator.compact'));
      expect(indicator).toBeTruthy();
    }));

    it('should limit visible users based on maxVisibleUsers', fakeAsync(() => {
      component.config.maxVisibleUsers = 2;
      typingSubject.next(mockTypingUsers); // 3 users
      tick();
      fixture.detectChanges();

      const visibleUsers = fixture.debugElement.queryAll(By.css('.typing-user'));
      expect(visibleUsers.length).toBeLessThanOrEqual(2);

      const moreIndicator = fixture.debugElement.query(By.css('.more-users-typing'));
      expect(moreIndicator).toBeTruthy();
      expect(moreIndicator.nativeElement.textContent).toContain('and 1 more');
    }));

    it('should handle users with missing avatars', fakeAsync(() => {
      const userWithoutAvatar = {
        ...mockTypingUsers[0],
        avatar_url: undefined
      };

      typingSubject.next([userWithoutAvatar]);
      tick();
      fixture.detectChanges();

      const defaultAvatar = fixture.debugElement.query(By.css('.default-avatar'));
      expect(defaultAvatar).toBeTruthy();
      
      const avatarInitials = defaultAvatar.query(By.css('.avatar-initials'));
      expect(avatarInitials.nativeElement.textContent).toBe('E'); // First letter of Emma
    }));
  });

  describe('Typing Animation States', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should animate in when users start typing', fakeAsync(() => {
      // Initially no users typing
      expect(component.typingUsers.length).toBe(0);

      // User starts typing
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(indicator.nativeElement.classList).toContain('fade-in');
    }));

    it('should animate out when users stop typing', fakeAsync(() => {
      // User is typing
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      // User stops typing
      typingSubject.next([]);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      if (indicator) {
        expect(indicator.nativeElement.classList).toContain('fade-out');
      }
    }));

    it('should handle rapid typing state changes', fakeAsync(() => {
      const rapidChanges = [
        [mockTypingUsers[0]],
        [mockTypingUsers[0], mockTypingUsers[1]],
        [mockTypingUsers[1]],
        [],
        [mockTypingUsers[2]]
      ];

      rapidChanges.forEach((users, index) => {
        typingSubject.next(users);
        tick(50); // Short delay between changes
      });

      fixture.detectChanges();
      
      // Should handle all changes without errors
      expect(component.typingUsers.length).toBe(1);
      expect(component.typingUsers[0].user_name).toBe('Alexandra');
    }));

    it('should maintain consistent animation timing', fakeAsync(() => {
      const animationStartTime = performance.now();

      typingSubject.next([mockTypingUsers[0]]);
      tick(component.config.animationDuration);
      fixture.detectChanges();

      const animationEndTime = performance.now();
      const actualDuration = animationEndTime - animationStartTime;

      // Allow some tolerance for test execution time
      expect(actualDuration).toBeLessThan(component.config.animationDuration + 100);
    }));

    it('should stagger animations for multiple users', fakeAsync(() => {
      component.config.staggerDelay = 100;
      typingSubject.next(mockTypingUsers);
      tick();
      fixture.detectChanges();

      const userElements = fixture.debugElement.queryAll(By.css('.typing-user'));
      userElements.forEach((element, index) => {
        const delay = parseInt(element.nativeElement.style.animationDelay || '0');
        expect(delay).toBe(index * component.config.staggerDelay);
      });
    }));
  });

  describe('User Interaction and Accessibility', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should have proper ARIA labels', fakeAsync(() => {
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(indicator.nativeElement.getAttribute('aria-label')).toBe('Emma is typing');
      expect(indicator.nativeElement.getAttribute('role')).toBe('status');
    }));

    it('should update ARIA labels for multiple users', fakeAsync(() => {
      typingSubject.next(mockTypingUsers.slice(0, 2));
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(indicator.nativeElement.getAttribute('aria-label')).toBe('Emma and Sofia are typing');
    }));

    it('should support reduced motion preferences', fakeAsync(() => {
      // Mock reduced motion preference
      spyOnProperty(window, 'matchMedia').and.returnValue({
        matches: true,
        media: '(prefers-reduced-motion: reduce)'
      } as MediaQueryList);

      component.ngOnInit();
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(indicator.nativeElement.classList).toContain('reduced-motion');
    }));

    it('should handle click events on typing users', fakeAsync(() => {
      spyOn(component.userClicked, 'emit');
      
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const userElement = fixture.debugElement.query(By.css('.typing-user'));
      userElement.triggerEventHandler('click', {});

      expect(component.userClicked.emit).toHaveBeenCalledWith(mockTypingUsers[0]);
    }));

    it('should support keyboard navigation', fakeAsync(() => {
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const userElement = fixture.debugElement.query(By.css('.typing-user'));
      expect(userElement.nativeElement.getAttribute('tabindex')).toBe('0');

      userElement.triggerEventHandler('keydown.enter', {});
      expect(component.userClicked.emit).toHaveBeenCalledWith(mockTypingUsers[0]);
    }));

    it('should provide hover tooltips with typing duration', fakeAsync(() => {
      const userStartTime = new Date(Date.now() - 10000); // 10 seconds ago
      const userWithDuration = {
        ...mockTypingUsers[0],
        started_at: userStartTime.toISOString()
      };

      typingSubject.next([userWithDuration]);
      tick();
      fixture.detectChanges();

      const userElement = fixture.debugElement.query(By.css('.typing-user'));
      const tooltip = userElement.nativeElement.getAttribute('title');
      
      expect(tooltip).toContain('Emma');
      expect(tooltip).toContain('typing for');
    }));
  });

  describe('Performance and Optimization', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should debounce rapid typing updates', fakeAsync(() => {
      spyOn(component, 'updateTypingUsers').and.callThrough();

      // Rapid updates
      for (let i = 0; i < 10; i++) {
        typingSubject.next([mockTypingUsers[0]]);
        tick(10); // Very short intervals
      }

      // Should debounce to fewer actual updates
      expect(component.updateTypingUsers).toHaveBeenCalledTimes(1);
    }));

    it('should cleanup expired typing indicators', fakeAsync(() => {
      const expiredUser = {
        ...mockTypingUsers[0],
        started_at: new Date(Date.now() - 35000).toISOString() // 35 seconds ago
      };

      typingSubject.next([expiredUser]);
      tick(1000); // Wait for cleanup interval
      fixture.detectChanges();

      expect(component.typingUsers.length).toBe(0);
    }));

    it('should limit maximum typing users for performance', () => {
      const manyUsers = Array.from({ length: 20 }, (_, i) => ({
        ...mockTypingUsers[0],
        user_id: i + 2,
        user_name: `User${i + 2}`
      }));

      typingSubject.next(manyUsers);
      fixture.detectChanges();

      expect(component.visibleTypingUsers.length).toBeLessThanOrEqual(
        component.config.maxVisibleUsers
      );
    });

    it('should use virtual scrolling for large user lists', fakeAsync(() => {
      component.config.maxVisibleUsers = 100;
      const manyUsers = Array.from({ length: 100 }, (_, i) => ({
        ...mockTypingUsers[0],
        user_id: i + 2,
        user_name: `User${i + 2}`
      }));

      typingSubject.next(manyUsers);
      tick();
      fixture.detectChanges();

      const virtualScrollViewport = fixture.debugElement.query(By.css('cdk-virtual-scroll-viewport'));
      expect(virtualScrollViewport).toBeTruthy();
    }));

    it('should implement lazy loading for user avatars', fakeAsync(() => {
      typingSubject.next(mockTypingUsers);
      tick();
      fixture.detectChanges();

      const lazyImages = fixture.debugElement.queryAll(By.css('img[loading="lazy"]'));
      expect(lazyImages.length).toBe(mockTypingUsers.length);
    }));

    it('should cache user information for performance', () => {
      const userCache = component.getUserCache();
      
      typingSubject.next([mockTypingUsers[0]]);
      fixture.detectChanges();

      expect(userCache.has(mockTypingUsers[0].user_id)).toBe(true);
      expect(userCache.get(mockTypingUsers[0].user_id)).toEqual(
        jasmine.objectContaining({
          user_name: 'Emma',
          avatar_url: mockTypingUsers[0].avatar_url
        })
      );
    });
  });

  describe('Sound and Audio Feedback', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should play sound when typing starts', fakeAsync(() => {
      component.config.enableSounds = true;
      spyOn(component, 'playTypingSound');

      typingSubject.next([mockTypingUsers[0]]);
      tick();

      expect(component.playTypingSound).toHaveBeenCalledWith('start');
    }));

    it('should play sound when typing stops', fakeAsync(() => {
      component.config.enableSounds = true;
      spyOn(component, 'playTypingSound');

      typingSubject.next([mockTypingUsers[0]]);
      tick();

      typingSubject.next([]);
      tick();

      expect(component.playTypingSound).toHaveBeenCalledWith('stop');
    }));

    it('should respect sound preferences', fakeAsync(() => {
      component.config.enableSounds = false;
      spyOn(component, 'playTypingSound');

      typingSubject.next([mockTypingUsers[0]]);
      tick();

      expect(component.playTypingSound).not.toHaveBeenCalled();
    }));

    it('should handle audio loading failures gracefully', fakeAsync(() => {
      component.config.enableSounds = true;
      spyOn(component, 'playTypingSound').and.throwError('Audio load failed');
      spyOn(console, 'warn');

      typingSubject.next([mockTypingUsers[0]]);
      tick();

      expect(console.warn).toHaveBeenCalled();
    }));

    it('should adjust sound volume based on user preferences', () => {
      component.config.enableSounds = true;
      component.config.soundVolume = 0.3;

      const audioElement = component.getTypingSoundElement();
      expect(audioElement.volume).toBe(0.3);
    });
  });

  describe('Mobile and Responsive Behavior', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should adapt layout for mobile screens', fakeAsync(() => {
      spyOnProperty(window, 'innerWidth').and.returnValue(375);
      
      component.ngOnInit();
      typingSubject.next(mockTypingUsers);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(indicator.nativeElement.classList).toContain('mobile');
    }));

    it('should use smaller avatars on mobile', fakeAsync(() => {
      component.isMobile = true;
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const avatar = fixture.debugElement.query(By.css('.typing-avatar'));
      expect(avatar.nativeElement.classList).toContain('small');
    }));

    it('should show fewer users on small screens', fakeAsync(() => {
      component.isMobile = true;
      component.config.maxVisibleUsers = 2; // Reduced for mobile

      typingSubject.next(mockTypingUsers); // 3 users
      tick();
      fixture.detectChanges();

      const visibleUsers = component.getVisibleUsers();
      expect(visibleUsers.length).toBeLessThanOrEqual(2);
    }));

    it('should support touch gestures for user interaction', fakeAsync(() => {
      component.isMobile = true;
      spyOn(component.userClicked, 'emit');

      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const userElement = fixture.debugElement.query(By.css('.typing-user'));
      userElement.triggerEventHandler('touchend', { preventDefault: () => {} });

      expect(component.userClicked.emit).toHaveBeenCalled();
    }));

    it('should optimize animations for mobile performance', fakeAsync(() => {
      component.isMobile = true;
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(indicator.nativeElement.classList).toContain('optimized-animations');
    }));
  });

  describe('Error Handling and Edge Cases', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should handle WebSocket disconnection gracefully', fakeAsync(() => {
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      // Simulate WebSocket error
      typingSubject.error(new Error('WebSocket disconnected'));
      tick();

      expect(component.typingUsers).toEqual([]);
      
      const offlineIndicator = fixture.debugElement.query(By.css('.offline-indicator'));
      expect(offlineIndicator).toBeTruthy();
    }));

    it('should handle malformed typing data', fakeAsync(() => {
      const malformedData = [
        { user_id: null, user_name: 'Invalid', connection_id: 1 },
        { user_id: 2, user_name: '', connection_id: 1 },
        { user_id: 3, user_name: 'Valid', connection_id: null }
      ] as any[];

      spyOn(console, 'warn');
      typingSubject.next(malformedData);
      tick();

      expect(console.warn).toHaveBeenCalled();
      expect(component.typingUsers.length).toBe(0); // Should filter out invalid data
    }));

    it('should handle rapid user additions and removals', fakeAsync(() => {
      const userSequences = [
        [mockTypingUsers[0]],
        [mockTypingUsers[0], mockTypingUsers[1]],
        [mockTypingUsers[1]],
        [mockTypingUsers[1], mockTypingUsers[2]],
        [],
        [mockTypingUsers[0], mockTypingUsers[2]]
      ];

      userSequences.forEach((users, index) => {
        typingSubject.next(users);
        tick(50);
      });

      fixture.detectChanges();
      
      // Should handle all transitions smoothly
      expect(component.typingUsers.length).toBe(2);
    }));

    it('should handle missing user information', fakeAsync(() => {
      const usersWithMissingInfo = [
        { ...mockTypingUsers[0], user_name: undefined },
        { ...mockTypingUsers[1], avatar_url: undefined }
      ] as any[];

      typingSubject.next(usersWithMissingInfo);
      tick();
      fixture.detectChanges();

      const userElements = fixture.debugElement.queryAll(By.css('.typing-user'));
      expect(userElements.length).toBe(2);

      // Should use fallback values
      const firstUser = userElements[0];
      expect(firstUser.nativeElement.textContent).toContain('Unknown User');
    }));

    it('should prevent memory leaks on component destroy', () => {
      spyOn(component['subscriptions'], 'unsubscribe');
      
      component.ngOnDestroy();
      
      expect(component['subscriptions'].unsubscribe).toHaveBeenCalled();
    });

    it('should handle simultaneous typing timeout and new typing events', fakeAsync(() => {
      const oldUser = {
        ...mockTypingUsers[0],
        started_at: new Date(Date.now() - 35000).toISOString() // Expired
      };

      const newUser = {
        ...mockTypingUsers[1],
        started_at: new Date().toISOString() // Fresh
      };

      typingSubject.next([oldUser, newUser]);
      tick(1000); // Wait for cleanup

      expect(component.typingUsers.length).toBe(1);
      expect(component.typingUsers[0].user_name).toBe('Sofia');
    }));
  });

  describe('Theming and Customization', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('should apply custom theme colors', fakeAsync(() => {
      component.config.theme = {
        primaryColor: '#6366f1',
        backgroundColor: '#f8fafc',
        textColor: '#1e293b'
      };

      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      const computedStyles = getComputedStyle(indicator.nativeElement);
      
      expect(computedStyles.getPropertyValue('--primary-color')).toBe('#6366f1');
    }));

    it('should support dark mode', fakeAsync(() => {
      component.config.darkMode = true;
      
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const indicator = fixture.debugElement.query(By.css('.typing-indicator'));
      expect(indicator.nativeElement.classList).toContain('dark-mode');
    }));

    it('should allow custom dot animations', fakeAsync(() => {
      component.config.dotAnimation = 'pulse';
      
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const dots = fixture.debugElement.queryAll(By.css('.dot'));
      dots.forEach(dot => {
        expect(dot.nativeElement.classList).toContain('pulse-animation');
      });
    }));

    it('should support custom user templates', fakeAsync(() => {
      component.config.customTemplate = true;
      
      typingSubject.next([mockTypingUsers[0]]);
      tick();
      fixture.detectChanges();

      const customTemplate = fixture.debugElement.query(By.css('.custom-typing-template'));
      expect(customTemplate).toBeTruthy();
    }));
  });
});