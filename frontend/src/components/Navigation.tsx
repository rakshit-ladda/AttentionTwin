import React from 'react';
import { UserCheck, BellRing, GitCompare, History } from 'lucide-react';
import { NavTab } from '../types';

interface NavigationProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, onTabChange }) => {
  const tabs: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'profile', label: 'Attention Profile', icon: <UserCheck size={18} /> },
    { id: 'simulator', label: 'Notification Simulator', icon: <BellRing size={18} /> },
    { id: 'counterfactual', label: 'Counterfactual Comparison', icon: <GitCompare size={18} /> },
    { id: 'history', label: 'History and Learning', icon: <History size={18} /> },
  ];

  return (
    <nav className="app-nav">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.icon}
          <span>{tab.label}</span>
        </button>
      ))}
    </nav>
  );
};
