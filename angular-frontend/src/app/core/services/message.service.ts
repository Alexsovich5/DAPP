import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError, catchError } from 'rxjs';
import { environment } from '@environments/environment';

export interface Message {
  id: number;
  connection_id: number;
  sender_id: number;
  recipient_id: number;
  message_text: string;
  message_type: 'text' | 'revelation_share' | 'photo_consent' | 'system' | 'emoji' | 'image';
  created_at: string;
  is_read: boolean;
  sender_name: string;
  is_own_message: boolean;
  emotional_tone?: string;
  reply_to_message_id?: number;
}

export interface MessageSendResponse {
  id: number;
  message_text: string;
  created_at: string;
}

export interface MessageEditResponse {
  success: boolean;
  message: Message;
}

export interface MessageDeleteResponse {
  success: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class MessageService {
  private readonly apiUrl = environment.apiUrl;

  constructor(private readonly http: HttpClient) {}

  getMessages(connectionId: number): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.apiUrl}/messages/${connectionId}`).pipe(
      catchError(this.handleError)
    );
  }

  sendMessage(
    connectionId: number,
    messageText: string,
    messageType: string = 'text'
  ): Observable<MessageSendResponse> {
    return this.http.post<MessageSendResponse>(
      `${this.apiUrl}/messages/${connectionId}`,
      { message_text: messageText, message_type: messageType }
    ).pipe(
      catchError(this.handleError)
    );
  }

  markAsRead(messageIds: number[]): Observable<{ success: boolean }> {
    return this.http.post<{ success: boolean }>(
      `${this.apiUrl}/messages/mark-read`,
      { message_ids: messageIds }
    ).pipe(
      catchError(this.handleError)
    );
  }

  deleteMessage(messageId: number): Observable<MessageDeleteResponse> {
    return this.http.delete<MessageDeleteResponse>(
      `${this.apiUrl}/messages/${messageId}`
    ).pipe(
      catchError(this.handleError)
    );
  }

  editMessage(messageId: number, newText: string): Observable<MessageEditResponse> {
    return this.http.put<MessageEditResponse>(
      `${this.apiUrl}/messages/${messageId}`,
      { message_text: newText }
    ).pipe(
      catchError(this.handleError)
    );
  }

  getMessageHistory(connectionId: number, beforeMessageId: number): Observable<Message[]> {
    return this.http.get<Message[]>(
      `${this.apiUrl}/messages/${connectionId}/history`,
      { params: { before: beforeMessageId.toString() } }
    ).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: unknown): Observable<never> {
    console.error('MessageService error:', error);
    return throwError(() => error);
  }
}
