import React from 'react';
import './ProgressBar.css';

interface ProgressBarProps {
  currentStep: number; // 1-5
}

const steps = [
  { key: 'url', label: 'URL' },
  { key: 'crawl', label: 'Crawl Pages' },
  { key: 'generate', label: 'Generate Tests' },
  { key: 'execute', label: 'Execute Tests' },
  { key: 'report', label: 'Report' }
];

const ProgressBar: React.FC<ProgressBarProps> = ({ currentStep }) => {
  return (
    <div className="progressbar">
      {steps.map((step, index) => {
        const stepIndex = index + 1;
        const status = stepIndex < currentStep ? 'done' : stepIndex === currentStep ? 'active' : 'todo';
        return (
          <div key={step.key} className={`progress-step ${status}`}>
            <div className="progress-dot" />
            <span className="progress-label">{step.label}</span>
            {index < steps.length - 1 && <div className="progress-line" />}
          </div>
        );
      })}
    </div>
  );
};

export default ProgressBar;


