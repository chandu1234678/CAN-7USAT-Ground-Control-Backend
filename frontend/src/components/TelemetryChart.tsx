import { useEffect, useRef } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';

interface TelemetryChartProps {
  data: Array<{ time: number; value: number }>;
  title: string;
  color: string;
  unit: string;
  height?: number;
}

export const TelemetryChart: React.FC<TelemetryChartProps> = ({
  data, title, color, unit, height = 160
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const plotRef = useRef<uPlot | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const times  = data.length > 0 ? data.map(d => d.time)  : [0, 1];
    const values = data.length > 0 ? data.map(d => d.value) : [0, 0];

    const w = containerRef.current.clientWidth || 400;

    const opts: uPlot.Options = {
      width: w,
      height,
      title,
      padding: [8, 8, 0, 0],
      cursor: { show: false },
      legend: { show: false },
      scales: {
        x: {
          time: false,
          // Always start from 0 - show full history
          range: () => [0, Math.max(times[times.length - 1] ?? 1, 1)],
        },
        y: { auto: true },
      },
      series: [
        {},
        {
          stroke: color,
          width: 2,
          fill: color + '18',
          points: { show: false },
        },
      ],
      axes: [
        {
          stroke: '#444',
          ticks: { stroke: '#444', width: 1 },
          grid:  { stroke: '#ddd', width: 1 },
          font:  '10px Arial',
        },
        {
          stroke: '#444',
          ticks: { stroke: '#444', width: 1 },
          grid:  { stroke: '#ddd', width: 1 },
          font:  '10px Arial',
          values: (_u, vals) => vals.map(v => v.toFixed(0) + unit),
          size: 52,
        },
      ],
    };

    if (plotRef.current) {
      plotRef.current.destroy();
      plotRef.current = null;
    }

    plotRef.current = new uPlot(opts, [times, values], containerRef.current);

    const onResize = () => {
      if (plotRef.current && containerRef.current) {
        plotRef.current.setSize({ width: containerRef.current.clientWidth, height });
      }
    };
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      plotRef.current?.destroy();
      plotRef.current = null;
    };
  }, [data, color, unit, height, title]);

  return (
    <div ref={containerRef} style={{ width: '100%', background: '#fff' }} />
  );
};
