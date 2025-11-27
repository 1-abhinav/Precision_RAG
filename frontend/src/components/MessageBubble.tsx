import { CitationRenderer } from './CitationRenderer';
import type { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const avatar = message.type === 'user' ? '🧑‍💻' : '🤖';
  const label = message.type === 'user' ? 'You' : 'Assistant';

  return (
    <div className={`message-bubble ${message.type}`}>
      <div className="message-meta">
        <div className="avatar">{avatar}</div>
        <div>
          <p className="message-type">{label}</p>
          <span className="message-time">
            {message.timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
      </div>
      <div className="message-body">
        <div className="message-content">{message.content}</div>
        {message.citations && message.citations.length > 0 && (
          <CitationRenderer citations={message.citations} />
        )}
      </div>
    </div>
  );
}

