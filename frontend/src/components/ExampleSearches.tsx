import React from 'react';

const EXAMPLES = [
  'How to make French toast',
  'What\'s the weather near me?',
  'Easy dinner recipes for family',
  'Best-selling games of all time'
];

interface Props {
  onExampleClick: (q: string) => void;
}

const ExampleSearches: React.FC<Props> = ({ onExampleClick }) => {
  return (
    <div className="examples">
      {EXAMPLES.map((ex) => (
        <button
          key={ex}
          className="example-card"
          onClick={() => onExampleClick(ex)}
        >
          <span>{ex}</span>
          <i className="bi bi-arrow-right ms-auto"></i>
        </button>
      ))}
    </div>
  );
};

export default ExampleSearches;
