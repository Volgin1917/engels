import React, { useEffect, useRef } from 'react';
import { Entity, Connection, TimeRange } from '../../types';

interface GraphCanvasProps {
  entities: Entity[];
  connections: Connection[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  timeRange: TimeRange;
}

const TYPE_COLORS: Record<string, string> = {
  proletariat: '#ef4444',
  bourgeoisie: '#3b82f6',
  event: '#eab308',
  concept: '#22c55e'
};

export const GraphCanvas: React.FC<GraphCanvasProps> = ({ 
  entities, 
  connections, 
  selectedId, 
  onSelect,
  timeRange 
}) => {
  const canvasRef = useRef<HTMLDivElement>(null);

  // Simple force-directed visualization placeholder
  // In production, this will use @antv/xflow or d3-force
  useEffect(() => {
    console.log('GraphCanvas updated:', { entities: entities.length, connections: connections.length, timeRange });
  }, [entities, connections, timeRange]);

  return (
    <div className="w-full h-full relative" ref={canvasRef}>
      {/* Placeholder for graph visualization */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <p className="font-mono text-archive-muted text-sm mb-2">Graph Visualization</p>
          <p className="font-mono text-archive-muted/60 text-xs">
            Nodes: {entities.length} | Edges: {connections.length}
          </p>
          <p className="font-mono text-archive-muted/40 text-xs mt-4">
            (@antv/xflow integration pending)
          </p>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 flex gap-4 bg-archive-surface/90 backdrop-blur border border-archive-border px-3 py-2 rounded-md">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-xs font-mono uppercase text-archive-muted">{type.replace('_', ' ')}</span>
          </div>
        ))}
      </div>

      {/* Selected entity indicator */}
      {selectedId && (
        <div className="absolute top-4 right-4 bg-archive-surface/90 backdrop-blur border border-archive-green px-3 py-2 rounded-md">
          <span className="text-xs font-mono text-archive-green">
            Selected: {entities.find(e => e.id === selectedId)?.label || 'Unknown'}
          </span>
        </div>
      )}
    </div>
  );
};
