import { User, Bot, Database } from 'lucide-react';
import type { Message } from '../../types';
import { ChartView } from '../panels/ChartView';
import { formatTime } from '../../lib/utils';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Assistant Avatar */}
      {!isUser && (
        <div className="w-8 h-8 border-2 border-vintage-brown dark:border-vintage-amber flex items-center justify-center shrink-0 mt-0.5">
          <Bot className="w-4 h-4 text-vintage-brown dark:text-vintage-amber" />
        </div>
      )}

      <div className={`max-w-[80%] ${isUser ? 'order-1' : ''}`}>
        {isUser ? (
          /* User Message - like a handwritten note */
          <div className="relative group">
            <div className="bg-vintage-brown text-vintage-cream px-5 py-3 font-serif text-sm leading-relaxed shadow-vintage-sm transition-colors duration-700">
              {message.content}
            </div>
          </div>
        ) : (
          /* Assistant Message */
          <div className="space-y-4">
            {/* SQL Code Block */}
            {message.sql && (
              <div className="border-2 border-vintage-brown dark:border-vintage-amber bg-vintage-ink dark:bg-[#1a0f05] overflow-hidden shadow-vintage-sm">
                <div className="flex items-center justify-between px-4 py-2 border-b-2 border-vintage-brown/30 dark:border-vintage-amber/30">
                  <div className="flex items-center gap-2">
                    <Database className="w-3 h-3 text-vintage-amber dark:text-vintage-amber" />
                    <span className="text-[10px] uppercase tracking-[0.2em] text-vintage-amber/80 font-serif">
                      Generated SQL
                    </span>
                  </div>
                </div>
                <pre className="p-4 text-xs text-vintage-cream overflow-x-auto font-mono leading-relaxed">
                  {message.sql}
                </pre>
              </div>
            )}

            {/* Chart */}
            {message.result?.chart && message.result.chart.type !== 'none' && (
              <ChartView chart={message.result.chart} />
            )}

            {/* Analysis Text */}
            {message.content && (
              <div className="paper-texture dark:paper-texture-dark border-2 border-vintage-brown dark:border-vintage-amber p-5 shadow-vintage-sm corner-ornament">
                <div className="text-sm text-vintage-ink dark:text-vintage-cream leading-relaxed whitespace-pre-wrap markdown-body">
                  {message.content}
                </div>
              </div>
            )}

            {/* Stats Footer */}
            {message.result && (
              <div className="flex items-center gap-4 text-[10px] font-serif uppercase tracking-[0.15em] text-vintage-brown/50 dark:text-vintage-amber/50">
                <div className="vintage-divider flex-1" />
                {message.result.row_count > 0 && (
                  <span>{message.result.row_count} rows returned</span>
                )}
                {message.result.elapsed_ms > 0 && (
                  <span>{formatTime(message.result.elapsed_ms)}</span>
                )}
                <div className="vintage-divider flex-1" />
              </div>
            )}
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 border-2 border-vintage-brown dark:border-vintage-amber flex items-center justify-center shrink-0 mt-0.5">
          <User className="w-4 h-4 text-vintage-brown dark:text-vintage-amber" />
        </div>
      )}
    </div>
  );
}