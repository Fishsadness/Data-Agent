import { useEffect, useState } from 'react';
import { ChevronRight, Table2, Key, Link, ArrowRight } from 'lucide-react';
import { getSchema } from '../../api';
import { useStore } from '../../store';
import type { TableSchema, ColumnInfo } from '../../types';

export function SchemaPanel() {
  const { schemas, setSchemas } = useStore();
  const [expandedTable, setExpandedTable] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!schemas) {
      setLoading(true);
      getSchema()
        .then((data) => setSchemas(data.schemas))
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center paper-texture dark:paper-texture-dark">
        <div className="flex items-center gap-2 text-sm font-serif text-vintage-brown/50 dark:text-vintage-amber/50">
          <span className="typing-dot w-1.5 h-1.5 bg-vintage-brown/50 dark:bg-vintage-amber/50" />
          <span className="typing-dot w-1.5 h-1.5 bg-vintage-brown/50 dark:bg-vintage-amber/50" />
          <span className="typing-dot w-1.5 h-1.5 bg-vintage-brown/50 dark:bg-vintage-amber/50" />
        </div>
      </div>
    );
  }

  if (!schemas || Object.keys(schemas).length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center paper-texture dark:paper-texture-dark">
        <p className="font-serif text-sm text-vintage-brown/40 dark:text-vintage-amber/40 italic">
          No database schema available
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 paper-texture dark:paper-texture-dark">
      <div className="max-w-2xl mx-auto space-y-4">
        <h3 className="font-serif uppercase tracking-[0.3em] text-xs text-vintage-brown/60 dark:text-vintage-amber/60 mb-6">
          Database Structure
        </h3>
        {Object.entries(schemas).map(([tableName, schema]) => (
          <SchemaTable
            key={tableName}
            tableName={tableName}
            schema={schema}
            isExpanded={expandedTable === tableName}
            onToggle={() =>
              setExpandedTable(expandedTable === tableName ? null : tableName)
            }
          />
        ))}
      </div>
    </div>
  );
}

function SchemaTable({
  tableName,
  schema,
  isExpanded,
  onToggle,
}: {
  tableName: string;
  schema: TableSchema;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border-2 border-vintage-brown dark:border-vintage-amber overflow-hidden shadow-vintage-sm transition-colors duration-700">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-5 py-4 hover:bg-vintage-wheat/50 dark:hover:bg-vintage-ink/30 transition-colors duration-700"
      >
        <ChevronRight
          className={`w-4 h-4 text-vintage-brown/50 dark:text-vintage-amber/50 transition-transform duration-700 ${
            isExpanded ? 'rotate-90' : ''
          }`}
        />
        <Table2 className="w-4 h-4 text-vintage-brown dark:text-vintage-amber" />
        <span className="font-serif text-sm text-vintage-ink dark:text-vintage-cream">
          {tableName}
        </span>
        <span className="text-[10px] uppercase tracking-[0.15em] font-serif text-vintage-brown/40 dark:text-vintage-amber/40 ml-auto">
          {schema.columns.length} columns
        </span>
      </button>

      {isExpanded && (
        <div className="border-t-2 border-vintage-brown/30 dark:border-vintage-amber/30">
          <div className="p-4 space-y-1">
            {schema.columns.map((col: ColumnInfo) => (
              <div
                key={col.name}
                className="flex items-center gap-2 px-3 py-2 hover:bg-vintage-wheat/30 dark:hover:bg-vintage-ink/20 transition-colors duration-700"
              >
                {col.primary_key && (
                  <Key className="w-3 h-3 text-vintage-accent shrink-0" />
                )}
                <span className="text-sm font-mono text-vintage-ink dark:text-vintage-cream">
                  {col.name}
                </span>
                <span className="text-[10px] font-mono text-vintage-brown/50 dark:text-vintage-amber/50">
                  {col.type}
                </span>
                {!col.nullable && (
                  <span className="text-[8px] uppercase tracking-wider px-1.5 py-0.5 border border-vintage-accent text-vintage-accent dark:text-vintage-accent font-serif">
                    NOT NULL
                  </span>
                )}
              </div>
            ))}
          </div>

          {schema.foreign_keys.length > 0 && (
            <div className="border-t-2 border-vintage-brown/30 dark:border-vintage-amber/30 p-4">
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.15em] font-serif text-vintage-brown/50 dark:text-vintage-amber/50 mb-3">
                <Link className="w-3 h-3" />
                Foreign Keys
              </div>
              {schema.foreign_keys.map((fk, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 text-xs font-serif text-vintage-ink dark:text-vintage-cream ml-2 py-1"
                >
                  <span className="font-mono text-vintage-brown dark:text-vintage-amber">
                    {fk.columns.join(', ')}
                  </span>
                  <ArrowRight className="w-3 h-3 text-vintage-brown/50 dark:text-vintage-amber/50" />
                  <span className="font-mono text-vintage-forest dark:text-vintage-amber">
                    {fk.referenced_table}
                  </span>
                  <span className="text-vintage-brown/40 dark:text-vintage-amber/40 font-mono">
                    ({fk.referenced_columns.join(', ')})
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}