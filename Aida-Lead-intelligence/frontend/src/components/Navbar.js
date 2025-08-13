import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiHome, FiSettings, FiMail, FiFileText, FiBarChart2, FiServer, FiLogOut } from 'react-icons/fi';

const Navbar = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
      <div className="container-fluid">
        <Link className="navbar-brand" to="/dashboard">
          🎯 Aida Lead Intelligence
        </Link>
        
        <button 
          className="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link className="nav-link" to="/dashboard">
                <FiHome className="me-1" />
                Dashboard
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/outreach">
                <FiMail className="me-1" />
                Outreach
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/email-templates">
                <FiFileText className="me-1" />
                Email Templates
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/email-servers">
                <FiServer className="me-1" />
                Email Servers
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/email-tracking">
                <FiBarChart2 className="me-1" />
                Email Tracking
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/configuration">
                <FiSettings className="me-1" />
                Configuration
              </Link>
            </li>
          </ul>
          
          <ul className="navbar-nav">
            <li className="nav-item">
              <button 
                className="btn btn-outline-light btn-sm" 
                onClick={handleLogout}
              >
                <FiLogOut className="me-1" />
                Logout
              </button>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;