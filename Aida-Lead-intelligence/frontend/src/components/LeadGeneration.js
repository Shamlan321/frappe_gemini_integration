import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner, Badge, Table, Collapse } from 'react-bootstrap';
import axios from 'axios';
import { FiSearch, FiPlus, FiMapPin, FiPhone, FiMail, FiGlobe, FiUsers, FiChevronDown, FiChevronRight, FiStar, FiZap, FiTrendingUp, FiLink, FiGrid } from 'react-icons/fi';

const LeadGeneration = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [expandedLeads, setExpandedLeads] = useState(new Set());
  const [selectedSource, setSelectedSource] = useState(null);
  const [scoringLoading, setScoringLoading] = useState(new Set());
  
  // Google Maps form state
  const [gmapsQuery, setGmapsQuery] = useState('');
  
  // Apollo form state
  const [apolloUrl, setApolloUrl] = useState('');
  const [apolloPage, setApolloPage] = useState(1);

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const [leadsResponse, scoredLeadsResponse] = await Promise.all([
        axios.get('/api/leads'),
        axios.get('/api/leads/scored')
      ]);
      
      if (leadsResponse.data.success) {
        const leads = leadsResponse.data.leads;
        
        // Merge scoring data with leads
        if (scoredLeadsResponse.data.success) {
          const scoredLeads = scoredLeadsResponse.data.scored_leads;
          const scoredLeadsMap = {};
          
          scoredLeads.forEach(scoredLead => {
            scoredLeadsMap[scoredLead.lead_id] = {
              score: scoredLead.score,
              status: scoredLead.status,
              factors: scoredLead.factors,
              recommendations: scoredLead.recommendations,
              confidence: scoredLead.confidence,
              reasoning: scoredLead.reasoning,
              scored_at: scoredLead.scored_at
            };
          });
          
          // Merge scoring data with leads
          const leadsWithScoring = leads.map(lead => ({
            ...lead,
            scoring: scoredLeadsMap[lead.id] || null
          }));
          
          setLeads(leadsWithScoring);
        } else {
          setLeads(leads);
        }
      }
    } catch (error) {
      console.error('Error fetching leads:', error);
    }
  };

  const handleGmapsLeadGeneration = async (e) => {
    e.preventDefault();
    if (!gmapsQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post('/api/generate-leads', {
        query: gmapsQuery.trim()
      });

      if (response.data.success) {
        setSuccess(`Successfully generated ${response.data.leads_count} Google Maps leads!`);
        setGmapsQuery('');
        fetchLeads();
      } else {
        setError(response.data.message || 'Failed to generate leads');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while generating leads');
    } finally {
      setLoading(false);
    }
  };

  const handleApolloLeadGeneration = async (e) => {
    e.preventDefault();
    if (!apolloUrl.trim()) {
      setError('Please enter an Apollo URL');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post('/api/generate-apollo-leads', {
        url: apolloUrl.trim(),
        page: apolloPage
      });

      if (response.data.success) {
        setSuccess(`Successfully generated ${response.data.leads_count} Apollo leads!`);
        setApolloUrl('');
        setApolloPage(1);
        fetchLeads();
      } else {
        setError(response.data.message || 'Failed to generate leads');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while generating leads');
    } finally {
      setLoading(false);
    }
  };

  const handleScoreLead = async (leadId) => {
    setScoringLoading(prev => new Set(prev).add(leadId));
    setError('');
    setSuccess('');

    try {
      console.log(`Scoring lead ${leadId}...`);
      
      // Check authentication status first
      const authResponse = await axios.get('/api/user/profile');
      if (!authResponse.data.success) {
        throw new Error('Authentication required. Please log in again.');
      }
      
      const response = await axios.post('/api/leads/score', {
        lead_id: leadId
      });

      console.log('Scoring response:', response.data);

      if (response.data.success) {
        // Check if this was a re-score by looking at the current lead data
        const currentLead = leads.find(l => l.id === leadId);
        const isRescore = currentLead && currentLead.scoring && currentLead.scoring.status !== 'UNSCORED';
        setSuccess(`Lead ${isRescore ? 're-scored' : 'scored'} successfully!`);
        fetchLeads(); // Refresh to get updated scoring data
      } else {
        setError(response.data.message || response.data.error || 'Failed to score lead');
      }
    } catch (error) {
      console.error('Scoring error:', error);
      
      if (error.response?.status === 401) {
        setError('Authentication required. Please log in again.');
        // Redirect to login or refresh auth
        window.location.reload();
      } else {
        setError(error.response?.data?.message || error.response?.data?.error || 'An error occurred while scoring lead');
      }
    } finally {
      setScoringLoading(prev => {
        const newSet = new Set(prev);
        newSet.delete(leadId);
        return newSet;
      });
    }
  };

  const handleBatchScoreLeads = async () => {
    if (leads.length === 0) {
      setError('No leads to score');
      return;
    }

    setScoringLoading(prev => new Set(prev).add('all'));
    setError('');
    setSuccess('');

    try {
      // Check authentication status first
      const authResponse = await axios.get('/api/user/profile');
      if (!authResponse.data.success) {
        throw new Error('Authentication required. Please log in again.');
      }
      
      const leadIds = leads.map(lead => lead.id);
      const response = await axios.post('/api/leads/batch-score', {
        lead_ids: leadIds
      });

      if (response.data.success) {
        setSuccess(`Successfully scored ${response.data.scored_leads.length} leads!`);
        fetchLeads(); // Refresh to get updated scoring data
      } else {
        setError(response.data.message || response.data.error || 'Failed to score leads');
      }
    } catch (error) {
      console.error('Batch scoring error:', error);
      
      if (error.response?.status === 401) {
        setError('Authentication required. Please log in again.');
        // Redirect to login or refresh auth
        window.location.reload();
      } else {
        setError(error.response?.data?.message || error.response?.data?.error || 'An error occurred while scoring leads');
      }
    } finally {
      setScoringLoading(prev => {
        const newSet = new Set(prev);
        newSet.delete('all');
        return newSet;
      });
    }
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
    const isExpanded = expandedLeads.has(lead.id);
    const leadData = lead.data || {};
    
    // Get scoring data if available
    const scoring = lead.scoring || {};
    const score = scoring.score || 0;
    const status = scoring.status || 'UNSCORED';
    
    const getStatusBadge = (status) => {
      const scoringTime = scoring.scored_at ? new Date(scoring.scored_at).toLocaleDateString() : null;
      
      switch (status) {
        case 'HOT':
          return (
            <div>
              <Badge bg="danger">HOT ({score})</Badge>
              {scoringTime && <small className="d-block text-muted">Scored: {scoringTime}</small>}
            </div>
          );
        case 'WARM':
          return (
            <div>
              <Badge bg="warning">WARM ({score})</Badge>
              {scoringTime && <small className="d-block text-muted">Scored: {scoringTime}</small>}
            </div>
          );
        case 'COLD':
          return (
            <div>
              <Badge bg="secondary">COLD ({score})</Badge>
              {scoringTime && <small className="d-block text-muted">Scored: {scoringTime}</small>}
            </div>
          );
        default:
          return <Badge bg="light" text="dark">UNSCORED</Badge>;
      }
    };
    
    return (
      <React.Fragment key={lead.id}>
        <tr className="lead-row">
          <td>
            <div className="d-flex align-items-center">
              <Button
                variant="link"
                size="sm"
                className="p-0 me-2"
                onClick={() => toggleLeadExpansion(lead.id)}
              >
                {isExpanded ? <FiChevronDown /> : <FiChevronRight />}
              </Button>
              <div>
                <div className="fw-bold">{lead.name || leadData.company_name || 'Unknown'}</div>
                <small className="text-muted">
                  {leadData.source || lead.category || 'Unknown source'}
                </small>
              </div>
            </div>
          </td>
          <td>
            {leadData.website ? (
              <a href={leadData.website} target="_blank" rel="noopener noreferrer" className="text-decoration-none">
                <FiGlobe className="me-1" />
                {leadData.website}
              </a>
            ) : (
              <span className="text-muted">No website</span>
            )}
          </td>
          <td>
            {leadData.phone ? (
              <span>
                <FiPhone className="me-1" />
                {leadData.phone}
              </span>
            ) : (
              <span className="text-muted">No phone</span>
            )}
          </td>
          <td>
            {leadData.email ? (
              <span>
                <FiMail className="me-1" />
                {leadData.email}
              </span>
            ) : (
              <span className="text-muted">No email</span>
            )}
          </td>
          <td>
            {leadData.address || lead.address || (
              <span className="text-muted">No address</span>
            )}
          </td>
          <td>
            {getStatusBadge(status)}
          </td>
          <td>
            <div className="d-flex gap-1">
              <Button
                variant={status === 'UNSCORED' ? "outline-primary" : "outline-secondary"}
                size="sm"
                className="btn btn-sm"
                onClick={() => handleScoreLead(lead.id)}
                disabled={scoringLoading.has(lead.id)}
              >
                {scoringLoading.has(lead.id) ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-1" />
                    Scoring...
                  </>
                ) : (
                  <>
                    <FiStar className="me-1" />
                    {status === 'UNSCORED' ? 'Score' : 'Re-score'}
                  </>
                )}
              </Button>
              <small className="text-muted">
                {new Date(lead.created_at).toLocaleDateString()}
              </small>
            </div>
          </td>
        </tr>
        <tr>
          <td colSpan="7" className="p-0">
            <Collapse in={isExpanded}>
              <div className="lead-details p-3 bg-light">
                <Row>
                  <Col md="6">
                    <h6>Basic Information</h6>
                    <div className="mb-2">
                      <strong>Company:</strong> {leadData.company_name || lead.name || 'N/A'}
                    </div>
                    <div className="mb-2">
                      <strong>Category:</strong> {leadData.category || lead.category || 'N/A'}
                    </div>
                    <div className="mb-2">
                      <strong>Description:</strong> {leadData.description || 'N/A'}
                    </div>
                    {leadData.founded_year && (
                      <div className="mb-2">
                        <strong>Founded:</strong> {leadData.founded_year}
                      </div>
                    )}
                    {leadData.employee_count && (
                      <div className="mb-2">
                        <strong>Employees:</strong> {leadData.employee_count}
                      </div>
                    )}
                    {leadData.revenue && (
                      <div className="mb-2">
                        <strong>Revenue:</strong> {leadData.revenue}
                      </div>
                    )}
                  </Col>
                  <Col md="6">
                    <h6>Contact & Social</h6>
                    <div className="mb-2">
                      <strong>Website:</strong> {leadData.website || 'N/A'}
                    </div>
                    <div className="mb-2">
                      <strong>Phone:</strong> {leadData.phone || 'N/A'}
                    </div>
                    <div className="mb-2">
                      <strong>Email:</strong> {leadData.email || 'N/A'}
                    </div>
                    {leadData.linkedin_url && (
                      <div className="mb-2">
                        <strong>LinkedIn:</strong> <a href={leadData.linkedin_url} target="_blank" rel="noopener noreferrer">{leadData.linkedin_url}</a>
                      </div>
                    )}
                    {leadData.twitter_url && (
                      <div className="mb-2">
                        <strong>Twitter:</strong> <a href={leadData.twitter_url} target="_blank" rel="noopener noreferrer">{leadData.twitter_url}</a>
                      </div>
                    )}
                    {leadData.facebook_url && (
                      <div className="mb-2">
                        <strong>Facebook:</strong> <a href={leadData.facebook_url} target="_blank" rel="noopener noreferrer">{leadData.facebook_url}</a>
                      </div>
                    )}
                  </Col>
                </Row>
                
                {/* Scoring Information */}
                {scoring.score && (
                  <Row className="mt-3">
                    <Col md="12">
                      <h6>Lead Scoring Analysis</h6>
                      <div className="mb-2">
                        <strong>Overall Score:</strong> {scoring.score}/100 ({scoring.status})
                      </div>
                      <div className="mb-2">
                        <strong>Confidence:</strong> {scoring.confidence || 'N/A'}
                      </div>
                      {scoring.factors && (
                        <div className="mb-2">
                          <strong>Scoring Factors:</strong>
                          <ul className="mt-1">
                            {Object.entries(scoring.factors).map(([factor, data]) => (
                              <li key={factor}>
                                <strong>{factor.replace('_', ' ').toUpperCase()}:</strong> {data.score} points - {data.details}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {scoring.recommendations && (
                        <div className="mb-2">
                          <strong>Recommendations:</strong> {scoring.recommendations}
                        </div>
                      )}
                      {scoring.reasoning && (
                        <div className="mb-2">
                          <strong>Reasoning:</strong> {scoring.reasoning}
                        </div>
                      )}
                    </Col>
                  </Row>
                )}
                
                {leadData.raw_data && (
                  <div className="mt-3">
                    <h6>Raw Data</h6>
                    <pre className="bg-white p-2 rounded" style={{ fontSize: '0.8rem', maxHeight: '200px', overflow: 'auto' }}>
                      {JSON.stringify(leadData.raw_data, null, 2)}
                    </pre>
                  </div>
                )}
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
        <h1 className="page-title">Lead Generation</h1>
        <p className="page-subtitle">Generate leads from multiple sources including Google Maps and Apollo</p>
      </div>

      {error && <Alert variant="danger" className="alert">{error}</Alert>}
      {success && <Alert variant="success" className="alert">{success}</Alert>}

      <Row className="mb-4">
        <Col md="6">
          <Card className="card h-100">
            <Card.Header className="card-header">
              <Card.Title className="card-title">
                <FiMapPin className="me-2" />
                Google Maps Lead Generation
              </Card.Title>
            </Card.Header>
            <Card.Body className="card-body">
              <Form onSubmit={handleGmapsLeadGeneration}>
                <Form.Group className="form-group">
                  <Form.Label className="form-label">Search Query</Form.Label>
                  <Form.Control
                    type="text"
                    value={gmapsQuery}
                    onChange={(e) => setGmapsQuery(e.target.value)}
                    placeholder="e.g., restaurants in New York, tech companies in San Francisco"
                    className="form-control"
                  />
                  <Form.Text className="text-muted">
                    Describe the type of businesses you want to find
                  </Form.Text>
                </Form.Group>
                <Button
                  type="submit"
                  variant="primary"
                  className="btn btn-primary"
                  disabled={loading || !gmapsQuery.trim()}
                >
                  {loading ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <FiSearch className="me-2" />
                      Generate Google Maps Leads
                    </>
                  )}
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>

        <Col md="6">
          <Card className="card h-100">
            <Card.Header className="card-header">
              <Card.Title className="card-title">
                <FiLink className="me-2" />
                Apollo Lead Generation
              </Card.Title>
            </Card.Header>
            <Card.Body className="card-body">
              <Form onSubmit={handleApolloLeadGeneration}>
                <Form.Group className="form-group">
                  <Form.Label className="form-label">Apollo URL</Form.Label>
                  <Form.Control
                    type="url"
                    value={apolloUrl}
                    onChange={(e) => setApolloUrl(e.target.value)}
                    placeholder="https://app.apollo.io/#/companies?..."
                    className="form-control"
                  />
                  <Form.Text className="text-muted">
                    Paste the Apollo search URL you want to scrape
                  </Form.Text>
                </Form.Group>
                <Form.Group className="form-group">
                  <Form.Label className="form-label">Page Number</Form.Label>
                  <Form.Control
                    type="number"
                    min="1"
                    value={apolloPage}
                    onChange={(e) => setApolloPage(parseInt(e.target.value))}
                    className="form-control"
                  />
                  <Form.Text className="text-muted">
                    Which page of results to scrape (default: 1)
                  </Form.Text>
                </Form.Group>
                <Button
                  type="submit"
                  variant="primary"
                  className="btn btn-primary"
                  disabled={loading || !apolloUrl.trim()}
                >
                  {loading ? (
                    <>
                      <Spinner animation="border" size="sm" className="me-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <FiGrid className="me-2" />
                      Generate Apollo Leads
                    </>
                  )}
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Card className="card">
        <Card.Header className="card-header">
          <div className="d-flex justify-content-between align-items-center">
            <Card.Title className="card-title">
              <FiUsers className="me-2" />
              Generated Leads ({leads.length})
            </Card.Title>
            {leads.length > 0 && (
              <Button
                variant="outline-primary"
                size="sm"
                className="btn btn-outline-primary"
                onClick={handleBatchScoreLeads}
                disabled={scoringLoading.has('all')}
              >
                {scoringLoading.has('all') ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Scoring...
                  </>
                ) : (
                  <>
                    <FiStar className="me-2" />
                    Score All Leads
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
              <p className="text-muted">Use the forms above to generate your first leads</p>
            </div>
          ) : (
            <div className="table-responsive">
              <Table className="table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Website</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Address</th>
                    <th>Score</th>
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

export default LeadGeneration; 