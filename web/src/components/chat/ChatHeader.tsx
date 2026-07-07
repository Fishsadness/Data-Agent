import { Moon, Sun, Database, Trash2 } from 'lucide-react';
import { useStore } from '../../store';

interface ChatHeaderProps {
  title?: string;
}

export function ChatHeader({ title = 'DATA AGENT' }: ChatHeaderProps) {
  const { theme, toggleTheme, clearMessages, setActivePanel, activePanel } = useStore();

  return (
    <header className="sticky top-0 z-10 paper-texture border-b-2 border-vintage-brown/30 dark:paper-texture-dark dark:border-vintage-amber/30">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 border-2 border-vintage-brown dark:border-vintage-amber flex items-center justify-center">
            <Database className="w-5 h-5 text-vintage-brown dark:text-vintage-amber" />
          </div>
          <div className="flex flex-col">
            <h1 className="font-serif uppercase tracking-[0.3em] text-sm text-vintage-brown dark:text-vintage-amber">
              {title}
            </h1>
            <div className="vintage-divider w-full mt-1" />
            <p className="text-[10px] uppercase tracking-[0.2em] text-vintage-brown/60 dark:text-vintage-amber/60 mt-0.5">
              Intelligent Data Query System
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <nav className="flex items-center border-2 border-vintage-brown/30 dark:border-vintage-amber/30 p-0.5 mr-2">
            {(['chat', 'schema', 'history'] as const).map((panel) => (
              <button
                key={panel}
                onClick={() => setActivePanel(panel)}
                className={`px-4 py-1.5 text-[10px] uppercase tracking-[0.2em] font-serif transition-colors duration-700 ${
                  activePanel === panel
                    ? 'bg-vintage-brown text-vintage-cream dark:bg-vintage-amber dark:text-vintage-ink'
                    : 'text-vintage-brown/50 dark:text-vintage-amber/50 hover:text-vintage-brown dark:hover:text-vintage-amber'
                }`}
              >
                {panel === 'chat' ? 'Chat' : panel === 'schema' ? 'Schema' : 'History'}
              </button>
            ))}
          </nav>

          <button
            onClick={clearMessages}
            className="p-2 text-vintage-brown/40 dark:text-vintage-amber/40 hover:text-vintage-brown dark:hover:text-vintage-amber transition-colors duration-700"
            title="Clear Conversation"
          >
            <Trash2 className="w-4 h-4" />
          </button>

          <button
            onClick={toggleTheme}
            className="p-2 text-vintage-brown/40 dark:text-vintage-amber/40 hover:text-vintage-brown dark:hover:text-vintage-amber transition-colors duration-700"
            title={theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
}