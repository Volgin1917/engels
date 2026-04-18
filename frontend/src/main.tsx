import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// Mock data for development (will be replaced with API calls)
const mockEntities = [
  {
    id: '1',
    label: 'Пролетариат',
    type: 'proletariat' as const,
    year: 1848,
    attributes: { class: 'working', era: 'Industrial' },
    rawText: 'The proletariat rises...'
  },
  {
    id: '2',
    label: 'Буржуазия',
    type: 'bourgeoisie' as const,
    year: 1789,
    attributes: { class: 'owning', era: 'Feudal' },
    rawText: 'The bourgeoisie owns...'
  },
  {
    id: '3',
    label: 'Манифест Коммунистической партии',
    type: 'event' as const,
    year: 1848,
    attributes: { type: 'publication', significance: 'high' },
    rawText: 'Workers of the world unite...'
  },
  {
    id: '4',
    label: 'Прибавочная стоимость',
    type: 'concept' as const,
    year: 1867,
    attributes: { category: 'economic', complexity: 'advanced' },
    rawText: 'Surplus value is...'
  }
];

const mockConnections = [
  { id: 'c1', source: '1', target: '2', relation: 'противоречит' },
  { id: 'c2', source: '3', target: '1', relation: 'описывает' },
  { id: 'c3', source: '4', target: '2', relation: 'эксплуатирует' }
];

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App entities={mockEntities} connections={mockConnections} />
  </React.StrictMode>,
);
