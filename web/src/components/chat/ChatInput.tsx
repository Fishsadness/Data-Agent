import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t-2 border-vintage-brown/30 dark:border-vintage-amber/30 paper-texture dark:paper-texture-dark p-5">
      <div className="max-w-3xl mx-auto flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter your data query, e.g. top 10 best-selling products..."
            rows={1}
            disabled={disabled}
            className="w-full resize-none border-2 border-vintage-brown dark:border-vintage-amber bg-transparent text-vintage-ink dark:text-vintage-cream font-serif placeholder:text-vintage-brown/30 dark:placeholder:text-vintage-amber/30 px-4 py-3 pr-12 text-sm focus:outline-none focus:border-vintage-darkbrown dark:focus:border-vintage-amber transition-colors duration-700 disabled:opacity-40"
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
          className="shrink-0 w-10 h-10 border-2 border-vintage-brown dark:border-vintage-amber bg-vintage-brown dark:bg-vintage-amber text-vintage-cream dark:text-vintage-ink flex items-center justify-center transition-colors duration-700 hover:bg-vintage-darkbrown dark:hover:bg-vintage-amber/80 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {disabled ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
      <div className="max-w-3xl mx-auto mt-3 flex flex-wrap gap-2">
        {[
          'Top 10 best-selling products',
          'User count by city',
          'Monthly sales trend 2024',
          'Category sales share',
        ].map((q) => (
          <button
            key={q}
            onClick={() => { setInput(q); }}
            disabled={disabled}
            className="text-[10px] uppercase tracking-[0.15em] font-serif px-3 py-1.5 border border-vintage-brown/20 dark:border-vintage-amber/20 text-vintage-brown/60 dark:text-vintage-amber/60 hover:text-vintage-brown dark:hover:text-vintage-amber hover:border-vintage-brown dark:hover:border-vintage-amber transition-colors duration-700 disabled:opacity-30"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}