import React, { useEffect, useRef } from 'react';
import { Entity, Connection, TimeRange } from '../../types';

interface BottomTimelineProps {
  entities: Entity[];
  connections: Connection[];
  timeRange: TimeRange;
  onTimeRangeChange: (start: Date, end: Date) => void;
  onEntitySelect: (id: string) => void;
}

const TYPE_COLORS: Record<string, string> = {
  proletariat: '#ef4444',
  bourgeoisie: '#3b82f6',
  event: '#eab308',
  concept: '#22c55e'
};

export const BottomTimeline: React.FC<BottomTimelineProps> = ({ 
  entities, 
  timeRange, 
  onTimeRangeChange, 
  onEntitySelect 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Simple timeline visualization placeholder
    // In production, this will use vis-timeline
    console.log('Timeline updated:', { entities: entities.length, timeRange });

    // Cleanup
    return () => {
      if (timelineRef.current) {
        timelineRef.current.destroy();
      }
    };
  }, [entities, timeRange]);

  const entitiesWithYear = entities.filter(e => e.year);

  return (
    <div className="w-full h-full p-2 flex flex-col">
      <div className="text-xs font-mono uppercase tracking-widest text-archive-muted mb-1">
        Chronological Axis
      </div>
      
      {/* Timeline placeholder */}
      <div 
        ref={containerRef}
        className="flex-1 bg-archive-bg rounded border border-archive-border overflow-hidden relative"
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <p className="font-mono text-archive-muted text-sm mb-2">
              Timeline: {timeRange.start.getFullYear()} - {timeRange.end.getFullYear()}
            </p>
            <p className="font-mono text-archive-muted/60 text-xs">
              Events: {entitiesWithYear.length}
            </p>
            <p className="font-mono text-archive-muted/40 text-xs mt-4">
              (vis-timeline integration pending)
            </p>
          </div>
        </div>

        {/* Simple year markers */}
        <div className="absolute bottom-0 left-0 right-0 h-8 border-t border-archive-border flex items-end px-4 pb-1">
          <span className="text-xs font-mono text-archive-muted">{timeRange.start.getFullYear()}</span>
          <span className="ml-auto text-xs font-mono text-archive-muted">{timeRange.end.getFullYear()}</span>
        </div>
      </div>
    </div>
  );
};
