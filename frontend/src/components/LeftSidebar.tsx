import React from 'react';
import { Search, Filter, BookOpen } from 'lucide-react';
import { Filters } from '../../types';

interface LeftSidebarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  filters: Filters;
  onFilterChange: (key: string, val: string) => void;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({ 
  searchQuery, 
  onSearchChange, 
  filters, 
  onFilterChange 
}) => {
  const eras = ['Feudal', 'Primitive Accumulation', 'Industrial', 'Imperialist'];
  const modes = ['Slave', 'Feudal', 'Capitalist', 'Socialist Transition'];

  return (
    <div className="h-full p-4 flex flex-col gap-6">
      <div className="flex items-center gap-2 text-archive-muted font-mono text-xs uppercase tracking-widest">
        <BookOpen size={14} /> Query Archive
      </div>
      
      {/* Semantic Search */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 text-archive-muted" size={16} />
        <input 
          type="text" 
          value={searchQuery}
          onChange={e => onSearchChange(e.target.value)}
          placeholder="e.g. 'surplus value extraction 1848'"
          className="w-full bg-archive-bg border border-archive-border rounded-md py-2 pl-9 pr-3 text-sm font-mono focus:outline-none focus:border-archive-green transition-colors placeholder:text-archive-muted/50"
        />
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2 text-archive-muted font-mono text-xs uppercase tracking-widest">
          <Filter size={14} /> Historical Parameters
        </div>
        
        <div className="flex flex-col gap-2">
          <label className="text-xs font-mono text-archive-muted">ERA</label>
          <select 
            value={filters.era}
            onChange={e => onFilterChange('era', e.target.value)}
            className="bg-archive-bg border border-archive-border rounded px-3 py-2 text-sm font-mono focus:border-archive-blue focus:outline-none"
          >
            <option value="">All Eras</option>
            {eras.map(e => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs font-mono text-archive-muted">MODE OF PRODUCTION</label>
          <select 
            value={filters.modeOfProduction}
            onChange={e => onFilterChange('modeOfProduction', e.target.value)}
            className="bg-archive-bg border border-archive-border rounded px-3 py-2 text-sm font-mono focus:border-archive-blue focus:outline-none"
          >
            <option value="">All Modes</option>
            {modes.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
      </div>

      <div className="mt-auto pt-4 border-t border-archive-border">
        <div className="text-xs font-mono text-archive-muted space-y-1">
          <p>Nodes: <span className="text-archive-text">1,248</span></p>
          <p>Edges: <span className="text-archive-text">3,412</span></p>
          <p>Corpus: <span className="text-archive-text">Marx/Engels Collected Works</span></p>
        </div>
      </div>
    </div>
  );
};
