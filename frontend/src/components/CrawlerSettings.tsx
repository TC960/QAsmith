import React, { useState } from 'react';
import './CrawlerSettings.css';

export interface CrawlerConfig {
  max_depth: number;
  max_pages: number;
  timeout: number;
  screenshot: boolean;
  page_delay_ms: number;
  skip_embeddings: boolean;
}

interface CrawlerSettingsProps {
  settings: CrawlerConfig;
  onSettingsChange: (settings: CrawlerConfig) => void;
  disabled?: boolean;
}

const CrawlerSettings: React.FC<CrawlerSettingsProps> = ({ 
  settings, 
  onSettingsChange, 
  disabled = false 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleChange = (key: keyof CrawlerConfig, value: any) => {
    onSettingsChange({
      ...settings,
      [key]: value
    });
  };

  const presets = {
    fast: {
      max_depth: 1,
      max_pages: 10,
      timeout: 10000,
      screenshot: false,
      page_delay_ms: 200,
      skip_embeddings: true
    },
    balanced: {
      max_depth: 2,
      max_pages: 20,
      timeout: 15000,
      screenshot: false,
      page_delay_ms: 300,
      skip_embeddings: true
    },
    thorough: {
      max_depth: 3,
      max_pages: 50,
      timeout: 30000,
      screenshot: false,
      page_delay_ms: 500,
      skip_embeddings: false
    }
  };

  const applyPreset = (preset: keyof typeof presets) => {
    onSettingsChange(presets[preset]);
  };

  return (
    <div className="crawler-settings">
      <div className="settings-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>⚙️ Crawler Settings</h3>
        <button className="toggle-btn" type="button">
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {isExpanded && (
        <div className="settings-content">
          {/* Presets */}
          <div className="presets-section">
            <label>Quick Presets:</label>
            <div className="preset-buttons">
              <button 
                type="button"
                onClick={() => applyPreset('fast')} 
                disabled={disabled}
                className="preset-btn fast"
              >
                ⚡ Fast
              </button>
              <button 
                type="button"
                onClick={() => applyPreset('balanced')} 
                disabled={disabled}
                className="preset-btn balanced"
              >
                ⚖️ Balanced
              </button>
              <button 
                type="button"
                onClick={() => applyPreset('thorough')} 
                disabled={disabled}
                className="preset-btn thorough"
              >
                🔍 Thorough
              </button>
            </div>
          </div>

          <div className="settings-divider"></div>

          {/* Individual Settings */}
          <div className="settings-grid">
            {/* Max Depth */}
            <div className="setting-item">
              <label htmlFor="max_depth">
                Max Depth
                <span className="help-icon" title="How many levels deep to crawl from the homepage">ℹ️</span>
              </label>
              <input
                type="number"
                id="max_depth"
                min="1"
                max="5"
                value={settings.max_depth}
                onChange={(e) => handleChange('max_depth', parseInt(e.target.value))}
                disabled={disabled}
              />
              <span className="setting-value">{settings.max_depth} levels</span>
            </div>

            {/* Max Pages */}
            <div className="setting-item">
              <label htmlFor="max_pages">
                Max Pages
                <span className="help-icon" title="Maximum number of pages to crawl">ℹ️</span>
              </label>
              <input
                type="number"
                id="max_pages"
                min="5"
                max="100"
                step="5"
                value={settings.max_pages}
                onChange={(e) => handleChange('max_pages', parseInt(e.target.value))}
                disabled={disabled}
              />
              <span className="setting-value">{settings.max_pages} pages</span>
            </div>

            {/* Page Delay */}
            <div className="setting-item">
              <label htmlFor="page_delay_ms">
                Page Delay
                <span className="help-icon" title="Delay between page requests (ms)">ℹ️</span>
              </label>
              <input
                type="number"
                id="page_delay_ms"
                min="0"
                max="2000"
                step="100"
                value={settings.page_delay_ms}
                onChange={(e) => handleChange('page_delay_ms', parseInt(e.target.value))}
                disabled={disabled}
              />
              <span className="setting-value">{settings.page_delay_ms}ms</span>
            </div>

            {/* Timeout */}
            <div className="setting-item">
              <label htmlFor="timeout">
                Page Timeout
                <span className="help-icon" title="Timeout for loading each page (ms)">ℹ️</span>
              </label>
              <input
                type="number"
                id="timeout"
                min="5000"
                max="60000"
                step="5000"
                value={settings.timeout}
                onChange={(e) => handleChange('timeout', parseInt(e.target.value))}
                disabled={disabled}
              />
              <span className="setting-value">{settings.timeout / 1000}s</span>
            </div>

            {/* Skip Embeddings */}
            <div className="setting-item checkbox-item">
              <label htmlFor="skip_embeddings">
                Fast Mode (Skip AI Embeddings)
                <span className="help-icon" title="Disable AI embeddings for faster crawling">ℹ️</span>
              </label>
              <input
                type="checkbox"
                id="skip_embeddings"
                checked={settings.skip_embeddings}
                onChange={(e) => handleChange('skip_embeddings', e.target.checked)}
                disabled={disabled}
              />
              <span className="setting-value">{settings.skip_embeddings ? 'Enabled' : 'Disabled'}</span>
            </div>

            {/* Screenshot */}
            <div className="setting-item checkbox-item">
              <label htmlFor="screenshot">
                Take Screenshots
                <span className="help-icon" title="Capture screenshots of each page">ℹ️</span>
              </label>
              <input
                type="checkbox"
                id="screenshot"
                checked={settings.screenshot}
                onChange={(e) => handleChange('screenshot', e.target.checked)}
                disabled={disabled}
              />
              <span className="setting-value">{settings.screenshot ? 'Enabled' : 'Disabled'}</span>
            </div>
          </div>

          {/* Estimated Time */}
          <div className="estimate-section">
            <div className="estimate">
              ⏱️ Estimated time: <strong>
                {Math.ceil((settings.max_pages * (settings.timeout + settings.page_delay_ms)) / 1000 / 60)} minutes
              </strong>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CrawlerSettings;

