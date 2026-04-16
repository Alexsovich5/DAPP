import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConnectionCardComponent } from './connection-card.component';
import { SoulConnection } from '@core/interfaces/soul-connection.interfaces';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

const MOCK_CONNECTION: SoulConnection = {
  id: 1, user1_id: 10, user2_id: 20, initiated_by: 10,
  connection_stage: 'revelation_phase',
  compatibility_score: 78,
  compatibility_breakdown: { interests: 80, values: 75, demographics: 70, communication: 85, personality: 80 },
  reveal_day: 3, mutual_reveal_consent: false, first_dinner_completed: false,
  status: 'active', created_at: '', updated_at: '',
  user1_profile: { id: 10, first_name: 'Jordan' },
  user2_profile: { id: 20, first_name: 'Sam' }
};

describe('ConnectionCardComponent', () => {
  let fixture: ComponentFixture<ConnectionCardComponent>;
  let component: ConnectionCardComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConnectionCardComponent, NoopAnimationsModule]
    }).compileComponents();
    fixture = TestBed.createComponent(ConnectionCardComponent);
    component = fixture.componentInstance;
    component.connection = MOCK_CONNECTION;
    component.currentUserId = 10;
    fixture.detectChanges();
  });

  it('should display the partner name', () => {
    expect(fixture.nativeElement.textContent).toContain('Sam');
  });

  it('should display the connection stage as a badge', () => {
    expect(fixture.nativeElement.textContent).toContain('Revelation Phase');
  });

  it('should display the compatibility score', () => {
    expect(fixture.nativeElement.textContent).toContain('78%');
  });

  it('should emit openChat event when chat button clicked', () => {
    spyOn(component.openChat, 'emit');
    const btn = fixture.nativeElement.querySelector('[data-testid="open-chat-btn"]') as HTMLButtonElement;
    btn.click();
    expect(component.openChat.emit).toHaveBeenCalledWith(MOCK_CONNECTION);
  });
});
