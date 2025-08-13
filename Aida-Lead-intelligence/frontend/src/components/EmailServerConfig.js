import React, { useState, useEffect } from 'react';
import { 
    FiMail, FiServer, FiSettings, FiPlus, FiEdit, FiTrash2, 
    FiPlay, FiEye, FiEyeOff, FiSearch
} from 'react-icons/fi';
import axios from 'axios';

const EmailServerConfig = () => {
    const [configs, setConfigs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showTestModal, setShowTestModal] = useState(false);
    const [selectedConfig, setSelectedConfig] = useState(null);
    const [testResult, setTestResult] = useState(null);
    const [showPassword, setShowPassword] = useState({});
    
    const [newConfig, setNewConfig] = useState({
        name: '',
        smtp_server: '',
        smtp_port: 587,
        sender_email: '',
        sender_password: '',
        sender_name: 'Aida Lead Intelligence',
        use_ssl: false,
        use_tls: true,
        is_active: true
    });
    
    const [testEmail, setTestEmail] = useState({
        to_email: '',
        subject: '',
        content: ''
    });

    useEffect(() => {
        loadConfigs();
    }, []);

    const loadConfigs = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/email/servers');
            if (response.data.success) {
                setConfigs(response.data.configs);
            }
        } catch (error) {
            console.error('Error loading email server configs:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateConfig = async () => {
        try {
            setLoading(true);
            const response = await axios.post('/api/email/servers', newConfig);
            if (response.data.success) {
                setShowCreateModal(false);
                setNewConfig({
                    name: '',
                    smtp_server: '',
                    smtp_port: 587,
                    sender_email: '',
                    sender_password: '',
                    sender_name: 'Aida Lead Intelligence',
                    use_ssl: false,
                    use_tls: true,
                    is_active: true
                });
                loadConfigs();
            }
        } catch (error) {
            console.error('Error creating email server config:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateConfig = async () => {
        try {
            setLoading(true);
            const response = await axios.put(`/api/email/servers/${selectedConfig.id}`, selectedConfig);
            if (response.data.success) {
                setShowEditModal(false);
                setSelectedConfig(null);
                loadConfigs();
            }
        } catch (error) {
            console.error('Error updating email server config:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteConfig = async (configId) => {
        if (window.confirm('Are you sure you want to delete this email server configuration?')) {
            try {
                setLoading(true);
                const response = await axios.delete(`/api/email/servers/${configId}`);
                if (response.data.success) {
                    loadConfigs();
                }
            } catch (error) {
                console.error('Error deleting email server config:', error);
            } finally {
                setLoading(false);
            }
        }
    };

    const handleTestConnection = async (configId) => {
        try {
            setLoading(true);
            const response = await axios.post(`/api/email/servers/${configId}/test-connection`);
            setTestResult(response.data);
        } catch (error) {
            setTestResult({
                success: false,
                message: error.response?.data?.message || 'Connection test failed'
            });
        } finally {
            setLoading(false);
        }
    };

    const handleSendTestEmail = async () => {
        try {
            setLoading(true);
            const response = await axios.post(`/api/email/servers/${selectedConfig.id}/test-email`, testEmail);
            setTestResult(response.data);
        } catch (error) {
            setTestResult({
                success: false,
                message: error.response?.data?.message || 'Failed to send test email'
            });
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (isActive) => {
        return isActive ? 'success' : 'secondary';
    };

    const getConnectionType = (config) => {
        if (config.use_ssl) return 'SSL';
        if (config.use_tls) return 'TLS';
        return 'None';
    };

    const togglePasswordVisibility = (configId) => {
        setShowPassword(prev => ({
            ...prev,
            [configId]: !prev[configId]
        }));
    };

    return (
        <div className="page-container fade-in">
            <div className="page-header">
                <h1 className="page-title">Email Servers</h1>
                <p className="page-subtitle">Configure SMTP servers for sending tracked emails</p>
            </div>

            <div className="row mb-4">
                <div className="col-12">
                    <div className="card">
                        <div className="card-header">
                            <div className="d-flex justify-content-between align-items-center">
                                <h5 className="card-title mb-0">
                                    <FiServer className="me-2" />
                                    Email Server Configurations
                                </h5>
                                <button 
                                    className="btn btn-primary btn-sm"
                                    onClick={() => setShowCreateModal(true)}
                                >
                                    <FiPlus className="me-1" />
                                    Add Server
                                </button>
                            </div>
                        </div>
                        <div className="card-body">
                            {loading ? (
                                <div className="text-center py-4">
                                    <div className="spinner-border" role="status">
                                        <span className="visually-hidden">Loading...</span>
                                    </div>
                                    <p className="mt-2 text-muted">Loading configurations...</p>
                                </div>
                            ) : configs.length === 0 ? (
                                <div className="text-center py-4">
                                    <FiServer className="text-muted mb-3" style={{ fontSize: '3rem' }} />
                                    <h5 className="text-muted">No email servers configured</h5>
                                    <p className="text-muted">Add your first SMTP server to start sending emails</p>
                                </div>
                            ) : (
                                <div className="table-responsive">
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <th>Server Name</th>
                                                <th>SMTP Server</th>
                                                <th>Port</th>
                                                <th>Security</th>
                                                <th>Status</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {configs.map(config => (
                                                <tr key={config.id}>
                                                    <td>
                                                        <div className="fw-bold">{config.name}</div>
                                                        <small className="text-muted">{config.sender_email}</small>
                                                    </td>
                                                    <td>{config.smtp_server}</td>
                                                    <td>{config.smtp_port}</td>
                                                    <td>
                                                        <span className="badge bg-info">
                                                            {getConnectionType(config)}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <span className={`badge bg-${getStatusColor(config.is_active)}`}>
                                                            {config.is_active ? 'Active' : 'Inactive'}
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <div className="btn-group btn-group-sm">
                                                            <button 
                                                                className="btn btn-outline-primary"
                                                                onClick={() => {
                                                                    setSelectedConfig(config);
                                                                    setShowEditModal(true);
                                                                }}
                                                            >
                                                                <FiEdit />
                                                            </button>
                                                            <button 
                                                                className="btn btn-outline-success"
                                                                onClick={() => handleTestConnection(config.id)}
                                                            >
                                                                <FiPlay />
                                                            </button>
                                                            <button 
                                                                className="btn btn-outline-info"
                                                                onClick={() => {
                                                                    setSelectedConfig(config);
                                                                    setShowTestModal(true);
                                                                }}
                                                            >
                                                                <FiMail />
                                                            </button>
                                                            <button 
                                                                className="btn btn-outline-danger"
                                                                onClick={() => handleDeleteConfig(config.id)}
                                                            >
                                                                <FiTrash2 />
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {testResult && (
                <div className="row mb-4">
                    <div className="col-12">
                        <div className={`alert alert-${testResult.success ? 'success' : 'danger'}`}>
                            <div className="d-flex align-items-center">
                                {testResult.success ? <FiPlay className="me-2" /> : <FiSearch className="me-2" />}
                                {testResult.message}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Create Configuration Modal */}
            {showCreateModal && (
                <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog modal-lg">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">
                                    <FiPlus className="me-2" />
                                    Add Email Server
                                </h5>
                                <button 
                                    type="button" 
                                    className="btn-close"
                                    onClick={() => setShowCreateModal(false)}
                                ></button>
                            </div>
                            <div className="modal-body">
                                <div className="row">
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">Configuration Name</label>
                                            <input 
                                                type="text" 
                                                className="form-control"
                                                value={newConfig.name}
                                                onChange={(e) => setNewConfig(prev => ({ ...prev, name: e.target.value }))}
                                                placeholder="e.g., Gmail SMTP"
                                            />
                                        </div>
                                    </div>
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">SMTP Server</label>
                                            <input 
                                                type="text" 
                                                className="form-control"
                                                value={newConfig.smtp_server}
                                                onChange={(e) => setNewConfig(prev => ({ ...prev, smtp_server: e.target.value }))}
                                                placeholder="e.g., smtp.gmail.com"
                                            />
                                        </div>
                                    </div>
                                </div>
                                <div className="row">
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">SMTP Port</label>
                                            <input 
                                                type="number" 
                                                className="form-control"
                                                value={newConfig.smtp_port}
                                                onChange={(e) => setNewConfig(prev => ({ ...prev, smtp_port: parseInt(e.target.value) }))}
                                                placeholder="587"
                                            />
                                        </div>
                                    </div>
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">Sender Email</label>
                                            <input 
                                                type="email" 
                                                className="form-control"
                                                value={newConfig.sender_email}
                                                onChange={(e) => setNewConfig(prev => ({ ...prev, sender_email: e.target.value }))}
                                                placeholder="your-email@gmail.com"
                                            />
                                        </div>
                                    </div>
                                </div>
                                <div className="row">
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">Sender Password</label>
                                            <div className="input-group">
                                                <input 
                                                    type={showPassword.create ? "text" : "password"}
                                                    className="form-control"
                                                    value={newConfig.sender_password}
                                                    onChange={(e) => setNewConfig(prev => ({ ...prev, sender_password: e.target.value }))}
                                                    placeholder="Enter password or app password"
                                                />
                                                <button 
                                                    className="btn btn-outline-secondary"
                                                    type="button"
                                                    onClick={() => setShowPassword(prev => ({ ...prev, create: !prev.create }))}
                                                >
                                                    {showPassword.create ? <FiEyeOff /> : <FiEye />}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">Sender Name</label>
                                            <input 
                                                type="text" 
                                                className="form-control"
                                                value={newConfig.sender_name}
                                                onChange={(e) => setNewConfig(prev => ({ ...prev, sender_name: e.target.value }))}
                                                placeholder="Your Name"
                                            />
                                        </div>
                                    </div>
                                </div>
                                <div className="row">
                                    <div className="col-md-6">
                                        <div className="form-check">
                                            <input 
                                                type="checkbox" 
                                                className="form-check-input"
                                                checked={newConfig.use_ssl}
                                                onChange={(e) => setNewConfig(prev => ({ ...prev, use_ssl: e.target.checked }))}
                                            />
                                            <label className="form-check-label">Use SSL</label>
                                        </div>
                                    </div>
                                    <div className="col-md-6">
                                        <div className="form-check">
                                            <input 
                                                type="checkbox" 
                                                className="form-check-input"
                                                checked={newConfig.use_tls}
                                                onChange={(e) => setNewConfig(prev => ({ ...prev, use_tls: e.target.checked }))}
                                            />
                                            <label className="form-check-label">Use TLS</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button 
                                    type="button" 
                                    className="btn btn-secondary"
                                    onClick={() => setShowCreateModal(false)}
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="button" 
                                    className="btn btn-primary"
                                    onClick={handleCreateConfig}
                                    disabled={loading || !newConfig.name || !newConfig.smtp_server || !newConfig.sender_email}
                                >
                                    {loading ? 'Creating...' : 'Create Configuration'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit Configuration Modal */}
            {showEditModal && selectedConfig && (
                <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog modal-lg">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">
                                    <FiEdit className="me-2" />
                                    Edit Email Server
                                </h5>
                                <button 
                                    type="button" 
                                    className="btn-close"
                                    onClick={() => setShowEditModal(false)}
                                ></button>
                            </div>
                            <div className="modal-body">
                                <div className="row">
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">Configuration Name</label>
                                            <input 
                                                type="text" 
                                                className="form-control"
                                                value={selectedConfig.name}
                                                onChange={(e) => setSelectedConfig(prev => ({ ...prev, name: e.target.value }))}
                                            />
                                        </div>
                                    </div>
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">SMTP Server</label>
                                            <input 
                                                type="text" 
                                                className="form-control"
                                                value={selectedConfig.smtp_server}
                                                onChange={(e) => setSelectedConfig(prev => ({ ...prev, smtp_server: e.target.value }))}
                                            />
                                        </div>
                                    </div>
                                </div>
                                <div className="row">
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">SMTP Port</label>
                                            <input 
                                                type="number" 
                                                className="form-control"
                                                value={selectedConfig.smtp_port}
                                                onChange={(e) => setSelectedConfig(prev => ({ ...prev, smtp_port: parseInt(e.target.value) }))}
                                            />
                                        </div>
                                    </div>
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">Sender Email</label>
                                            <input 
                                                type="email" 
                                                className="form-control"
                                                value={selectedConfig.sender_email}
                                                onChange={(e) => setSelectedConfig(prev => ({ ...prev, sender_email: e.target.value }))}
                                            />
                                        </div>
                                    </div>
                                </div>
                                <div className="row">
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">Sender Password</label>
                                            <div className="input-group">
                                                <input 
                                                    type={showPassword.edit ? "text" : "password"}
                                                    className="form-control"
                                                    value={selectedConfig.sender_password}
                                                    onChange={(e) => setSelectedConfig(prev => ({ ...prev, sender_password: e.target.value }))}
                                                    placeholder="Enter new password (leave blank to keep current)"
                                                />
                                                <button 
                                                    className="btn btn-outline-secondary"
                                                    type="button"
                                                    onClick={() => setShowPassword(prev => ({ ...prev, edit: !prev.edit }))}
                                                >
                                                    {showPassword.edit ? <FiEyeOff /> : <FiEye />}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="col-md-6">
                                        <div className="form-group">
                                            <label className="form-label">Sender Name</label>
                                            <input 
                                                type="text" 
                                                className="form-control"
                                                value={selectedConfig.sender_name}
                                                onChange={(e) => setSelectedConfig(prev => ({ ...prev, sender_name: e.target.value }))}
                                            />
                                        </div>
                                    </div>
                                </div>
                                <div className="row">
                                    <div className="col-md-4">
                                        <div className="form-check">
                                            <input 
                                                type="checkbox" 
                                                className="form-check-input"
                                                checked={selectedConfig.use_ssl}
                                                onChange={(e) => setSelectedConfig(prev => ({ ...prev, use_ssl: e.target.checked }))}
                                            />
                                            <label className="form-check-label">Use SSL</label>
                                        </div>
                                    </div>
                                    <div className="col-md-4">
                                        <div className="form-check">
                                            <input 
                                                type="checkbox" 
                                                className="form-check-input"
                                                checked={selectedConfig.use_tls}
                                                onChange={(e) => setSelectedConfig(prev => ({ ...prev, use_tls: e.target.checked }))}
                                            />
                                            <label className="form-check-label">Use TLS</label>
                                        </div>
                                    </div>
                                    <div className="col-md-4">
                                        <div className="form-check">
                                            <input 
                                                type="checkbox" 
                                                className="form-check-input"
                                                checked={selectedConfig.is_active}
                                                onChange={(e) => setSelectedConfig(prev => ({ ...prev, is_active: e.target.checked }))}
                                            />
                                            <label className="form-check-label">Active</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button 
                                    type="button" 
                                    className="btn btn-secondary"
                                    onClick={() => setShowEditModal(false)}
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="button" 
                                    className="btn btn-primary"
                                    onClick={handleUpdateConfig}
                                    disabled={loading}
                                >
                                    {loading ? 'Updating...' : 'Update Configuration'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Test Email Modal */}
            {showTestModal && selectedConfig && (
                <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">
                                    <FiMail className="me-2" />
                                    Send Test Email
                                </h5>
                                <button 
                                    type="button" 
                                    className="btn-close"
                                    onClick={() => setShowTestModal(false)}
                                ></button>
                            </div>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">To Email</label>
                                    <input 
                                        type="email" 
                                        className="form-control"
                                        value={testEmail.to_email}
                                        onChange={(e) => setTestEmail(prev => ({ ...prev, to_email: e.target.value }))}
                                        placeholder="recipient@example.com"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Subject</label>
                                    <input 
                                        type="text" 
                                        className="form-control"
                                        value={testEmail.subject}
                                        onChange={(e) => setTestEmail(prev => ({ ...prev, subject: e.target.value }))}
                                        placeholder="Test Email Subject"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Content</label>
                                    <textarea 
                                        className="form-control"
                                        value={testEmail.content}
                                        onChange={(e) => setTestEmail(prev => ({ ...prev, content: e.target.value }))}
                                        placeholder="Test email content..."
                                        rows="4"
                                    ></textarea>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button 
                                    type="button" 
                                    className="btn btn-secondary"
                                    onClick={() => setShowTestModal(false)}
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="button" 
                                    className="btn btn-primary"
                                    onClick={handleSendTestEmail}
                                    disabled={loading || !testEmail.to_email}
                                >
                                    {loading ? 'Sending...' : 'Send Test Email'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EmailServerConfig; 