# Aida Lead Intelligence

AI-Powered Lead Generation and Intelligence Platform for ERPNext

## Overview

Aida Lead Intelligence is a comprehensive Frappe app that transforms your ERPNext instance into a powerful lead generation and intelligence platform. It combines the capabilities of the external Aida-Lead-Intelligence platform with native ERPNext integration, providing seamless lead management, AI-powered scoring, and automated workflows.

## Features

### 🚀 Lead Generation
- **Multi-Source Lead Generation**: Generate leads from Google Maps, Apollo.io, and other sources
- **AI-Powered Query Processing**: Use natural language to describe your lead requirements
- **Automated Lead Discovery**: Find businesses based on industry, location, company size, and more
- **Batch Processing**: Generate hundreds of leads in a single operation

### 🧠 AI Lead Scoring
- **Intelligent Scoring**: Uses Google Gemini AI to analyze lead quality and potential
- **Comprehensive Assessment**: Scores based on contact completeness, industry relevance, company size, geographic targeting, and online presence
- **HOT/WARM/COLD Classification**: Clear lead prioritization for sales teams
- **Batch Scoring**: Score multiple leads simultaneously for efficiency

### 🔗 ERP Integration
- **Native ERPNext Integration**: Seamlessly sync leads to your ERPNext Lead module
- **Bidirectional Sync**: Keep lead data synchronized between systems
- **Automated Workflows**: Trigger actions based on lead scoring and status changes
- **Real-time Updates**: Instant synchronization of lead information

### 📊 Advanced Analytics
- **Dashboard Insights**: Comprehensive overview of lead generation performance
- **Performance Metrics**: Track success rates, quality scores, and processing times
- **Source Analytics**: Understand which lead sources perform best
- **Trend Analysis**: Monitor lead generation patterns over time

### ⚙️ Configuration & Management
- **Centralized Settings**: Manage all API keys and configurations in one place
- **User Management**: Role-based access control and permissions
- **Scheduled Tasks**: Automated lead scoring and data cleanup
- **Audit Trail**: Complete history of all lead generation and scoring activities

## Installation

### Prerequisites
- Frappe Framework 14+ or ERPNext 14+
- Python 3.8+
- Google Gemini API key
- Apify token (for Google Maps lead generation)
- Apollo.io API key (optional)

### Installation Steps

1. **Install the app**:
   ```bash
   bench get-app aida_lead_intelligence
   bench install-app aida_lead_intelligence
   ```

2. **Install dependencies**:
   ```bash
   bench pip install -r requirements.txt
   ```

3. **Run migrations**:
   ```bash
   bench migrate
   ```

4. **Configure the app**:
   - Go to **Aida Lead Intelligence Settings**
   - Enter your API keys and configuration
   - Test ERP connection

## Configuration

### API Configuration
- **Google API Key**: Required for AI lead scoring and natural language processing
- **Apify Token**: Required for Google Maps lead generation
- **Apollo API Key**: Optional for Apollo.io lead generation

### ERP Configuration
- **ERP URL**: Your ERPNext instance URL
- **Username**: ERPNext username for authentication
- **Password**: ERPNext password for authentication
- **API Key**: Optional API key for enhanced security

### Company Configuration
- **Company Name**: Your company name for lead generation context
- **Industry**: Your primary industry for better lead targeting
- **Website**: Company website for lead generation context

## Usage

### Generating Leads

1. **Navigate to Dashboard**: Go to **Aida Dashboard** in your ERPNext desk
2. **Click Generate Leads**: Use the "Generate Leads" button
3. **Describe Requirements**: Use natural language to describe what you're looking for
   - Example: "Find 20 tech companies in San Francisco with email addresses"
4. **Select Source**: Choose Google Maps or Apollo as your lead source
5. **Set Parameters**: Configure maximum leads and advanced criteria
6. **Generate**: Click generate and wait for results

### Lead Scoring

1. **Automatic Scoring**: Leads are automatically scored when generated
2. **Manual Scoring**: Use the "Score Lead" action on individual leads
3. **Batch Scoring**: Select multiple leads and use "Batch Score" for efficiency
4. **Review Results**: Check scoring factors, recommendations, and risk factors

### ERP Integration

1. **Automatic Sync**: Scored leads are automatically synced to ERPNext
2. **Manual Sync**: Use "Sync to ERP" action on individual leads
3. **Monitor Status**: Track sync status and ERP lead IDs
4. **Bidirectional Updates**: Changes in ERPNext are reflected in the dashboard

## API Endpoints

### Lead Generation
- `POST /api/method/aida_lead_intelligence.api.generate_leads` - Generate new leads
- `GET /api/method/aida_lead_intelligence.api.get_leads` - Retrieve leads with filtering
- `DELETE /api/method/aida_lead_intelligence.api.delete_lead` - Delete a lead

### Lead Scoring
- `POST /api/method/aida_lead_intelligence.api.score_lead` - Score a single lead
- `POST /api/method/aida_lead_intelligence.api.batch_score_leads` - Score multiple leads

### ERP Integration
- `POST /api/method/aida_lead_intelligence.api.sync_lead_to_erp` - Sync lead to ERP
- `POST /api/method/aida_lead_intelligence.api.test_erp_connection` - Test ERP connection

### Analytics
- `GET /api/method/aida_lead_intelligence.api.get_dashboard_stats` - Get dashboard statistics
- `GET /api/method/aida_lead_intelligence.api.get_lead_sources` - Get available lead sources

## Scheduled Tasks

The app includes several automated tasks:

- **Daily Lead Scoring**: Automatically score unscored leads
- **Hourly Lead Generation**: Monitor and process scheduled lead generation
- **Data Cleanup**: Remove old data to maintain performance
- **ERP Sync**: Automatically sync scored leads to ERP
- **Statistics Update**: Update performance metrics and analytics

## Customization

### Adding New Lead Sources
1. Extend the `LeadGenerator` class
2. Implement the required methods
3. Add configuration options to settings
4. Update the UI to include the new source

### Custom Scoring Factors
1. Modify the `LeadScoringService` class
2. Update the scoring prompt template
3. Adjust scoring weights and criteria
4. Test with sample data

### ERP Field Mapping
1. Update the `_map_lead_to_erp` method in `ERPIntegration`
2. Add new field mappings as needed
3. Test field synchronization

## Troubleshooting

### Common Issues

**API Key Errors**
- Verify API keys are correctly entered
- Check API key permissions and quotas
- Ensure keys are active and not expired

**ERP Connection Issues**
- Verify ERP URL and credentials
- Check network connectivity
- Ensure ERP user has required permissions

**Lead Generation Failures**
- Check source-specific API quotas
- Verify search criteria are valid
- Review error logs for specific issues

**Scoring Errors**
- Ensure Google API key is valid
- Check API quota limits
- Verify lead data format

### Debug Mode
Enable debug logging in Frappe settings to get detailed error information.

## Support

For support and questions:
- Check the documentation
- Review error logs
- Contact the development team
- Submit issues on the project repository

## Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- Lead generation from Google Maps and Apollo
- AI-powered lead scoring with Gemini
- ERPNext integration
- Comprehensive dashboard
- Scheduled tasks and automation

## Roadmap

### Upcoming Features
- LinkedIn lead generation
- Advanced filtering and segmentation
- Email campaign integration
- Lead nurturing workflows
- Advanced analytics and reporting
- Mobile app support
- Multi-language support
- Advanced AI models integration

---

**Aida Lead Intelligence** - Transforming ERPNext into a lead generation powerhouse.