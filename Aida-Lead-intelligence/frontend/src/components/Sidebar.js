import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  FiHome, 
  FiSettings, 
  FiMail, 
  FiFileText, 
  FiBarChart2, 
  FiServer, 
  FiLogOut,
  FiMenu,
  FiX,
  FiZap,
  FiUsers
} from 'react-icons/fi';

const Sidebar = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    {
      path: '/dashboard',
      icon: FiHome,
      label: 'Dashboard',
      description: 'Overview & Analytics'
    },
    {
      path: '/lead-generation',
      icon: FiUsers,
      label: 'Lead Generation',
      description: 'Generate Leads'
    },
    {
      path: '/outreach',
      icon: FiMail,
      label: 'Outreach',
      description: 'Lead Management'
    },
    {
      path: '/email-templates',
      icon: FiFileText,
      label: 'Email Templates',
      description: 'Template Builder'
    },
    {
      path: '/email-servers',
      icon: FiServer,
      label: 'Email Servers',
      description: 'SMTP Configuration'
    },
    {
      path: '/email-tracking',
      icon: FiBarChart2,
      label: 'Email Tracking',
      description: 'Analytics & Reports'
    },
    {
      path: '/configuration',
      icon: FiSettings,
      label: 'Configuration',
      description: 'System Settings'
    }
  ];

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <FiZap />
          </div>
          {!isCollapsed && (
            <div className="brand-text">
              <h4>Aida</h4>
              <span>Lead Intelligence</span>
            </div>
          )}
        </div>
        <button 
          className="sidebar-toggle"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? <FiMenu /> : <FiX />}
        </button>
      </div>

      <nav className="sidebar-nav">
        <ul className="nav-menu">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <li key={item.path} className={`nav-item ${isActive ? 'active' : ''}`}>
                <Link to={item.path} className="nav-link">
                  <div className="nav-icon">
                    <Icon />
                  </div>
                  {!isCollapsed && (
                    <div className="nav-content">
                      <span className="nav-label">{item.label}</span>
                      <span className="nav-description">{item.description}</span>
                    </div>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <button 
          className="logout-btn"
          onClick={handleLogout}
        >
          <FiLogOut />
          {!isCollapsed && <span>Logout</span>}
        </button>
      </div>
    </div>
  );
};

export default Sidebar; 