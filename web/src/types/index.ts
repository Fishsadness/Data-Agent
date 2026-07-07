export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  default: string | null;
}

export interface ForeignKey {
  columns: string[];
  referenced_table: string;
  referenced_columns: string[];
}

export interface TableSchema {
  table_name: string;
  columns: ColumnInfo[];
  foreign_keys: ForeignKey[];
}

export interface QueryResult {
  success: boolean;
  question: string;
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  answer: string;
  chart: ChartConfig;
  analysis: AnalysisResult;
  elapsed_ms: number;
  error: string;
}

export interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'table' | 'none';
  title?: string;
  columns?: string[];
  rows?: unknown[][];
  option?: Record<string, unknown>;
  error?: string;
}

export interface AnalysisResult {
  row_count: number;
  column_count: number;
  numeric_columns: string[];
  text_columns: string[];
  stats: Record<string, NumericStats | TextStats>;
}

export interface NumericStats {
  count: number;
  sum: number;
  avg: number;
  min: number;
  max: number;
  median: number;
}

export interface TextStats {
  unique_count: number;
  top_values: { value: string; count: number }[];
}

export interface StreamEvent {
  type: 'step' | 'sql' | 'sql_result' | 'data' | 'answer' | 'error' | 'done';
  content?: string;
  columns?: string[];
  rows?: Record<string, unknown>[];
  row_count?: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sql?: string;
  result?: QueryResult;
  timestamp: number;
}