import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiUser, FiLock, FiLogIn, FiZap } from 'react-icons/fi';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(formData.username, formData.password);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.message);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-vh-100 d-flex align-items-center justify-content-center" style={{ background: 'linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%)' }}>
      <div className="w-100" style={{ maxWidth: '400px' }}>
        <Card className="card shadow-xl">
          <Card.Body className="p-5">
            <div className="text-center mb-4">
              <div className="brand-icon mx-auto mb-3" style={{ width: '60px', height: '60px', fontSize: '1.5rem' }}>
                <FiZap />
              </div>
              <h2 className="page-title mb-2">Aida</h2>
              <p className="page-subtitle">Lead Intelligence Platform</p>
            </div>
            
            {error && (
              <Alert variant="danger" className="alert">
                {error}
              </Alert>
            )}
            
            <Form onSubmit={handleSubmit}>
              <Form.Group className="form-group">
                <Form.Label className="form-label">
                  <FiUser className="me-2" />
                  Username
                </Form.Label>
                <Form.Control
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="Enter your username"
                  required
                  className="form-control"
                />
              </Form.Group>
              
              <Form.Group className="form-group">
                <Form.Label className="form-label">
                  <FiLock className="me-2" />
                  Password
                </Form.Label>
                <Form.Control
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  required
                  className="form-control"
                />
              </Form.Group>
              
              <Button 
                type="submit" 
                variant="primary" 
                size="lg" 
                className="btn btn-primary w-100"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Signing In...
                  </>
                ) : (
                  <>
                    <FiLogIn className="me-2" />
                    Sign In
                  </>
                )}
              </Button>
            </Form>
            
            <div className="text-center mt-4">
              <p className="text-muted mb-0">
                Don't have an account?{' '}
                <Link to="/register" className="text-primary fw-semibold text-decoration-none">
                  Sign Up
                </Link>
              </p>
            </div>
          </Card.Body>
        </Card>
      </div>
    </div>
  );
};

export default Login;