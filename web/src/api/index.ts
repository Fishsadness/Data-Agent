import type { QueryResult, StreamEvent, TableSchema } from '../types';

const BASE_URL = '/api';

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}

export async function getSchema(): Promise<{
  success: boolean;
  tables: string[];
  schemas: Record<string, TableSchema>;
  prompt_text: string;
}> {
  const res = await fetch(`${BASE_URL}/schema`);
  return res.json();
}

export async function getTableInfo(tableName: string): Promise<{
  success: boolean;
  table_name: string;
  schema: TableSchema;
  sample_data: Record<string, unknown>[];
}> {
  const res = await fetch(`${BASE_URL}/schema/${tableName}`);
  return res.json();
}

export async function queryData(question: string): Promise<QueryResult> {
  const res = await fetch(`${BASE_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  return res.json();
}

export async function* queryDataStream(question: string): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${BASE_URL}/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  if (!res.body) throw new Error('No response body');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim();
        if (data) {
          try {
            yield JSON.parse(data);
          } catch {
            // skip malformed json
          }
        }
      }
    }
  }
}

export async function executeSQL(sql: string): Promise<QueryResult> {
  const res = await fetch(`${BASE_URL}/sql/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail?.details?.join(', ') || err.detail || 'SQL 执行失败');
  }
  return res.json();
}