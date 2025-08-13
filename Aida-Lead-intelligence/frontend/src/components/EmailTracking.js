import React, { useState, useEffect } from 'react';
import { 
    FiMail, FiBarChart2, FiTrendingUp, FiClock, 
    FiEye, FiMousePointer, FiMessageSquare,
    FiPlay, FiPause, FiEdit, FiTrash2, FiPlus,
    FiFilter, FiDownload, FiActivity
} from 'react-icons/fi';
import axios from 'axios';

const EmailTracking = () => {
    const [activeTab, setActiveTab] = useState('overview');
    const [analytics, setAnalytics] = useState({});
    const [campaigns, setCampaigns] = useState([]);
    const [sequences, setSequences] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showCreateCampaign, setShowCreateCampaign] = useState(false);
    const [showCreateSequence, setShowCreateSequence] = useState(false);
    const [newCampaign, setNewCampaign] = useState({ name: '', description: '' });
    const [newSequence, setNewSequence] = useState({ 
        name: '', 
        description: '', 
        steps: [],
        triggers: {}
    });

    useEffect(() => {
        loadAnalytics();
        loadCampaigns();
        loadSequences();
    }, []);

    const loadAnalytics = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/email/analytics');
            if (response.data.success) {
                setAnalytics(response.data.analytics);
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadCampaigns = async () => {
        try {
            const response = await axios.get('/api/email/campaigns');
            if (response.data.success) {
                setCampaigns(response.data.campaigns);
            }
        } catch (error) {
            console.error('Error loading campaigns:', error);
        }
    };

    const loadSequences = async () => {
        try {
            const response = await axios.get('/api/email/sequences');
            if (response.data.success) {
                setSequences(response.data.sequences);
            }
        } catch (error) {
            console.error('Error loading sequences:', error);
        }
    };

    const createCampaign = async () => {
        try {
            setLoading(true);
            const response = await axios.post('/api/email/campaigns', newCampaign);
            if (response.data.success) {
                setShowCreateCampaign(false);
                setNewCampaign({ name: '', description: '' });
                loadCampaigns();
            }
        } catch (error) {
            console.error('Error creating campaign:', error);
        } finally {
            setLoading(false);
        }
    };

    const createSequence = async () => {
        try {
            setLoading(true);
            const response = await axios.post('/api/email/sequences', newSequence);
            if (response.data.success) {
                setShowCreateSequence(false);
                setNewSequence({ name: '', description: '', steps: [], triggers: {} });
                loadSequences();
            }
        } catch (error) {
            console.error('Error creating sequence:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatPercentage = (value) => {
        return value ? `${Math.round(value * 100)}%` : '0%';
    };

    const formatNumber = (value) => {
        return value ? value.toLocaleString() : '0';
    };

    const getStatusColor = (status) => {
        const colors = {
            'active': 'success',
            'paused': 'warning',
            'completed': 'info',
            'draft': 'secondary'
        };
        return colors[status] || 'secondary';
    };

    const renderOverview = () => (
        <div className="row">
            <div className="col-md-3 mb-4">
                <div className="card">
                    <div className="card-body text-center">
                        <FiEye className="text-primary mb-2" style={{ fontSize: '2rem' }} />
                        <h3 className="text-primary">{formatNumber(analytics.total_opens || 0)}</h3>
                        <p className="text-muted mb-0">Total Opens</p>
                    </div>
                </div>
            </div>
            <div className="col-md-3 mb-4">
                <div className="card">
                    <div className="card-body text-center">
                        <FiMousePointer className="text-success mb-2" style={{ fontSize: '2rem' }} />
                        <h3 className="text-success">{formatNumber(analytics.total_clicks || 0)}</h3>
                        <p className="text-muted mb-0">Total Clicks</p>
                    </div>
                </div>
            </div>
            <div className="col-md-3 mb-4">
                <div className="card">
                    <div className="card-body text-center">
                        <FiMessageSquare className="text-info mb-2" style={{ fontSize: '2rem' }} />
                        <h3 className="text-info">{formatNumber(analytics.total_replies || 0)}</h3>
                        <p className="text-muted mb-0">Total Replies</p>
                    </div>
                </div>
            </div>
            <div className="col-md-3 mb-4">
                <div className="card">
                    <div className="card-body text-center">
                        <FiTrendingUp className="text-warning mb-2" style={{ fontSize: '2rem' }} />
                        <h3 className="text-warning">{formatPercentage(analytics.open_rate || 0)}</h3>
                        <p className="text-muted mb-0">Open Rate</p>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderCampaigns = () => (
        <div className="row">
            <div className="col-12">
                <div className="card">
                    <div className="card-header">
                        <div className="d-flex justify-content-between align-items-center">
                            <h5 className="card-title mb-0">
                                <FiMail className="me-2" />
                                Email Campaigns
                            </h5>
                            <button 
                                className="btn btn-primary btn-sm"
                                onClick={() => setShowCreateCampaign(true)}
                            >
                                <FiPlus className="me-1" />
                                Create Campaign
                            </button>
                        </div>
                    </div>
                    <div className="card-body">
                        {campaigns.length === 0 ? (
                            <div className="text-center py-4">
                                <FiMail className="text-muted mb-3" style={{ fontSize: '3rem' }} />
                                <h5 className="text-muted">No campaigns created yet</h5>
                                <p className="text-muted">Create your first email campaign to get started</p>
                            </div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Campaign Name</th>
                                            <th>Status</th>
                                            <th>Sent</th>
                                            <th>Opens</th>
                                            <th>Clicks</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {campaigns.map(campaign => (
                                            <tr key={campaign.id}>
                                                <td>
                                                    <div className="fw-bold">{campaign.name}</div>
                                                    <small className="text-muted">{campaign.description}</small>
                                                </td>
                                                <td>
                                                    <span className={`badge bg-${getStatusColor(campaign.status)}`}>
                                                        {campaign.status}
                                                    </span>
                                                </td>
                                                <td>{formatNumber(campaign.sent_count || 0)}</td>
                                                <td>{formatNumber(campaign.open_count || 0)}</td>
                                                <td>{formatNumber(campaign.click_count || 0)}</td>
                                                <td>
                                                    <div className="btn-group btn-group-sm">
                                                        <button className="btn btn-outline-primary">
                                                            <FiEdit />
                                                        </button>
                                                        <button className="btn btn-outline-success">
                                                            <FiPlay />
                                                        </button>
                                                        <button className="btn btn-outline-danger">
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
    );

    const renderSequences = () => (
        <div className="row">
            <div className="col-12">
                <div className="card">
                    <div className="card-header">
                        <div className="d-flex justify-content-between align-items-center">
                            <h5 className="card-title mb-0">
                                <FiActivity className="me-2" />
                                Email Sequences
                            </h5>
                            <button 
                                className="btn btn-primary btn-sm"
                                onClick={() => setShowCreateSequence(true)}
                            >
                                <FiPlus className="me-1" />
                                Create Sequence
                            </button>
                        </div>
                    </div>
                    <div className="card-body">
                        {sequences.length === 0 ? (
                            <div className="text-center py-4">
                                <FiActivity className="text-muted mb-3" style={{ fontSize: '3rem' }} />
                                <h5 className="text-muted">No sequences created yet</h5>
                                <p className="text-muted">Create your first email sequence to get started</p>
                            </div>
                        ) : (
                            <div className="table-responsive">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Sequence Name</th>
                                            <th>Status</th>
                                            <th>Steps</th>
                                            <th>Active</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sequences.map(sequence => (
                                            <tr key={sequence.id}>
                                                <td>
                                                    <div className="fw-bold">{sequence.name}</div>
                                                    <small className="text-muted">{sequence.description}</small>
                                                </td>
                                                <td>
                                                    <span className={`badge bg-${getStatusColor(sequence.status)}`}>
                                                        {sequence.status}
                                                    </span>
                                                </td>
                                                <td>{sequence.steps?.length || 0} steps</td>
                                                <td>{formatNumber(sequence.active_count || 0)}</td>
                                                <td>
                                                    <div className="btn-group btn-group-sm">
                                                        <button className="btn btn-outline-primary">
                                                            <FiEdit />
                                                        </button>
                                                        <button className="btn btn-outline-success">
                                                            <FiPlay />
                                                        </button>
                                                        <button className="btn btn-outline-danger">
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
    );

    return (
        <div className="page-container fade-in">
            <div className="page-header">
                <h1 className="page-title">Email Tracking</h1>
                <p className="page-subtitle">Monitor and analyze your email campaign performance</p>
            </div>

            <div className="row mb-4">
                <div className="col-12">
                    <div className="card">
                        <div className="card-header">
                            <ul className="nav nav-tabs card-header-tabs">
                                <li className="nav-item">
                                    <button 
                                        className={`nav-link ${activeTab === 'overview' ? 'active' : ''}`}
                                        onClick={() => setActiveTab('overview')}
                                    >
                                        <FiBarChart2 className="me-2" />
                                        Overview
                                    </button>
                                </li>
                                <li className="nav-item">
                                    <button 
                                        className={`nav-link ${activeTab === 'campaigns' ? 'active' : ''}`}
                                        onClick={() => setActiveTab('campaigns')}
                                    >
                                        <FiMail className="me-2" />
                                        Campaigns
                                    </button>
                                </li>
                                <li className="nav-item">
                                    <button 
                                        className={`nav-link ${activeTab === 'sequences' ? 'active' : ''}`}
                                        onClick={() => setActiveTab('sequences')}
                                    >
                                        <FiActivity className="me-2" />
                                        Sequences
                                    </button>
                                </li>
                            </ul>
                        </div>
                        <div className="card-body">
                            {loading ? (
                                <div className="text-center py-4">
                                    <div className="spinner-border" role="status">
                                        <span className="visually-hidden">Loading...</span>
                                    </div>
                                    <p className="mt-2 text-muted">Loading analytics...</p>
                                </div>
                            ) : (
                                <>
                                    {activeTab === 'overview' && renderOverview()}
                                    {activeTab === 'campaigns' && renderCampaigns()}
                                    {activeTab === 'sequences' && renderSequences()}
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Create Campaign Modal */}
            {showCreateCampaign && (
                <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">
                                    <FiMail className="me-2" />
                                    Create Campaign
                                </h5>
                                <button 
                                    type="button" 
                                    className="btn-close"
                                    onClick={() => setShowCreateCampaign(false)}
                                ></button>
                            </div>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Campaign Name</label>
                                    <input 
                                        type="text" 
                                        className="form-control"
                                        value={newCampaign.name}
                                        onChange={(e) => setNewCampaign(prev => ({ ...prev, name: e.target.value }))}
                                        placeholder="Enter campaign name"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Description</label>
                                    <textarea 
                                        className="form-control"
                                        value={newCampaign.description}
                                        onChange={(e) => setNewCampaign(prev => ({ ...prev, description: e.target.value }))}
                                        placeholder="Enter campaign description"
                                        rows="3"
                                    ></textarea>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button 
                                    type="button" 
                                    className="btn btn-secondary"
                                    onClick={() => setShowCreateCampaign(false)}
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="button" 
                                    className="btn btn-primary"
                                    onClick={createCampaign}
                                    disabled={loading || !newCampaign.name.trim()}
                                >
                                    {loading ? 'Creating...' : 'Create Campaign'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Create Sequence Modal */}
            {showCreateSequence && (
                <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">
                                    <FiActivity className="me-2" />
                                    Create Sequence
                                </h5>
                                <button 
                                    type="button" 
                                    className="btn-close"
                                    onClick={() => setShowCreateSequence(false)}
                                ></button>
                            </div>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">Sequence Name</label>
                                    <input 
                                        type="text" 
                                        className="form-control"
                                        value={newSequence.name}
                                        onChange={(e) => setNewSequence(prev => ({ ...prev, name: e.target.value }))}
                                        placeholder="Enter sequence name"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Description</label>
                                    <textarea 
                                        className="form-control"
                                        value={newSequence.description}
                                        onChange={(e) => setNewSequence(prev => ({ ...prev, description: e.target.value }))}
                                        placeholder="Enter sequence description"
                                        rows="3"
                                    ></textarea>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button 
                                    type="button" 
                                    className="btn btn-secondary"
                                    onClick={() => setShowCreateSequence(false)}
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="button" 
                                    className="btn btn-primary"
                                    onClick={createSequence}
                                    disabled={loading || !newSequence.name.trim()}
                                >
                                    {loading ? 'Creating...' : 'Create Sequence'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EmailTracking; 