import React from 'react';
import { ChevronRight, FileText, Hash } from 'lucide-react';
import { Entity } from '../../types';

interface RightSidebarProps {
  entity: Entity | null;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({ entity }) => {
  if (!entity) {
    return (
      <div className="h-full flex items-center justify-center text-archive-muted font-mono text-sm">
        Select an entity to view dialectical attributes
      </div>
    );
  }

  const typeColorClass = { 
    proletariat: 'text-archive-red', 
    bourgeoisie: 'text-archive-blue', 
    event: 'text-archive-gold', 
    concept: 'text-archive-green' 
  }[entity.type];

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-archive-border bg-archive-bg">
        <div className={`font-mono text-xs uppercase tracking-widest mb-1 ${typeColorClass}`}>
          {entity.type}
        </div>
        <h2 className="text-lg font-bold text-archive-text leading-tight">{entity.label}</h2>
        <div className="mt-2 flex items-center gap-2 text-xs font-mono text-archive-muted">
          <Hash size={12} /> ID: {entity.id.slice(0, 8)}
        </div>
      </div>

      <div className="flex-1 p-4 space-y-6 overflow-y-auto">
        {/* Extracted Attributes */}
        <section>
          <h3 className="text-xs font-mono uppercase tracking-widest text-archive-muted mb-3 flex items-center gap-2">
            <FileText size={12} /> Extracted Attributes
          </h3>
          <div className="bg-archive-bg border border-archive-border rounded-md overflow-hidden">
            <table className="w-full text-sm font-mono">
              <tbody>
                {Object.entries(entity.attributes || {}).map(([key, val]) => (
                  <tr key={key} className="border-b border-archive-border last:border-0 hover:bg-archive-surface/50">
                    <td className="p-2 text-archive-muted border-r border-archive-border w-1/3">{key}</td>
                    <td className="p-2 text-archive-text">{val}</td>
                  </tr>
                ))}
                {Object.entries(entity.attributes || {}).length === 0 && (
                  <tr>
                    <td colSpan={2} className="p-2 text-archive-muted/60 text-center">No attributes extracted</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Raw Text Chunks */}
        <section>
          <h3 className="text-xs font-mono uppercase tracking-widest text-archive-muted mb-3 flex items-center gap-2">
            <ChevronRight size={12} /> Source Corpus Chunks
          </h3>
          <div className="space-y-3">
            {(entity.rawText ? [entity.rawText] : ['No direct textual extraction available.']).map((chunk, i) => (
              <div key={i} className="bg-archive-bg border border-archive-border rounded-md p-3 font-mono text-xs leading-relaxed text-archive-muted/90">
                <span className="text-archive-muted/50 select-none mr-2">[{i + 1}]</span>
                {chunk}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};
