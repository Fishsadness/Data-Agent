import { useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import { useStore } from '../../store';
import { MessageBubble } from './MessageBubble';

export function MessageList() {
  const { messages, isQuerying } = useStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isQuerying]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-6 text-center paper-texture dark:paper-texture-dark">
        {/* Decorative Ornament */}
        <div className="mb-8 text-vintage-brown/20 dark:text-vintage-amber/20 font-serif text-6xl select-none">
          &#10086;
        </div>

        <h2 className="font-serif uppercase tracking-[0.3em] text-lg text-vintage-brown dark:text-vintage-amber mb-3">
          Data Agent
        </h2>
        <div className="vintage-divider w-48 mx-auto mb-4" />
        <p className="font-serif text-sm text-vintage-brown/50 dark:text-vintage-amber/50 max-w-xs leading-relaxed italic">
          "Ask your data a question in plain English, and the agent will craft the query, fetch the results, and tell you the story hidden within."
        </p>

        <div className="mt-10 text-[10px] uppercase tracking-[0.3em] text-vintage-brown/30 dark:text-vintage-amber/30">
          est. 2024
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 paper-texture dark:paper-texture-dark">
      <div className="max-w-3xl mx-auto space-y-8">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isQuerying && (
          <div className="flex gap-3">
            <div className="w-8 h-8 border-2 border-vintage-brown dark:border-vintage-amber flex items-center justify-center shrink-0">
              <Loader2 className="w-4 h-4 text-vintage-brown dark:text-vintage-amber animate-spin" />
            </div>
            <div className="flex items-center gap-2 px-5 py-3 border-2 border-vintage-brown/30 dark:border-vintage-amber/30 paper-texture dark:paper-texture-dark">
              <span className="typing-dot w-1.5 h-1.5 bg-vintage-brown/50 dark:bg-vintage-amber/50" />
              <span className="typing-dot w-1.5 h-1.5 bg-vintage-brown/50 dark:bg-vintage-amber/50" />
              <span className="typing-dot w-1.5 h-1.5 bg-vintage-brown/50 dark:bg-vintage-amber/50" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}