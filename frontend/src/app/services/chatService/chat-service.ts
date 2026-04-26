import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment.development';

export interface ChatMessage {
  id: number;
  room_id: number;
  user_id: number;
  username: string;
  content: string;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class ChatService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getMessages(exerciseId: number): Observable<ChatMessage[]> {
    return this.http.get<ChatMessage[]>(`${this.apiUrl}chat/${exerciseId}/messages`);
  }

  sendMessage(exerciseId: number, userId: number, content: string): Observable<ChatMessage> {
    return this.http.post<ChatMessage>(`${this.apiUrl}chat/${exerciseId}/messages`, {
      user_id: userId,
      content
    });
  }

  openStream(exerciseId: number): EventSource {
    return new EventSource(`${this.apiUrl}chat/${exerciseId}/stream`);
  }
}
