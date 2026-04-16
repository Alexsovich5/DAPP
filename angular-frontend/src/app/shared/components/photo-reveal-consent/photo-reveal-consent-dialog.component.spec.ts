import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { PhotoRevealConsentDialogComponent } from './photo-reveal-consent-dialog.component';

describe('PhotoRevealConsentDialogComponent', () => {
  let fixture: ComponentFixture<PhotoRevealConsentDialogComponent>;
  let component: PhotoRevealConsentDialogComponent;
  const dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PhotoRevealConsentDialogComponent],
      providers: [
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: { partnerName: 'Alex' } }
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(PhotoRevealConsentDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should display the partner name', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Alex');
  });

  it('should call dialogRef.close(true) when consent given', () => {
    component.onConsent();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(true);
  });

  it('should call dialogRef.close(false) when declined', () => {
    component.onDecline();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(false);
  });
});
