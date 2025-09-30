import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home' },
    { path: '/crawl', label: 'Crawl' },
    { path: '/tests', label: 'Tests' },
    { path: '/results', label: 'Results' },
  ];

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <h1 className="logo">QAsmith</h1>
          <nav className="nav">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="main">{children}</main>
    </div>
  );
};

export default Layout;