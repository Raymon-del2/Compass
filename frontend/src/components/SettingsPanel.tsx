import React, { useState } from 'react';

interface Props {}

const SettingsPanel: React.FC<Props> = () => {
  const [open, setOpen] = useState(false);

  return (
    <div className="settings-wrapper">
      <button
        aria-label="Settings"
        className="icon-btn settings-btn"
        onClick={() => setOpen((o) => !o)}
      >
        {/* gear */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          className="icon"
        >
          <path
            fill="currentColor"
            d="M8.75 3.63C8.907 2.69 9.72 2 10.675 2h2.65c.955 0 1.769.69 1.925 1.63l.219 1.31c.017.104.095.23.256.319q.127.07.25.145c.157.095.306.1.405.062L17.624 5a1.95 1.95 0 0 1 2.374.852l1.325 2.296a1.95 1.95 0 0 1-.45 2.482l-1.026.845c-.081.067-.151.198-.148.38.003.097.003.194 0 .29-.003.182.067.313.148.38l1.027.845c.736.606.926 1.656.45 2.482l-1.326 2.296a1.95 1.95 0 0 1-2.375.852l-1.243-.466c-.099-.037-.248-.033-.405.062q-.123.075-.25.145c-.16.089-.24.215-.256.32l-.219 1.309A1.95 1.95 0 0 1 13.326 22h-2.652c-.953 0-1.767-.69-1.924-1.63l-.218-1.31c-.018-.104-.096-.23-.256-.319a8 8 0 0 1-.251-.145c-.157-.095-.306-.1-.405-.062L6.377 19a1.95 1.95 0 0 1-2.375-.852l-1.325-2.296a1.95 1.95 0 0 1 .45-2.482l1.026-.845c.081-.067.151-.198.148-.38a8 8 0 0 1 0-.29c-.003-.182.067-.313.148-.38l-1.027-.845a1.95 1.95 0 0 1-.45-2.482l1.326-2.296A1.95 1.95 0 0 1 6.377 5l1.243.466c.1.037.248.033.405-.062q.124-.075.25-.145c.161-.089.24-.215.257-.32zM12 9.735a2.265 2.265 0 1 0 0 4.53 2.265 2.265 0 0 0 0-4.53"
          />
        </svg>
      </button>
      {open && (
        <div className="settings-panel" onClick={() => setOpen(false)}>
          <div className="settings-card" onClick={(e) => e.stopPropagation()}>
            <h3 className="panel-title">Quick settings</h3>
            <div className="panel-section">
              <h4>Theme</h4>
              <div className="theme-options">Dark</div>
            </div>
            <div className="panel-section">
              <h4>Safe search</h4>
              <div>Moderate</div>
            </div>
            <div className="panel-section">
              <h4>Answer with AI</h4>
              <label className="switch">
                <input type="checkbox" defaultChecked />
                <span className="slider"></span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPanel;
