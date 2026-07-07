import { create } from 'zustand';
import type { Message, TableSchema, QueryResult } from '../types';

interface AppState {
  // 主题
  theme: 'light' | 'dark';
  toggleTheme: () => void;

  // 消息列表
  messages: Message[];
  addMessage: (msg: Message) => void;
  updateLastAssistant: (updates: Partial<Message>) => void;
  clearMessages: () => void;

  // 查询状态
  isQuerying: boolean;
  setQuerying: (v: boolean) => void;

  // Schema
  schemas: Record<string, TableSchema> | null;
  setSchemas: (s: Record<string, TableSchema> | null) => void;

  // 当前结果
  currentResult: QueryResult | null;
  setCurrentResult: (r: QueryResult | null) => void;

  // 面板
  activePanel: 'chat' | 'schema' | 'dashboard' | 'history';
  setActivePanel: (p: 'chat' | 'schema' | 'dashboard' | 'history') => void;
}

export const useStore = create<AppState>((set) => ({
  theme: (() => {
    if (typeof window !== 'undefined') {
      if (localStorage.getItem('theme') === 'dark') return 'dark';
      if (localStorage.getItem('theme') === 'light') return 'light';
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'light';
  })(),

  toggleTheme: () =>
    set((state) => {
      const next = state.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', next);
      return { theme: next };
    }),

  messages: [],
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  updateLastAssistant: (updates) =>
    set((state) => {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, ...updates };
      }
      return { messages: msgs };
    }),
  clearMessages: () => set({ messages: [], currentResult: null }),

  isQuerying: false,
  setQuerying: (v) => set({ isQuerying: v }),

  schemas: null,
  setSchemas: (s) => set({ schemas: s }),

  currentResult: null,
  setCurrentResult: (r) => set({ currentResult: r }),

  activePanel: 'chat',
  setActivePanel: (p) => set({ activePanel: p }),
}));