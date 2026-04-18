import React from 'react';
import { Entity, Connection, TimeRange, Filters } from '../types';

interface EngelsDashboardProps {
  entities: Entity[];
  connections: Connection[];
}

export const EngelsDashboard: React.FC<EngelsDashboardProps> = ({ entities, connections }) => {
  const [selectedEntityId, setSelectedEntityId] = React.useState<string | null>(null);
  const [timeRange, setTimeRange] = React.useState<TimeRange>({
    start: new Date(1789, 0, 1),
    end: new Date(1917, 11, 31)
  });
  const [filters, setFilters] = React.useState<Filters>({ era: '', modeOfProduction: '' });
  const [searchQuery, setSearchQuery] = React.useState('');

  const selectedEntity = entities.find(e => e.id === selectedEntityId) || null;

  const handleEntitySelect = React.useCallback((id: string) => setSelectedEntityId(id), []);
  
  const handleTimeRangeChange = React.useCallback((start: Date, end: Date) => {
    setTimeRange({ start, end });
  }, []);
  
  const handleFilterChange = React.useCallback((key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  return (
    <div className="h-screen w-full bg-archive-bg text-archive-text font-sans overflow-hidden">
      {/* Archival Grid Overlay */}
      <div className="fixed inset-0 pointer-events-none bg-grid-archival bg-[size:40px_40px] opacity-[0.04]" />

      {/* Main Grid Layout */}
      <div className="relative z-10 grid grid-cols-[280px_1fr_340px] grid-rows-[1fr_220px] h-full">
        {/* Left Sidebar */}
        <aside className="row-span-2 border-r border-archive-border bg-archive-surface">
          <LeftSidebar 
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            filters={filters}
            onFilterChange={handleFilterChange}
          />
        </aside>

        {/* Main Graph Canvas */}
        <main className="col-start-2 row-start-1 border-b border-archive-border bg-archive-bg relative">
          <GraphCanvas 
            entities={entities}
            connections={connections}
            selectedId={selectedEntityId}
            onSelect={handleEntitySelect}
            timeRange={timeRange}
          />
          <div className="absolute top-4 left-4 font-mono text-xs tracking-widest text-archive-muted uppercase">
            System: Engels // Mode: Dialectical Analysis
          </div>
        </main>

        {/* Right Entity Panel */}
        <aside className="row-span-2 col-start-3 border-l border-archive-border bg-archive-surface overflow-y-auto">
          <RightSidebar entity={selectedEntity} />
        </aside>

        {/* Bottom Timeline */}
        <footer className="col-start-2 row-start-2 bg-archive-surface border-t border-archive-border">
          <BottomTimeline 
            entities={entities}
            connections={connections}
            timeRange={timeRange}
            onTimeRangeChange={handleTimeRangeChange}
            onEntitySelect={handleEntitySelect}
          />
        </footer>
      </div>
    </div>
  );
};

import { LeftSidebar } from './components/LeftSidebar';
import { GraphCanvas } from './components/GraphCanvas';
import { BottomTimeline } from './components/BottomTimeline';
import { RightSidebar } from './components/RightSidebar';
