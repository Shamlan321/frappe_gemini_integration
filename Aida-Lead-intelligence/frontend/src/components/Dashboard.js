import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner, Badge, Table, Collapse } from 'react-bootstrap';
import axios from 'axios';
import { FiSearch, FiPlus, FiMapPin, FiPhone, FiMail, FiGlobe, FiUsers, FiChevronDown, FiChevronRight, FiStar, FiZap, FiTrendingUp, FiFileText } from 'react-icons/fi';

const Dashboard = () => {
  const [leads, setLeads] = useState([]);
  const [recentLeads, setRecentLeads] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [addingToCrm, setAddingToCrm] = useState({});
  const [expandedLeads, setExpandedLeads] = useState(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const [allLeadsResponse, recentLeadsResponse] = await Promise.all([
        axios.get('/api/leads'),
        axios.get('/api/leads/recent')
      ]);
      
      if (allLeadsResponse.data.success) {
        setLeads(allLeadsResponse.data.leads);
      }
      
      if (recentLeadsResponse.data.success) {
        setRecentLeads(recentLeadsResponse.data.leads);
      }
    } catch (error) {
      console.error('Error fetching leads:', error);
    }
  };

  const handleAddToCrm = async (leadId) => {
    setAddingToCrm(prev => ({ ...prev, [leadId]: true }));
    setError('');
    setSuccess('');

    try {
      const response = await axios.post('/api/add-single-to-crm', {
        lead_id: leadId
      });

      if (response.data.success) {
        setSuccess('Lead successfully added to CRM!');
        fetchLeads(); // Refresh to update the lead status
      } else {
        setError(response.data.message || 'Failed to add lead to CRM');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while adding lead to CRM');
    } finally {
      setAddingToCrm(prev => ({ ...prev, [leadId]: false }));
    }
  };

  const handleAddAllToCrm = async (leadsToAdd = null) => {
    const targetLeads = leadsToAdd || recentLeads;
    const unsyncedLeads = targetLeads.filter(lead => !lead.is_synced);
    if (unsyncedLeads.length === 0) {
      setError('No leads to add to CRM');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post('/api/add-to-crm', {
        lead_ids: unsyncedLeads.map(lead => lead.id)
      });

      if (response.data.success) {
        setSuccess(`Successfully added ${response.data.added_count} leads to CRM!`);
        fetchLeads(); // Refresh to update lead statuses
      } else {
        setError(response.data.message || 'Failed to add leads to CRM');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while adding leads to CRM');
    } finally {
      setLoading(false);
    }
  };

  const formatLeadData = (lead) => {
    return {
      ...lead,
      phone: lead.phone || 'N/A',
      email: lead.email || 'N/A',
      website: lead.website || 'N/A',
      address: lead.address || 'N/A'
    };
  };

  const toggleLeadExpansion = (leadId) => {
    const newExpanded = new Set(expandedLeads);
    if (newExpanded.has(leadId)) {
      newExpanded.delete(leadId);
    } else {
      newExpanded.add(leadId);
    }
    setExpandedLeads(newExpanded);
  };

  const renderLeadRow = (lead) => {
    const formattedLead = formatLeadData(lead);
    const isExpanded = expandedLeads.has(lead.id);
    const isAdding = addingToCrm[lead.id];

    return (
      <React.Fragment key={lead.id}>
        <tr className="lead-row">
          <td>
            <div className="d-flex align-items-center">
              <button
                className="btn btn-link p-0 me-2"
                onClick={() => toggleLeadExpansion(lead.id)}
              >
                {isExpanded ? <FiChevronDown /> : <FiChevronRight />}
              </button>
              <div>
                <div className="fw-bold">{formattedLead.name}</div>
                <small className="text-muted">{formattedLead.industry}</small>
              </div>
            </div>
          </td>
          <td>
            <div className="d-flex align-items-center">
              <FiMapPin className="me-1" />
              {formattedLead.location}
            </div>
          </td>
          <td>
            <div className="d-flex align-items-center">
              <FiPhone className="me-1" />
              {formattedLead.phone}
            </div>
          </td>
          <td>
            <div className="d-flex align-items-center">
              <FiMail className="me-1" />
              {formattedLead.email}
            </div>
          </td>
          <td>
            <div className="d-flex align-items-center">
              <FiGlobe className="me-1" />
              {formattedLead.website}
            </div>
          </td>
          <td>
            {lead.is_synced ? (
              <Badge bg="success">Synced</Badge>
            ) : (
              <Badge bg="warning">Pending</Badge>
            )}
          </td>
          <td>
            <Button
              size="sm"
              variant={lead.is_synced ? "outline-secondary" : "primary"}
              disabled={lead.is_synced || isAdding}
              onClick={() => handleAddToCrm(lead.id)}
            >
              {isAdding ? (
                <>
                  <Spinner animation="border" size="sm" className="me-1" />
                  Adding...
                </>
              ) : (
                <>
                  <FiPlus className="me-1" />
                  {lead.is_synced ? 'Added' : 'Add to CRM'}
                </>
              )}
            </Button>
          </td>
        </tr>
        <tr>
          <td colSpan="7" className="p-0">
            <Collapse in={isExpanded}>
              <div className="p-3 bg-light">
                <Row>
                  <Col md={6}>
                    <h6>Additional Details</h6>
                    <p><strong>Address:</strong> {formattedLead.address}</p>
                    <p><strong>Industry:</strong> {formattedLead.industry}</p>
                    <p><strong>Source:</strong> {formattedLead.source}</p>
                  </Col>
                  <Col md={6}>
                    <h6>Contact Information</h6>
                    <p><strong>Phone:</strong> {formattedLead.phone}</p>
                    <p><strong>Email:</strong> {formattedLead.email}</p>
                    <p><strong>Website:</strong> {formattedLead.website}</p>
                  </Col>
                </Row>
              </div>
            </Collapse>
          </td>
        </tr>
      </React.Fragment>
    );
  };

  return (
    <div className="page-container fade-in">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Overview of your lead intelligence platform</p>
      </div>

      {error && <Alert variant="danger" className="mb-4">{error}</Alert>}
      {success && <Alert variant="success" className="mb-4">{success}</Alert>}

      <Row className="mb-4">
        <Col lg="8">
          <Card className="card">
            <Card.Header className="card-header">
              <Card.Title className="card-title">
                <FiTrendingUp className="me-2" />
                Platform Overview
              </Card.Title>
            </Card.Header>
            <Card.Body className="card-body">
              <Row>
                <Col md="6">
                  <div className="text-center p-3">
                    <FiUsers className="text-primary mb-2" style={{ fontSize: '2rem' }} />
                    <h4>{leads.length}</h4>
                    <p className="text-muted">Total Leads</p>
                  </div>
                </Col>
                <Col md="6">
                  <div className="text-center p-3">
                    <FiMail className="text-success mb-2" style={{ fontSize: '2rem' }} />
                    <h4>{recentLeads.length}</h4>
                    <p className="text-muted">Recent Leads</p>
                  </div>
                </Col>
              </Row>
              <div className="mt-3">
                <h6>Quick Actions</h6>
                <div className="d-flex gap-2 flex-wrap">
                  <Button
                    variant="outline-primary"
                    className="btn btn-outline-primary"
                    onClick={() => window.location.href = '/lead-generation'}
                  >
                    <FiSearch className="me-2" />
                    Generate Leads
                  </Button>
                  <Button
                    variant="outline-success"
                    className="btn btn-outline-success"
                    onClick={() => window.location.href = '/outreach'}
                  >
                    <FiMail className="me-2" />
                    Manage Outreach
                  </Button>
                  <Button
                    variant="outline-info"
                    className="btn btn-outline-info"
                    onClick={() => window.location.href = '/email-templates'}
                  >
                    <FiFileText className="me-2" />
                    Email Templates
                  </Button>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col lg="4">
          <Card className="card">
            <Card.Header className="card-header">
              <Card.Title className="card-title">
                <FiZap className="me-2" />
                Recent Activity
              </Card.Title>
            </Card.Header>
            <Card.Body className="card-body">
              {recentLeads.length === 0 ? (
                <div className="text-center py-3">
                  <FiUsers className="text-muted mb-2" style={{ fontSize: '2rem' }} />
                  <p className="text-muted">No recent leads</p>
                  <Button
                    variant="primary"
                    size="sm"
                    className="btn btn-primary"
                    onClick={() => window.location.href = '/lead-generation'}
                  >
                    Generate Your First Leads
                  </Button>
                </div>
              ) : (
                <div>
                  {recentLeads.slice(0, 5).map((lead) => (
                    <div key={lead.id} className="d-flex justify-content-between align-items-center py-2 border-bottom">
                      <div>
                        <div className="fw-bold">{lead.name || 'Unknown'}</div>
                        <small className="text-muted">{lead.category || 'No category'}</small>
                      </div>
                      <Badge bg={lead.is_synced ? 'success' : 'warning'}>
                        {lead.is_synced ? 'Synced' : 'Pending'}
                      </Badge>
                    </div>
                  ))}
                  {recentLeads.length > 5 && (
                    <div className="text-center mt-2">
                      <Button
                        variant="link"
                        size="sm"
                        className="btn btn-link"
                        onClick={() => window.location.href = '/outreach'}
                      >
                        View All Leads
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Card className="card">
        <Card.Header className="card-header">
          <div className="d-flex justify-content-between align-items-center">
            <Card.Title className="card-title">
              <FiUsers className="me-2" />
              Generated Leads
            </Card.Title>
            {recentLeads.length > 0 && (
              <Button
                variant="success"
                size="sm"
                className="btn btn-success"
                onClick={() => handleAddAllToCrm()}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Adding All...
                  </>
                ) : (
                  <>
                    <FiPlus className="me-2" />
                    Add All to CRM
                  </>
                )}
              </Button>
            )}
          </div>
        </Card.Header>
        <Card.Body className="card-body">
          {leads.length === 0 ? (
            <div className="text-center py-4">
              <FiUsers className="text-muted mb-3" style={{ fontSize: '3rem' }} />
              <h5 className="text-muted">No leads generated yet</h5>
              <p className="text-muted">Use the form above to generate your first leads</p>
            </div>
          ) : (
            <div className="table-responsive">
              <Table className="table">
                <thead>
                  <tr>
                    <th>Name & Industry</th>
                    <th>Location</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Website</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map(renderLeadRow)}
                </tbody>
              </Table>
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
};

export default Dashboard;