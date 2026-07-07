import { useEffect } from 'react';
import { useStore } from '../store';
import { MessageList } from '../components/chat/MessageList';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatHeader } from '../components/chat/ChatHeader';
import { SchemaPanel } from '../components/panels/SchemaPanel';
import { DashboardPanel } from '../components/panels/DashboardPanel';
import { queryData } from '../api';
import { generateId } from '../lib/utils';
import type { Message } from '../types';

export function Home() {
  const {
    addMessage,
    updateLastAssistant,
    setQuerying,
    isQuerying,
    activePanel,
    setCurrentResult,
  } = useStore();

  const handleSend = async (question: string) => {
    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: question,
      timestamp: Date.now(),
    };
    addMessage(userMsg);

    const assistantMsg: Message = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    };
    addMessage(assistantMsg);
    setQuerying(true);

    try {
      const result = await queryData(question);

      updateLastAssistant({
        content: result.answer || (result.error ? `Query failed: ${result.error}` : 'Query complete'),
        sql: result.sql || undefined,
        result: result.success ? result : undefined,
      });

      if (result.success) {
        setCurrentResult(result);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      updateLastAssistant({ content: `Query failed: ${message}` });
    } finally {
      setQuerying(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-[#f5e6d3] dark:bg-[#2a1a0a]">
      <ChatHeader />
      {activePanel === 'chat' && (
        <>
          <MessageList />
          <ChatInput onSend={handleSend} disabled={isQuerying} />
        </>
      )}
      {activePanel === 'schema' && <SchemaPanel />}
      {activePanel === 'dashboard' && <DashboardPanel activePanel={activePanel} />}
      {activePanel === 'history' && (
        <div className="flex-1 flex items-center justify-center paper-texture dark:paper-texture-dark">
          <div className="text-center">
            <p className="font-serif text-sm text-vintage-brown/40 dark:text-vintage-amber/40 italic">
              History records — coming soon
            </p>
            <div className="vintage-divider w-32 mx-auto mt-3" />
          </div>
        </div>
      )}
    </div>
  );
}