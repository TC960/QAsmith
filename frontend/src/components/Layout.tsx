import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './Layout.css';
import ProgressBar from './ProgressBar';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const readStep = (): number => {
    const stored = typeof window !== 'undefined' ? window.localStorage.getItem('qa_progress_step') : null;
    const parsed = stored ? parseInt(stored, 10) : 1;
    return Math.min(Math.max(parsed || 1, 1), 5);
  };

  const [step, setStep] = useState<number>(readStep());

  useEffect(() => {
    const update = () => setStep(readStep());
    window.addEventListener('storage', update);
    window.addEventListener('qa_progress_changed', update as EventListener);
    return () => {
      window.removeEventListener('storage', update);
      window.removeEventListener('qa_progress_changed', update as EventListener);
    };
  }, []);

  const restart = () => {
    window.localStorage.setItem('qa_progress_step', '1');
    window.dispatchEvent(new Event('qa_progress_changed'));
    navigate('/');
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <h1 className="logo">QAsmith</h1>
          <button onClick={restart} className="nav-link">Restart</button>
        </div>
        <ProgressBar currentStep={step} />
      </header>
      <main className="main">{children}</main>
    </div>
  );
};

export default Layout;