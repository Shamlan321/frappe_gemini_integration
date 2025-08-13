import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Alert, Spinner, Badge, Table, ProgressBar } from 'react-bootstrap';
import axios from 'axios';
import { FiDownload, FiUsers, FiMail, FiPhone, FiMapPin, FiStar, FiCheckCircle, FiAlertCircle, FiDatabase, FiUpload } from 'react-icons/fi';

const Outreach = () => {
  const [crmLeads, setCrmLeads] = useState([]);
  const [importedLeads, setImportedLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [importProgress, setImportProgress] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState('unknown');

  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/erp/test-connection');
      setConnectionStatus(response.data.success ? 'connected' : 'disconnected');
    } catch (error) {
      setConnectionStatus('disconnected');
    } finally {
      setLoading(false);
    }
  };

  const fetchCrmLeads = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await axios.get('/api/outreach/crm-leads');
      
      if (response.data.success) {
        setCrmLeads(response.data.leads);
        setSuccess(`Found ${response.data.leads.length} leads in your CRM`);
      } else {
        setError(response.data.message || 'Failed to fetch CRM leads');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while fetching CRM leads');
    } finally {
      setLoading(false);
    }
  };

  const importCrmLeads = async () => {
    try {
      setImporting(true);
      setError('');
      setSuccess('');
      setImportProgress(0);

      const response = await axios.post('/api/outreach/import-crm-leads', {
        leads: crmLeads
      });

      if (response.data.success) {
        setSuccess(`Successfully imported ${response.data.imported_count} leads from CRM`);
        setImportedLeads(response.data.imported_leads || []);
        setImportProgress(100);
      } else {
        setError(response.data.message || 'Failed to import CRM leads');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while importing CRM leads');
    } finally {
      setImporting(false);
    }
  };

  const renderConnectionStatus = () => {
    switch (connectionStatus) {
      case 'connected':
        return (
          <Alert variant="success" className="alert">
            <div className="d-flex align-items-center">
              <FiCheckCircle className="me-2" />
              <strong>Connected to ERPNext CRM</strong>
            </div>
          </Alert>
        );
      case 'disconnected':
        return (
          <Alert variant="danger" className="alert">
            <div className="d-flex align-items-center">
              <FiAlertCircle className="me-2" />
              <strong>Not connected to ERPNext CRM</strong>
            </div>
            <div className="mt-2">
              Please configure your ERPNext connection in the Configuration section.
            </div>
          </Alert>
        );
      default:
        return (
          <Alert variant="warning" className="alert">
            <div className="d-flex align-items-center">
              <Spinner animation="border" size="sm" className="me-2" />
              Checking connection status...
            </div>
          </Alert>
        );
    }
  };

  const renderCrmLeadRow = (lead) => {
    return (
      <tr key={lead.name}>
        <td>
          <div className="fw-bold">{lead.company_name || lead.name}</div>
          <small className="text-muted">{lead.lead_owner || 'No owner'}</small>
        </td>
        <td>
          <div className="d-flex align-items-center">
            <FiMail className="me-1" />
            {lead.email || 'No email'}
          </div>
        </td>
        <td>
          <div className="d-flex align-items-center">
            <FiPhone className="me-1" />
            {lead.mobile_no || lead.phone || 'No phone'}
          </div>
        </td>
        <td>
          <div className="d-flex align-items-center">
            <FiMapPin className="me-1" />
            {lead.city || 'No location'}
          </div>
        </td>
        <td>
          <Badge bg={lead.status === 'Lead' ? 'primary' : 'secondary'}>
            {lead.status || 'Unknown'}
          </Badge>
        </td>
      </tr>
    );
  };

  const renderImportedLeadRow = (lead) => {
    return (
      <tr key={lead.id}>
        <td>
          <div className="fw-bold">{lead.name}</div>
          <small className="text-muted">{lead.industry || 'No industry'}</small>
        </td>
        <td>
          <div className="d-flex align-items-center">
            <FiMail className="me-1" />
            {lead.email || 'No email'}
          </div>
        </td>
        <td>
          <div className="d-flex align-items-center">
            <FiPhone className="me-1" />
            {lead.phone || 'No phone'}
          </div>
        </td>
        <td>
          <div className="d-flex align-items-center">
            <FiMapPin className="me-1" />
            {lead.location || 'No location'}
          </div>
        </td>
        <td>
          <Badge bg="success">Imported</Badge>
        </td>
      </tr>
    );
  };

  return (
    <div className="page-container fade-in">
      <div className="page-header">
        <h1 className="page-title">Outreach</h1>
        <p className="page-subtitle">Import and manage leads from your CRM system</p>
      </div>

      {error && <Alert variant="danger" className="alert">{error}</Alert>}
      {success && <Alert variant="success" className="alert">{success}</Alert>}

      <div className="row mb-4">
        <div className="col-12">
          <Card className="card">
            <Card.Header className="card-header">
              <Card.Title className="card-title">
                <FiDatabase className="me-2" />
                CRM Connection Status
              </Card.Title>
            </Card.Header>
            <Card.Body className="card-body">
              {renderConnectionStatus()}
              
              {connectionStatus === 'connected' && (
                <div className="d-flex gap-2 mt-3">
                  <Button
                    variant="primary"
                    className="btn btn-primary"
                    onClick={fetchCrmLeads}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Fetching Leads...
                      </>
                    ) : (
                      <>
                        <FiUsers className="me-2" />
                        Fetch CRM Leads
                      </>
                    )}
                  </Button>
                  
                  {crmLeads.length > 0 && (
                    <Button
                      variant="success"
                      className="btn btn-success"
                      onClick={importCrmLeads}
                      disabled={importing}
                    >
                      {importing ? (
                        <>
                          <Spinner animation="border" size="sm" className="me-2" />
                          Importing...
                        </>
                      ) : (
                        <>
                          <FiUpload className="me-2" />
                          Import All Leads
                        </>
                      )}
                    </Button>
                  )}
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>

      {importing && (
        <div className="row mb-4">
          <div className="col-12">
            <Card className="card">
              <Card.Body className="card-body">
                <div className="d-flex align-items-center mb-2">
                  <FiUpload className="me-2" />
                  <strong>Importing leads...</strong>
                </div>
                <ProgressBar 
                  now={importProgress} 
                  className="mb-2"
                  variant="success"
                />
                <small className="text-muted">{importProgress}% complete</small>
              </Card.Body>
            </Card>
          </div>
        </div>
      )}

      {crmLeads.length > 0 && (
        <div className="row mb-4">
          <div className="col-12">
            <Card className="card">
              <Card.Header className="card-header">
                <Card.Title className="card-title">
                  <FiUsers className="me-2" />
                  CRM Leads ({crmLeads.length})
                </Card.Title>
              </Card.Header>
              <Card.Body className="card-body">
                <div className="table-responsive">
                  <Table className="table">
                    <thead>
                      <tr>
                        <th>Company & Owner</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Location</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {crmLeads.map(renderCrmLeadRow)}
                    </tbody>
                  </Table>
                </div>
              </Card.Body>
            </Card>
          </div>
        </div>
      )}

      {importedLeads.length > 0 && (
        <div className="row">
          <div className="col-12">
            <Card className="card">
              <Card.Header className="card-header">
                <Card.Title className="card-title">
                  <FiDownload className="me-2" />
                  Imported Leads ({importedLeads.length})
                </Card.Title>
              </Card.Header>
              <Card.Body className="card-body">
                <div className="table-responsive">
                  <Table className="table">
                    <thead>
                      <tr>
                        <th>Name & Industry</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Location</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {importedLeads.map(renderImportedLeadRow)}
                    </tbody>
                  </Table>
                </div>
              </Card.Body>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default Outreach; 