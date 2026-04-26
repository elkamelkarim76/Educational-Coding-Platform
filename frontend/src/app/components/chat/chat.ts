import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { ChatService, ChatMessage } from '../../services/chatService/chat-service';

@Component({
  selector: 'app-chat',
  imports: [FormsModule, DatePipe],
  templateUrl: './chat.html',
  styleUrl: './chat.css'
})
export class Chat implements OnInit, OnDestroy, AfterViewChecked {
  @Input() exerciseId!: number;
  @Input() userId: number = 1;
  @ViewChild('messagesEnd') messagesEnd!: ElementRef;

  messages: ChatMessage[] = [];
  newMessage = '';
  private eventSource?: EventSource;
  private sentMessageIds = new Set<number>(); // évite les doublons

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.chatService.getMessages(this.exerciseId).subscribe(msgs => this.messages = msgs);

    this.eventSource = this.chatService.openStream(this.exerciseId);
    this.eventSource.onmessage = (event) => {
      const msg: ChatMessage = JSON.parse(event.data);
      // Si on a déjà ajouté ce message localement, on ignore
      if (this.sentMessageIds.has(msg.id)) {
        this.sentMessageIds.delete(msg.id);
        return;
      }
      this.messages.push(msg);
    };
  }

  ngAfterViewChecked(): void {
    this.messagesEnd?.nativeElement.scrollIntoView({ behavior: 'smooth' });
  }

  sendMessage(): void {
    const content = this.newMessage.trim();
    if (!content) return;
    this.newMessage = '';

    this.chatService.sendMessage(this.exerciseId, this.userId, content).subscribe({
      next: (msg: ChatMessage) => {
        // Ajouter immédiatement le message localement
        this.messages.push(msg);
        // Mémoriser l'id pour ignorer quand il revient via SSE
        this.sentMessageIds.add(msg.id);
      }
    });
  }

  ngOnDestroy(): void {
    this.eventSource?.close();
  }
}
