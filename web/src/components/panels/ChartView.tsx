import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { BarChart, LineChart, PieChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { ChartConfig } from '../../types';

echarts.use([BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer]);

interface ChartViewProps {
  chart: ChartConfig;
}

export function ChartView({ chart }: ChartViewProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current || chart.type === 'none' || chart.type === 'table') return;

    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current, undefined, {
        renderer: 'canvas',
      });
    }

    const isDark = document.documentElement.classList.contains('dark');

    // Vintage color palette
    const vintageColors = ['#8b4513', '#d4a373', '#c94c4c', '#2e4a3f', '#816904', '#5c2e0a'];

    instanceRef.current.setOption(
      {
        ...chart.option,
        color: vintageColors,
        backgroundColor: 'transparent',
        tooltip: {
          ...(chart.option?.tooltip as object || {}),
          backgroundColor: isDark ? '#2a1a0a' : '#f5e6d3',
          borderColor: '#8b4513',
          borderWidth: 2,
          textStyle: {
            color: isDark ? '#f5e6d3' : '#3b2208',
            fontSize: 12,
            fontFamily: 'Georgia, serif',
          },
        },
        xAxis: {
          ...(chart.option?.xAxis as object || {}),
          axisLabel: {
            color: isDark ? '#d4a373' : '#8b4513',
            fontSize: 11,
            fontFamily: 'Georgia, serif',
          },
          axisLine: { lineStyle: { color: '#8b4513', width: 2 } },
          axisTick: { lineStyle: { color: '#8b4513' } },
        },
        yAxis: {
          ...(chart.option?.yAxis as object || {}),
          axisLabel: {
            color: isDark ? '#d4a373' : '#8b4513',
            fontSize: 11,
            fontFamily: 'Georgia, serif',
          },
          splitLine: { lineStyle: { color: isDark ? '#3b2208' : '#d4a373', type: 'dashed', opacity: 0.3 } },
          axisLine: { lineStyle: { color: '#8b4513', width: 2 } },
        },
        legend: {
          ...(chart.option?.legend as object || {}),
          textStyle: {
            color: isDark ? '#d4a373' : '#8b4513',
            fontFamily: 'Georgia, serif',
            fontSize: 11,
          },
        },
      },
      true,
    );

    const handleResize = () => instanceRef.current?.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [chart]);

  useEffect(() => {
    return () => {
      instanceRef.current?.dispose();
      instanceRef.current = null;
    };
  }, []);

  if (chart.type === 'none') return null;

  if (chart.type === 'table' && chart.columns && chart.rows) {
    return (
      <div className="border-2 border-vintage-brown dark:border-vintage-amber shadow-vintage-sm overflow-hidden">
        <div className="px-4 py-2.5 border-b-2 border-vintage-brown/30 dark:border-vintage-amber/30 bg-vintage-wheat/50 dark:bg-vintage-ink/30">
          <span className="text-[10px] uppercase tracking-[0.2em] font-serif text-vintage-brown dark:text-vintage-amber">
            {chart.title || 'Data Table'}
          </span>
        </div>
        <div className="overflow-x-auto max-h-80">
          <table className="w-full text-sm font-serif">
            <thead>
              <tr className="border-b-2 border-vintage-brown/30 dark:border-vintage-amber/30">
                {chart.columns.map((col) => (
                  <th key={col} className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.15em] font-serif text-vintage-brown dark:text-vintage-amber whitespace-nowrap bg-vintage-cream dark:bg-vintage-ink/50">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {chart.rows.map((row, i) => (
                <tr
                  key={i}
                  className="border-b border-vintage-brown/10 dark:border-vintage-amber/10 hover:bg-vintage-wheat/30 dark:hover:bg-vintage-ink/20 transition-colors duration-700"
                >
                  {row.map((cell, j) => (
                    <td key={j} className="px-4 py-2 text-xs text-vintage-ink dark:text-vintage-cream whitespace-nowrap font-serif">
                      {String(cell ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div className="border-2 border-vintage-brown dark:border-vintage-amber shadow-vintage-sm overflow-hidden paper-texture dark:paper-texture-dark">
      <div className="px-4 py-2.5 border-b-2 border-vintage-brown/30 dark:border-vintage-amber/30">
        <span className="text-[10px] uppercase tracking-[0.2em] font-serif text-vintage-brown dark:text-vintage-amber">
          {chart.title || 'Chart'}
        </span>
      </div>
      <div ref={chartRef} className="chart-container" />
    </div>
  );
}