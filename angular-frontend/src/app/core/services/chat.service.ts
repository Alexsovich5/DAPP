import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, BehaviorSubject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { map, tap } from 'rxjs/operators';

interface Message {
  id: string;
  senderId: string;
  content: string;
  timestamp: string;
  isRead: boolean;
}

interface ChatUser {
  _id: string;
  firstName: string;
  lastName: string;
  profilePicture?: string;
  lastActive?: string;
}

interface ChatData {
  user: ChatUser;
  messages: Message[];
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private socket$!: WebSocketSubject<any>;
  private messageSubject = new Subject<Message>();
  private onlineUsers = new BehaviorSubject<string[]>([]);

  constructor(private http: HttpClient) {
    this.setupWebSocket();
  }

  private setupWebSocket(): void {
    // In a real app, this would be your WebSocket server URL
    this.socket$ = webSocket(`${environment.socketUrl}/chat`);

    this.socket$.subscribe({
      next: (message) => this.handleWebSocketMessage(message),
      error: (err) => console.error('WebSocket error:', err)
    });
  }

  private handleWebSocketMessage(message: any): void {
    switch (message.type) {
      case 'message':
        this.messageSubject.next(message.data);
        break;
      case 'online_users':
        this.onlineUsers.next(message.data);
        break;
    }
  }

  getChatData(userId: string): Observable<ChatData> {
    return this.http.get<ChatData>(`${environment.apiUrl}/chat/${userId}`).pipe(
      tap(data => {
        // Mark messages as read when loading chat
        if (data.messages.length > 0) {
          this.markMessagesAsRead(userId);
        }
      })
    );
  }

  sendMessage(userId: string, content: string): Observable<Message> {
    const message = {
      receiverId: userId,
      content,
      timestamp: new Date().toISOString()
    };

    return this.http.post<Message>(`${environment.apiUrl}/chat/send`, message);
  }

  markMessagesAsRead(userId: string): Observable<void> {
    return this.http.post<void>(`${environment.apiUrl}/chat/${userId}/read`, {});
  }

  getNewMessages(): Observable<Message> {
    return this.messageSubject.asObservable();
  }

  getOnlineUsers(): Observable<string[]> {
    return this.onlineUsers.asObservable();
  }

  disconnect(): void {
    if (this.socket$) {
      this.socket$.complete();
    }
  }
}
