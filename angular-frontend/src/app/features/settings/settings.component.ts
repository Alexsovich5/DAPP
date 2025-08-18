import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';

interface PrivacySettings {
  profileVisibility: 'public' | 'hidden' | 'connections_only';
  showPhotosAfterReveal: boolean;
  allowDirectMessages: boolean;
  showOnlineStatus: boolean;
  shareLocation: boolean;
}

interface NotificationSettings {
  pushNotifications: boolean;
  emailNotifications: boolean;
  revelationReminders: boolean;
  newMatches: boolean;
  newMessages: boolean;
  photoRevealReady: boolean;
}

interface AppSettings {
  soulBeforeSkinMode: boolean;
  autoPhotoReveal: boolean;
  revelationCycleDays: number;
  compatibilityThreshold: number;
  darkMode: boolean;
  language: string;
}

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  template: `
    <div class="settings-container">
      <header class="settings-header">
        <h1>Settings</h1>
        <p class="subtitle">Customize your Soul Before Skin experience</p>
      </header>

      <div class="settings-content">
        <!-- Privacy Settings -->
        <section class="settings-section">
          <div class="section-header">
            <h2>🔒 Privacy & Visibility</h2>
            <p>Control who can see your profile and information</p>
          </div>

          <div class="settings-group">
            <div class="setting-item">
              <div class="setting-info">
                <h3>Profile Visibility</h3>
                <p>Choose who can discover your profile</p>
              </div>
              <select [(ngModel)]="privacySettings.profileVisibility" class="setting-select">
                <option value="public">Public - Anyone can discover me</option>
                <option value="hidden">Hidden - I choose who to connect with</option>
                <option value="connections_only">Connections Only - Only existing connections</option>
              </select>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Show Photos After Revelation</h3>
                <p>Automatically show photos after completing 7-day cycle</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="privacySettings.showPhotosAfterReveal">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Allow Direct Messages</h3>
                <p>Let people message you directly</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="privacySettings.allowDirectMessages">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Show Online Status</h3>
                <p>Let others see when you're online</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="privacySettings.showOnlineStatus">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Share Location</h3>
                <p>Include general location in compatibility matching</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="privacySettings.shareLocation">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </section>

        <!-- Notification Settings -->
        <section class="settings-section">
          <div class="section-header">
            <h2>🔔 Notifications</h2>
            <p>Choose what notifications you want to receive</p>
          </div>

          <div class="settings-group">
            <div class="setting-item">
              <div class="setting-info">
                <h3>Push Notifications</h3>
                <p>Receive notifications on your device</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="notificationSettings.pushNotifications">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Email Notifications</h3>
                <p>Get updates via email</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="notificationSettings.emailNotifications">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Revelation Reminders</h3>
                <p>Daily reminders to share revelations</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="notificationSettings.revelationReminders">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>New Matches</h3>
                <p>Notify when you have new soul connections</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="notificationSettings.newMatches">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>New Messages</h3>
                <p>Notify when you receive messages</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="notificationSettings.newMessages">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Photo Reveal Ready</h3>
                <p>Notify when mutual photo reveal is available</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="notificationSettings.photoRevealReady">
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </section>

        <!-- App Settings -->
        <section class="settings-section">
          <div class="section-header">
            <h2>⚙️ App Preferences</h2>
            <p>Customize how the app works for you</p>
          </div>

          <div class="settings-group">
            <div class="setting-item">
              <div class="setting-info">
                <h3>Soul Before Skin Mode</h3>
                <p>Hide photos until mutual consent after revelations</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="appSettings.soulBeforeSkinMode">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Auto Photo Reveal</h3>
                <p>Automatically agree to photo reveals after day 7</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="appSettings.autoPhotoReveal">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Revelation Cycle Length</h3>
                <p>Number of days for revelation sharing cycle</p>
              </div>
              <select [(ngModel)]="appSettings.revelationCycleDays" class="setting-select">
                <option value="5">5 Days - Quick Connection</option>
                <option value="7">7 Days - Standard Cycle</option>
                <option value="10">10 Days - Deep Exploration</option>
              </select>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Compatibility Threshold</h3>
                <p>Minimum compatibility score to show matches</p>
              </div>
              <div class="range-setting">
                <input 
                  type="range" 
                  [(ngModel)]="appSettings.compatibilityThreshold"
                  min="30" 
                  max="90" 
                  step="5"
                  class="setting-range"
                >
                <span class="range-value">{{appSettings.compatibilityThreshold}}%</span>
              </div>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Dark Mode</h3>
                <p>Use dark theme for better night viewing</p>
              </div>
              <label class="toggle-switch">
                <input type="checkbox" [(ngModel)]="appSettings.darkMode">
                <span class="toggle-slider"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-info">
                <h3>Language</h3>
                <p>Choose your preferred language</p>
              </div>
              <select [(ngModel)]="appSettings.language" class="setting-select">
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
              </select>
            </div>
          </div>
        </section>

        <!-- Account Actions -->
        <section class="settings-section danger-section">
          <div class="section-header">
            <h2>⚠️ Account Management</h2>
            <p>Manage your account and data</p>
          </div>

          <div class="settings-group">
            <div class="action-item">
              <div class="action-info">
                <h3>Export Your Data</h3>
                <p>Download a copy of your revelations and connections</p>
              </div>
              <button class="action-btn secondary" (click)="exportData()">
                <span>📥</span> Export Data
              </button>
            </div>

            <div class="action-item">
              <div class="action-info">
                <h3>Deactivate Account</h3>
                <p>Temporarily hide your profile from discovery</p>
              </div>
              <button class="action-btn warning" (click)="deactivateAccount()">
                <span>⏸️</span> Deactivate
              </button>
            </div>

            <div class="action-item">
              <div class="action-info">
                <h3>Delete Account</h3>
                <p>Permanently delete your account and all data</p>
              </div>
              <button class="action-btn danger" (click)="deleteAccount()">
                <span>🗑️</span> Delete Account
              </button>
            </div>
          </div>
        </section>
      </div>

      <!-- Save Actions -->
      <div class="save-actions">
        <button class="save-btn" (click)="saveSettings()" [disabled]="!hasChanges">
          <span>💾</span> Save Changes
        </button>
        <button class="reset-btn" (click)="resetSettings()">
          <span>🔄</span> Reset to Defaults
        </button>
      </div>
    </div>
  `,
  styles: [`
    .settings-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 1rem;
      min-height: 100vh;
    }

    .settings-header {
      text-align: center;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #e2e8f0;
    }

    .settings-header h1 {
      font-size: 2.5rem;
      font-weight: 600;
      color: #2d3748;
      margin-bottom: 0.5rem;
    }

    .subtitle {
      font-size: 1.1rem;
      color: #718096;
      margin: 0;
    }

    .settings-content {
      display: flex;
      flex-direction: column;
      gap: 2rem;
      margin-bottom: 2rem;
    }

    .settings-section {
      background: white;
      border-radius: 12px;
      padding: 2rem;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
      border: 1px solid #e2e8f0;
    }

    .danger-section {
      border-color: #fed7d7;
      background: linear-gradient(135deg, rgba(245, 101, 101, 0.02) 0%, rgba(245, 101, 101, 0.01) 100%);
    }

    .section-header {
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #f7fafc;
    }

    .section-header h2 {
      font-size: 1.3rem;
      font-weight: 600;
      color: #2d3748;
      margin: 0 0 0.5rem 0;
    }

    .section-header p {
      color: #718096;
      margin: 0;
      font-size: 0.95rem;
    }

    .settings-group {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .setting-item, .action-item {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
    }

    .setting-info, .action-info {
      flex: 1;
    }

    .setting-info h3, .action-info h3 {
      font-size: 1rem;
      font-weight: 600;
      color: #2d3748;
      margin: 0 0 0.25rem 0;
    }

    .setting-info p, .action-info p {
      font-size: 0.9rem;
      color: #718096;
      margin: 0;
      line-height: 1.4;
    }

    .toggle-switch {
      position: relative;
      display: inline-block;
      width: 50px;
      height: 24px;
      cursor: pointer;
    }

    .toggle-switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }

    .toggle-slider {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: #cbd5e0;
      transition: 0.3s;
      border-radius: 24px;
    }

    .toggle-slider:before {
      position: absolute;
      content: "";
      height: 18px;
      width: 18px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      transition: 0.3s;
      border-radius: 50%;
    }

    input:checked + .toggle-slider {
      background-color: #667eea;
    }

    input:checked + .toggle-slider:before {
      transform: translateX(26px);
    }

    .setting-select {
      padding: 0.5rem 1rem;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      background: white;
      color: #2d3748;
      font-size: 0.9rem;
      cursor: pointer;
      min-width: 200px;
    }

    .setting-select:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .range-setting {
      display: flex;
      align-items: center;
      gap: 1rem;
      min-width: 200px;
    }

    .setting-range {
      flex: 1;
      height: 6px;
      border-radius: 3px;
      background: #e2e8f0;
      outline: none;
      cursor: pointer;
    }

    .setting-range::-webkit-slider-thumb {
      appearance: none;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #667eea;
      cursor: pointer;
    }

    .setting-range::-moz-range-thumb {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #667eea;
      cursor: pointer;
      border: none;
    }

    .range-value {
      font-weight: 600;
      color: #667eea;
      min-width: 45px;
      text-align: center;
    }

    .action-btn {
      padding: 0.75rem 1.5rem;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.9rem;
    }

    .action-btn.secondary {
      background: #f7fafc;
      color: #4a5568;
      border: 1px solid #e2e8f0;
    }

    .action-btn.secondary:hover {
      background: #edf2f7;
      border-color: #cbd5e0;
    }

    .action-btn.warning {
      background: #fed7a1;
      color: #c05621;
      border: 1px solid #f6ad55;
    }

    .action-btn.warning:hover {
      background: #fbd38d;
      border-color: #ed8936;
    }

    .action-btn.danger {
      background: #fed7d7;
      color: #c53030;
      border: 1px solid #fc8181;
    }

    .action-btn.danger:hover {
      background: #feb2b2;
      border-color: #f56565;
    }

    .save-actions {
      display: flex;
      justify-content: center;
      gap: 1rem;
      padding: 2rem 0;
      border-top: 1px solid #e2e8f0;
    }

    .save-btn {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      padding: 1rem 2rem;
      border-radius: 12px;
      font-size: 1.1rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .save-btn:hover:not(:disabled) {
      transform: translateY(-1px);
    }

    .save-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .reset-btn {
      background: white;
      color: #718096;
      border: 1px solid #e2e8f0;
      padding: 1rem 2rem;
      border-radius: 12px;
      font-size: 1.1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .reset-btn:hover {
      background: #f7fafc;
      border-color: #cbd5e0;
    }

    @media (max-width: 768px) {
      .settings-container {
        padding: 0.5rem;
      }
      
      .settings-section {
        padding: 1rem;
      }
      
      .setting-item, .action-item {
        flex-direction: column;
        align-items: stretch;
        gap: 0.75rem;
      }
      
      .setting-select {
        min-width: auto;
      }
      
      .save-actions {
        flex-direction: column;
        align-items: stretch;
      }
    }
  `]
})
export class SettingsComponent implements OnInit {
  privacySettings: PrivacySettings = {
    profileVisibility: 'public',
    showPhotosAfterReveal: true,
    allowDirectMessages: true,
    showOnlineStatus: true,
    shareLocation: false
  };

  notificationSettings: NotificationSettings = {
    pushNotifications: true,
    emailNotifications: false,
    revelationReminders: true,
    newMatches: true,
    newMessages: true,
    photoRevealReady: true
  };

  appSettings: AppSettings = {
    soulBeforeSkinMode: true,
    autoPhotoReveal: false,
    revelationCycleDays: 7,
    compatibilityThreshold: 50,
    darkMode: false,
    language: 'en'
  };

  hasChanges = false;
  originalSettings: any = {};

  constructor(
    private router: Router,
    private formBuilder: FormBuilder
  ) {}

  ngOnInit() {
    this.loadSettings();
    this.saveOriginalSettings();
    this.setupChangeDetection();
  }

  loadSettings() {
    // Load settings from local storage or API
    const savedPrivacy = localStorage.getItem('privacySettings');
    const savedNotifications = localStorage.getItem('notificationSettings');
    const savedApp = localStorage.getItem('appSettings');

    if (savedPrivacy) {
      this.privacySettings = { ...this.privacySettings, ...JSON.parse(savedPrivacy) };
    }

    if (savedNotifications) {
      this.notificationSettings = { ...this.notificationSettings, ...JSON.parse(savedNotifications) };
    }

    if (savedApp) {
      this.appSettings = { ...this.appSettings, ...JSON.parse(savedApp) };
    }
  }

  saveOriginalSettings() {
    this.originalSettings = {
      privacy: { ...this.privacySettings },
      notifications: { ...this.notificationSettings },
      app: { ...this.appSettings }
    };
  }

  setupChangeDetection() {
    // Simple change detection - in real app, use reactive forms
    setInterval(() => {
      this.hasChanges = this.detectChanges();
    }, 500);
  }

  detectChanges(): boolean {
    return JSON.stringify(this.privacySettings) !== JSON.stringify(this.originalSettings.privacy) ||
           JSON.stringify(this.notificationSettings) !== JSON.stringify(this.originalSettings.notifications) ||
           JSON.stringify(this.appSettings) !== JSON.stringify(this.originalSettings.app);
  }

  saveSettings() {
    try {
      // Save to local storage
      localStorage.setItem('privacySettings', JSON.stringify(this.privacySettings));
      localStorage.setItem('notificationSettings', JSON.stringify(this.notificationSettings));
      localStorage.setItem('appSettings', JSON.stringify(this.appSettings));

      // In real app, also save to backend API
      // await this.settingsService.updateSettings({
      //   privacy: this.privacySettings,
      //   notifications: this.notificationSettings,
      //   app: this.appSettings
      // });

      this.saveOriginalSettings();
      this.hasChanges = false;

      // Show success message
      console.log('Settings saved successfully!');

      // Apply dark mode if changed
      if (this.appSettings.darkMode) {
        document.body.classList.add('dark-mode');
      } else {
        document.body.classList.remove('dark-mode');
      }

    } catch (error) {
      console.error('Error saving settings:', error);
    }
  }

  resetSettings() {
    this.privacySettings = {
      profileVisibility: 'public',
      showPhotosAfterReveal: true,
      allowDirectMessages: true,
      showOnlineStatus: true,
      shareLocation: false
    };

    this.notificationSettings = {
      pushNotifications: true,
      emailNotifications: false,
      revelationReminders: true,
      newMatches: true,
      newMessages: true,
      photoRevealReady: true
    };

    this.appSettings = {
      soulBeforeSkinMode: true,
      autoPhotoReveal: false,
      revelationCycleDays: 7,
      compatibilityThreshold: 50,
      darkMode: false,
      language: 'en'
    };

    this.hasChanges = true;
  }

  exportData() {
    // Create mock export data
    const exportData = {
      profile: {
        exportDate: new Date().toISOString(),
        userData: 'Sample user data...'
      },
      revelations: [
        { day: 1, content: 'Sample revelation content...' },
        { day: 2, content: 'Another revelation...' }
      ],
      connections: [
        { partner: 'Alex', compatibility: 89, status: 'active' }
      ]
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `dinner_first-data-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }

  deactivateAccount() {
    if (confirm('Are you sure you want to deactivate your account? Your profile will be hidden from discovery.')) {
      // Implement account deactivation
      console.log('Account deactivated');
      this.router.navigate(['/']);
    }
  }

  deleteAccount() {
    const confirmation = prompt('To delete your account, type "DELETE" to confirm:');
    if (confirmation === 'DELETE') {
      if (confirm('This action cannot be undone. All your data will be permanently deleted.')) {
        // Implement account deletion
        console.log('Account deleted');
        this.router.navigate(['/']);
      }
    }
  }
}