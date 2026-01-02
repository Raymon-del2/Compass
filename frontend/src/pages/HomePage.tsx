import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ExampleSearches from '../components/ExampleSearches';

const logoUrl = '/Compass.png';

const HomePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (q: string) => {
    if (!q.trim()) return;
    navigate(`/search?q=${encodeURIComponent(q)}`);
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(query);
  };

  return (
    <div className="page">
      <img src={logoUrl} alt="Compass" className="logo" />
      <form onSubmit={onSubmit} className="search-box">
        <span className="search-icon">
          <i className="bi bi-search" />
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search the web..."
          className="search-input"
        />
        <button type="submit" className="search-btn" aria-label="Search">
          <i className="bi bi-search" />
        </button>
      </form>

      <ExampleSearches onExampleClick={handleSearch} />
    </div>
  );
};

export default HomePage;
