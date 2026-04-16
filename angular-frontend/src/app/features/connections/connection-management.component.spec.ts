import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ConnectionManagementComponent } from './connection-management.component';
import { SoulConnectionService } from '@core/services/soul-connection.service';
import { AuthService } from '@core/services/auth.service';
import { SoulConnection } from '@core/interfaces/soul-connection.interfaces';

const makeConnection = (id: number, stage: SoulConnection['connection_stage']): SoulConnection => ({
  id, user1_id: 1, user2_id: 2, initiated_by: 1,
  connection_stage: stage, compatibility_score: 75,
  compatibility_breakdown: { interests: 70, values: 80, demographics: 70, communication: 75, personality: 80 },
  reveal_day: 3, mutual_reveal_consent: false, first_dinner_completed: false,
  status: 'active', created_at: '', updated_at: '',
  user1_profile: { id: 1, first_name: 'Me' },
  user2_profile: { id: 2, first_name: 'Partner' }
});

describe('ConnectionManagementComponent', () => {
  let fixture: ComponentFixture<ConnectionManagementComponent>;
  let component: ConnectionManagementComponent;
  let soulConnectionServiceSpy: jasmine.SpyObj<SoulConnectionService>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    soulConnectionServiceSpy = jasmine.createSpyObj('SoulConnectionService', ['getActiveConnections']);
    authServiceSpy = jasmine.createSpyObj('AuthService', [], { currentUser$: of({ id: 1, first_name: 'Me' }) });
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    soulConnectionServiceSpy.getActiveConnections.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [ConnectionManagementComponent, NoopAnimationsModule],
      providers: [
        { provide: SoulConnectionService, useValue: soulConnectionServiceSpy },
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ConnectionManagementComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should load connections on init', () => {
    expect(soulConnectionServiceSpy.getActiveConnections).toHaveBeenCalled();
  });

  it('should show loading state before connections load', () => {
    component.isLoading = true;
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('mat-spinner')).toBeTruthy();
  });

  it('should show error state when load fails', () => {
    soulConnectionServiceSpy.getActiveConnections.and.returnValue(throwError(() => new Error('fail')));
    component['loadConnections']();
    fixture.detectChanges();
    expect(component.error).toBeTruthy();
  });

  it('activeConnections returns only soul_discovery stage', () => {
    component.connections = [
      makeConnection(1, 'soul_discovery'),
      makeConnection(2, 'revelation_phase')
    ];
    expect(component.activeConnections.length).toBe(1);
    expect(component.activeConnections[0].id).toBe(1);
  });

  it('revealingConnections includes revelation_phase and photo_reveal', () => {
    component.connections = [
      makeConnection(1, 'revelation_phase'),
      makeConnection(2, 'photo_reveal'),
      makeConnection(3, 'dinner_planning')
    ];
    expect(component.revealingConnections.length).toBe(2);
  });

  it('navigateToChat routes to /chat with connectionId query param', () => {
    const conn = makeConnection(5, 'soul_discovery');
    component.navigateToChat(conn);
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/chat'], { queryParams: { connectionId: 5 } });
  });
});
