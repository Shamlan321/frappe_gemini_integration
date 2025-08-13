import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiUser, FiMail, FiLock, FiUserPlus, FiZap } from 'react-icons/fi';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      setLoading(false);
      return;
    }

    const result = await register(formData.username, formData.email, formData.password);
    
    if (result.success) {
      setSuccess('Registration successful! You can now login.');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
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
              <p className="page-subtitle">Create Your Account</p>
            </div>
            
            {error && (
              <Alert variant="danger" className="alert">
                {error}
              </Alert>
            )}
            
            {success && (
              <Alert variant="success" className="alert">
                {success}
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
                  placeholder="Choose a username"
                  required
                  className="form-control"
                />
              </Form.Group>
              
              <Form.Group className="form-group">
                <Form.Label className="form-label">
                  <FiMail className="me-2" />
                  Email
                </Form.Label>
                <Form.Control
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Enter your email"
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
                  placeholder="Create a password"
                  required
                  className="form-control"
                />
              </Form.Group>
              
              <Form.Group className="form-group">
                <Form.Label className="form-label">
                  <FiLock className="me-2" />
                  Confirm Password
                </Form.Label>
                <Form.Control
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm your password"
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
                    Creating Account...
                  </>
                ) : (
                  <>
                    <FiUserPlus className="me-2" />
                    Create Account
                  </>
                )}
              </Button>
            </Form>
            
            <div className="text-center mt-4">
              <p className="text-muted mb-0">
                Already have an account?{' '}
                <Link to="/login" className="text-primary fw-semibold text-decoration-none">
                  Sign In
                </Link>
              </p>
            </div>
          </Card.Body>
        </Card>
      </div>
    </div>
  );
};

export default Register;