import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PreferencesService {
  constructor(private http: HttpClient) {}

  getPreferences(): Observable<any> {
    return this.http.get(`${environment.apiUrl}/preferences`);
  }

  updatePreferences(preferences: any): Observable<any> {
    return this.http.put(`${environment.apiUrl}/preferences`, preferences);
  }
}
