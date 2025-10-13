/**
 * Dashboard Component Tests
 * Tests for stub component - TODO: Expand when component is fully implemented
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { DashboardComponent } from './dashboard.component';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        DashboardComponent,
        BrowserAnimationsModule
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have stats property with default values', () => {
    expect(component.stats).toEqual({
      active_connections: 0,
      pending_connections: 0,
      completed_revelations: 0,
      total_messages: 0
    });
  });

  it('should have ngOnInit method', () => {
    expect(component.ngOnInit).toBeDefined();
  });

  it('should have loadDashboardStats private method', () => {
    expect(component['loadDashboardStats']).toBeDefined();
  });

  it('should call loadDashboardStats on init', () => {
    spyOn<any>(component, 'loadDashboardStats');
    component.ngOnInit();
    expect(component['loadDashboardStats']).toHaveBeenCalled();
  });

  it('should render the component template', () => {
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.dashboard')).toBeTruthy();
    expect(compiled.querySelector('h2')?.textContent).toContain('Dashboard');
  });

  it('should have stats grid with 4 cards', () => {
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const statsGrid = compiled.querySelector('.stats-grid');
    expect(statsGrid).toBeTruthy();

    const cards = compiled.querySelectorAll('mat-card');
    expect(cards.length).toBe(4);
  });

  it('should display Active Connections stat', () => {
    component.stats.active_connections = 5;
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const content = compiled.textContent || '';
    expect(content).toContain('Active Connections');
  });

  it('should display Pending Connections stat', () => {
    component.stats.pending_connections = 3;
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const content = compiled.textContent || '';
    expect(content).toContain('Pending Connections');
  });

  it('should display Completed Revelations stat', () => {
    component.stats.completed_revelations = 10;
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const content = compiled.textContent || '';
    expect(content).toContain('Completed Revelations');
  });

  it('should display Total Messages stat', () => {
    component.stats.total_messages = 25;
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const content = compiled.textContent || '';
    expect(content).toContain('Total Messages');
  });
});

// TODO: Add comprehensive tests when component features are implemented
// Future tests should cover:
// - Loading dashboard statistics from API
// - Displaying active connections list
// - Displaying recent activities
// - WebSocket real-time updates for stats
// - Navigation to detailed views
// - Error handling and loading states
