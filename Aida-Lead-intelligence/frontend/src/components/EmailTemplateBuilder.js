import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner, Badge, Modal, Table } from 'react-bootstrap';
import axios from 'axios';
import { FiPlus, FiEdit, FiTrash2, FiEye, FiSave, FiX, FiMail, FiTag, FiFileText, FiPlay } from 'react-icons/fi';

const EmailTemplateBuilder = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Template form state
  const [showModal, setShowModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [templateForm, setTemplateForm] = useState({
    name: '',
    subject: '',
    content: '',
    category: 'General',
    variables: {}
  });
  
  // Test template state
  const [showTestModal, setShowTestModal] = useState(false);
  const [testingTemplate, setTestingTemplate] = useState(null);
  const [testData, setTestData] = useState({});
  const [processedTemplate, setProcessedTemplate] = useState(null);

  // Available variables for templates
  const availableVariables = [
    { key: 'company_name', label: 'Company Name', example: 'Acme Corp' },
    { key: 'contact_name', label: 'Contact Name', example: 'John Doe' },
    { key: 'contact_first_name', label: 'First Name', example: 'John' },
    { key: 'contact_last_name', label: 'Last Name', example: 'Doe' },
    { key: 'industry', label: 'Industry', example: 'Technology' },
    { key: 'location', label: 'Location', example: 'San Francisco, CA' },
    { key: 'website', label: 'Website', example: 'www.acmecorp.com' },
    { key: 'phone', label: 'Phone', example: '+1-555-0123' },
    { key: 'email', label: 'Email', example: 'john@acmecorp.com' },
    { key: 'lead_score', label: 'Lead Score', example: '85' },
    { key: 'lead_status', label: 'Lead Status', example: 'Hot' }
  ];

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/email/templates');
      
      if (response.data.success) {
        setTemplates(response.data.templates);
      } else {
        setError(response.data.message || 'Failed to fetch templates');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while fetching templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setEditingTemplate(null);
    setTemplateForm({
      name: '',
      subject: '',
      content: '',
      category: 'General',
      variables: {}
    });
    setShowModal(true);
  };

  const handleEditTemplate = (template) => {
    setEditingTemplate(template);
    setTemplateForm({
      name: template.name,
      subject: template.subject || '',
      content: template.content,
      category: template.category || 'General',
      variables: template.variables || {}
    });
    setShowModal(true);
  };

  const handleSaveTemplate = async () => {
    if (!templateForm.name.trim() || !templateForm.content.trim()) {
      setError('Template name and content are required');
      return;
    }

    try {
      setSaving(true);
      setError('');
      setSuccess('');

      const url = editingTemplate 
        ? `/api/email/templates/${editingTemplate.id}`
        : '/api/email/templates';
      
      const method = editingTemplate ? 'put' : 'post';
      
      const response = await axios[method](url, templateForm);
      
      if (response.data.success) {
        setSuccess(editingTemplate ? 'Template updated successfully!' : 'Template created successfully!');
        setShowModal(false);
        fetchTemplates();
      } else {
        setError(response.data.message || 'Failed to save template');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while saving template');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      setLoading(true);
      const response = await axios.delete(`/api/email/templates/${templateId}`);
      
      if (response.data.success) {
        setSuccess('Template deleted successfully!');
        fetchTemplates();
      } else {
        setError(response.data.message || 'Failed to delete template');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while deleting template');
    } finally {
      setLoading(false);
    }
  };

  const handleTestTemplate = async (template) => {
    setTestingTemplate(template);
    setTestData({});
    setProcessedTemplate(null);
    setShowTestModal(true);
  };

  const processTestTemplate = async () => {
    try {
      const response = await axios.post(`/api/email/templates/${testingTemplate.id}/test`, {
        test_data: testData
      });
      
      if (response.data.success) {
        setProcessedTemplate(response.data.processed_template);
      } else {
        setError(response.data.message || 'Failed to process template');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'An error occurred while processing template');
    }
  };

  const insertVariable = (variable) => {
    const textarea = document.getElementById('template-content');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const before = text.substring(0, start);
    const after = text.substring(end, text.length);
    
    const newText = before + `{{${variable.key}}} ` + after;
    setTemplateForm(prev => ({ ...prev, content: newText }));
    
    // Set cursor position after the inserted variable
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + variable.key.length + 4, start + variable.key.length + 4);
    }, 0);
  };

  const getCategoryBadge = (category) => {
    const colors = {
      'General': 'primary',
      'Follow-up': 'success',
      'Introduction': 'info',
      'Promotional': 'warning',
      'Custom': 'secondary'
    };
    return <Badge bg={colors[category] || 'secondary'}>{category}</Badge>;
  };

  return (
    <div className="page-container fade-in">
      <div className="page-header">
        <h1 className="page-title">Email Templates</h1>
        <p className="page-subtitle">Create and manage email templates for your outreach campaigns</p>
      </div>

      {error && <Alert variant="danger" className="alert">{error}</Alert>}
      {success && <Alert variant="success" className="alert">{success}</Alert>}

      <div className="row mb-4">
        <div className="col-12">
          <Card className="card">
            <Card.Header className="card-header">
              <div className="d-flex justify-content-between align-items-center">
                <Card.Title className="card-title">
                  <FiFileText className="me-2" />
                  Email Templates
                </Card.Title>
                <Button
                  variant="primary"
                  className="btn btn-primary"
                  onClick={handleCreateTemplate}
                >
                  <FiPlus className="me-2" />
                  Create Template
                </Button>
              </div>
            </Card.Header>
            <Card.Body className="card-body">
              {loading ? (
                <div className="text-center py-4">
                  <Spinner animation="border" />
                  <p className="mt-2 text-muted">Loading templates...</p>
                </div>
              ) : templates.length === 0 ? (
                <div className="text-center py-4">
                  <FiFileText className="text-muted mb-3" style={{ fontSize: '3rem' }} />
                  <h5 className="text-muted">No templates created yet</h5>
                  <p className="text-muted">Create your first email template to get started</p>
                </div>
              ) : (
                <div className="table-responsive">
                  <Table className="table">
                    <thead>
                      <tr>
                        <th>Template Name</th>
                        <th>Category</th>
                        <th>Subject</th>
                        <th>Created</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {templates.map((template) => (
                        <tr key={template.id}>
                          <td>
                            <div className="fw-bold">{template.name}</div>
                            <small className="text-muted">
                              {template.content.length > 100 
                                ? template.content.substring(0, 100) + '...' 
                                : template.content
                              }
                            </small>
                          </td>
                          <td>{getCategoryBadge(template.category)}</td>
                          <td>{template.subject || 'No subject'}</td>
                          <td>
                            <small className="text-muted">
                              {new Date(template.created_at).toLocaleDateString()}
                            </small>
                          </td>
                          <td>
                            <div className="d-flex gap-1">
                              <Button
                                size="sm"
                                variant="outline-primary"
                                className="btn btn-sm"
                                onClick={() => handleEditTemplate(template)}
                              >
                                <FiEdit />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline-info"
                                className="btn btn-sm"
                                onClick={() => handleTestTemplate(template)}
                              >
                                <FiPlay />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline-danger"
                                className="btn btn-sm"
                                onClick={() => handleDeleteTemplate(template.id)}
                              >
                                <FiTrash2 />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>

      {/* Template Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            <FiMail className="me-2" />
            {editingTemplate ? 'Edit Template' : 'Create Template'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="form-group">
              <Form.Label className="form-label">Template Name</Form.Label>
              <Form.Control
                type="text"
                value={templateForm.name}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter template name"
                className="form-control"
              />
            </Form.Group>

            <Form.Group className="form-group">
              <Form.Label className="form-label">Category</Form.Label>
              <Form.Select
                value={templateForm.category}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, category: e.target.value }))}
                className="form-control"
              >
                <option value="General">General</option>
                <option value="Follow-up">Follow-up</option>
                <option value="Introduction">Introduction</option>
                <option value="Promotional">Promotional</option>
                <option value="Custom">Custom</option>
              </Form.Select>
            </Form.Group>

            <Form.Group className="form-group">
              <Form.Label className="form-label">Subject Line</Form.Label>
              <Form.Control
                type="text"
                value={templateForm.subject}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, subject: e.target.value }))}
                placeholder="Enter email subject"
                className="form-control"
              />
            </Form.Group>

            <Form.Group className="form-group">
              <Form.Label className="form-label">
                Content
                <small className="text-muted ms-2">Use variables like {'{company_name}'} to personalize</small>
              </Form.Label>
              <Form.Control
                as="textarea"
                rows={8}
                value={templateForm.content}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, content: e.target.value }))}
                placeholder="Enter your email content here..."
                className="form-control"
                id="template-content"
              />
            </Form.Group>

            <div className="mb-3">
              <Form.Label className="form-label">
                <FiTag className="me-2" />
                Available Variables
              </Form.Label>
              <div className="d-flex flex-wrap gap-1">
                {availableVariables.map((variable) => (
                  <Button
                    key={variable.key}
                    size="sm"
                    variant="outline-secondary"
                    className="btn btn-sm"
                    onClick={() => insertVariable(variable)}
                    title={`${variable.label}: ${variable.example}`}
                  >
                    {variable.label}
                  </Button>
                ))}
              </div>
            </div>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            className="btn btn-primary"
            onClick={handleSaveTemplate}
            disabled={saving}
          >
            {saving ? (
              <>
                <Spinner animation="border" size="sm" className="me-2" />
                Saving...
              </>
            ) : (
              <>
                <FiSave className="me-2" />
                {editingTemplate ? 'Update Template' : 'Create Template'}
              </>
            )}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Test Template Modal */}
      <Modal show={showTestModal} onHide={() => setShowTestModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            <FiPlay className="me-2" />
            Test Template: {testingTemplate?.name}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {testingTemplate && (
            <div className="row">
              <div className="col-md-6">
                <h6>Test Data</h6>
                <Form>
                  {availableVariables.map((variable) => (
                    <Form.Group key={variable.key} className="form-group">
                      <Form.Label className="form-label">{variable.label}</Form.Label>
                      <Form.Control
                        type="text"
                        value={testData[variable.key] || ''}
                        onChange={(e) => setTestData(prev => ({ ...prev, [variable.key]: e.target.value }))}
                        placeholder={variable.example}
                        className="form-control"
                      />
                    </Form.Group>
                  ))}
                  <Button
                    variant="primary"
                    className="btn btn-primary"
                    onClick={processTestTemplate}
                  >
                    <FiPlay className="me-2" />
                    Process Template
                  </Button>
                </Form>
              </div>
              <div className="col-md-6">
                <h6>Preview</h6>
                {processedTemplate ? (
                  <div className="border rounded p-3 bg-light">
                    <div className="mb-2">
                      <strong>Subject:</strong> {processedTemplate.subject}
                    </div>
                    <div>
                      <strong>Content:</strong>
                      <div className="mt-2" dangerouslySetInnerHTML={{ __html: processedTemplate.content }} />
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted">
                    <FiEye className="mb-2" style={{ fontSize: '2rem' }} />
                    <p>Fill in test data and click "Process Template" to see preview</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default EmailTemplateBuilder; 