export interface Entity {
  id: string;
  label: string;
  type: 'proletariat' | 'bourgeoisie' | 'event' | 'concept';
  year?: number;
  attributes: Record<string, string>;
  rawText?: string;
}

export interface Connection {
  id: string;
  source: string;
  target: string;
  relation: string;
}

export interface TimeRange {
  start: Date;
  end: Date;
}

export interface Filters {
  era: string;
  modeOfProduction: string;
}
