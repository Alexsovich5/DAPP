/**
 * Connection Management Component Tests
 * Tests for stub component - TODO: Expand when component is fully implemented
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ConnectionManagementComponent } from './connection-management.component';

describe('ConnectionManagementComponent', () => {
  let component: ConnectionManagementComponent;
  let fixture: ComponentFixture<ConnectionManagementComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        ConnectionManagementComponent,
        BrowserAnimationsModule
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ConnectionManagementComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have ngOnInit method', () => {
    expect(component.ngOnInit).toBeDefined();
  });

  it('should have loadConnections private method', () => {
    expect(component['loadConnections']).toBeDefined();
  });

  it('should call loadConnections on init', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    spyOn<any>(component, 'loadConnections');
    component.ngOnInit();
    expect(component['loadConnections']).toHaveBeenCalled();
  });

  it('should render the component template', () => {
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.connection-management')).toBeTruthy();
    expect(compiled.querySelector('h2')?.textContent).toContain('Soul Connections');
  });

  it('should have mat-tab-group with two tabs', async () => {
    fixture.detectChanges();
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    const tabGroup = compiled.querySelector('mat-tab-group');
    expect(tabGroup).toBeTruthy();

    // Check for tab labels instead of mat-tab elements directly
    const tabLabels = compiled.querySelectorAll('.mat-mdc-tab');
    expect(tabLabels.length).toBe(2);
  });
});

// TODO: Add comprehensive tests when component features are implemented
// Future tests should cover:
// - Loading active connections
// - Loading pending requests
// - WebSocket real-time updates
// - Connection management actions (pause, resume, end)
// - Navigation to messaging
// - Error handling
