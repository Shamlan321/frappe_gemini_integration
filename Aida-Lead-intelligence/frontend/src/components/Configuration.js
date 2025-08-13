import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import axios from 'axios';
import { FiServer, FiUser, FiLock, FiSave, FiCheckCircle, FiSettings } from 'react-icons/fi';

const Configuration = () => {
  const [config, setConfig] = useState({
    erp_url: '',
    erp_username: '',
    erp_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    fetchCurrentConfig();
  }, []);

  const fetchCurrentConfig = async () => {
    try {
      const response = await axios.get('/api/config/erp');
      if (response.data.success && response.data.config) {
        setConfig({
          erp_url: response.data.config.erp_url || '',
          erp_username: response.data.config.erp_username || '',
          erp_password: '' // Don't populate password for security
        });
      }
    } catch (error) {
      console.error('Error fetching config:', error);
    }
  };

  const handleChange = (e) => {
    setConfig({
      ...config,
      [e.target.name]: e.target.value
    });
    setError('');
    setSuccess('');
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    if (!config.erp_url || !config.erp_username || !config.erp_password) {
      setError('Please fill in all fields before testing the connection');
      return;
    }

    setTesting(true);
    setError('');
    setSuccess('');
    setTestResult(null);

    try {
      const response = await axios.post('/api/erp/test-connection', {
        erp_url: config.erp_url,
        erp_username: config.erp_username,
        erp_password: config.erp_password
      });

      if (response.data.success) {
        setTestResult({ success: true, message: 'Connection successful!' });
      } else {
        setTestResult({ success: false, message: response.data.message || 'Connection failed' });
      }
    } catch (error) {
      setTestResult({ 
        success: false, 
        message: error.response?.data?.message || 'Connection test failed' 
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    
    if (!config.erp_url || !config.erp_username || !config.erp_password) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post('/api/config/erp', {
        erp_url: config.erp_url,
        erp_username: config.erp_username,
        erp_password: config.erp_password
      });

      if (response.data.success) {
        setSuccess('ERPNext configuration saved successfully!');
        setConfig(prev => ({ ...prev, erp_password: '' })); // Clear password field
      } else {
        setError(response.data.message || 'Failed to save configuration');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while saving configuration');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container fade-in">
      <div className="page-header">
        <h1 className="page-title">Configuration</h1>
        <p className="page-subtitle">Configure your ERPNext integration settings</p>
      </div>

      {error && <Alert variant="danger" className="alert">{error}</Alert>}
      {success && <Alert variant="success" className="alert">{success}</Alert>}

      <div className="row">
        <div className="col-lg-8">
          <Card className="card">
            <Card.Header className="card-header">
              <Card.Title className="card-title">
                <FiServer className="me-2" />
                ERPNext Configuration
              </Card.Title>
            </Card.Header>
            <Card.Body className="card-body">
              <Form onSubmit={handleSaveConfig}>
                <Form.Group className="form-group">
                  <Form.Label className="form-label">
                    <FiServer className="me-2" />
                    ERPNext URL
                  </Form.Label>
                  <Form.Control
                    type="url"
                    name="erp_url"
                    value={config.erp_url}
                    onChange={handleChange}
                    placeholder="https://your-erpnext-instance.com"
                    className="form-control"
                    required
                  />
                </Form.Group>

                <Form.Group className="form-group">
                  <Form.Label className="form-label">
                    <FiUser className="me-2" />
                    Username
                  </Form.Label>
                  <Form.Control
                    type="text"
                    name="erp_username"
                    value={config.erp_username}
                    onChange={handleChange}
                    placeholder="Enter your ERPNext username"
                    className="form-control"
                    required
                  />
                </Form.Group>

                <Form.Group className="form-group">
                  <Form.Label className="form-label">
                    <FiLock className="me-2" />
                    Password
                  </Form.Label>
                  <Form.Control
                    type="password"
                    name="erp_password"
                    value={config.erp_password}
                    onChange={handleChange}
                    placeholder="Enter your ERPNext password"
                    className="form-control"
                    required
                  />
                </Form.Group>

                <div className="d-flex gap-2">
                  <Button
                    type="submit"
                    variant="primary"
                    className="btn btn-primary"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <FiSave className="me-2" />
                        Save Configuration
                      </>
                    )}
                  </Button>

                  <Button
                    type="button"
                    variant="secondary"
                    className="btn btn-secondary"
                    onClick={handleTestConnection}
                    disabled={testing || !config.erp_url || !config.erp_username || !config.erp_password}
                  >
                    {testing ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Testing...
                      </>
                    ) : (
                      <>
                        <FiCheckCircle className="me-2" />
                        Test Connection
                      </>
                    )}
                  </Button>
                </div>
              </Form>

              {testResult && (
                <Alert 
                  variant={testResult.success ? "success" : "danger"} 
                  className="alert mt-3"
                >
                  <div className="d-flex align-items-center">
                    <FiCheckCircle className="me-2" />
                    {testResult.message}
                  </div>
                </Alert>
              )}
            </Card.Body>
          </Card>
        </div>

        <div className="col-lg-4">
          <Card className="card">
            <Card.Header className="card-header">
              <Card.Title className="card-title">
                <FiSettings className="me-2" />
                Configuration Info
              </Card.Title>
            </Card.Header>
            <Card.Body className="card-body">
              <div className="mb-3">
                <h6 className="fw-bold">ERPNext Integration</h6>
                <p className="text-muted small">
                  Configure your ERPNext instance connection to enable lead synchronization and CRM integration.
                </p>
              </div>
              
              <div className="mb-3">
                <h6 className="fw-bold">Required Fields</h6>
                <ul className="text-muted small">
                  <li>ERPNext URL (e.g., https://your-instance.com)</li>
                  <li>Username with API access</li>
                  <li>Password or API key</li>
                </ul>
              </div>

              <div className="mb-3">
                <h6 className="fw-bold">Security Note</h6>
                <p className="text-muted small">
                  Your password is encrypted and stored securely. It will not be displayed after saving.
                </p>
              </div>
            </Card.Body>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Configuration;