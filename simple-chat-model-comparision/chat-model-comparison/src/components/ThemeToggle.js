import React from 'react';
import './ThemeToggle.css';

function ThemeToggle({ isDark, onToggle }) {
  return (
    <div className="theme-toggle">
      <label className="switch">
        <input
          type="checkbox"
          checked={isDark}
          onChange={onToggle}
        />
        <span className="slider">
          <span className="icon">
            {isDark ? '🌙' : '☀️'}
          </span>
        </span>
      </label>
      <span className="theme-label">
        {isDark ? 'Dark' : 'Light'} Mode
      </span>
    </div>
  );
}

export default ThemeToggle; 
