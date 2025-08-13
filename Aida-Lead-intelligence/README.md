# AIDA Lead Intelligence Platform

A powerful multi-tenant AI-driven lead generation and management platform that integrates seamlessly with ERPNext CRM. Each user can register, configure their own ERPNext credentials, and manage their leads independently.

## Features

### 👥 Multi-Tenant Architecture
- **User Registration & Authentication**: Secure user registration and login system
- **Session Management**: Automatic session handling with configurable timeouts
- **User Isolation**: Each user's data is completely isolated from others
- **SQLite Database**: Lightweight database for storing user sessions and configurations
- **Secure Credential Storage**: Encrypted storage of ERPNext credentials per user

### 🎯 Lead Generation
- **AI-Powered Query Processing**: Describe your lead requirements in natural language
- **Google Maps Integration**: Extract business leads from Google Maps using Apify actors
- **Smart Filtering**: Filter by location, rating, contact information, and business type
- **User-Specific Lead Management**: Each user manages their own leads independently

### 🤖 AI Agent Capabilities
- **Natural Language Processing**: Uses Langchain + Gemini 2.0 for intent detection
- **Criteria Extraction**: Automatically extracts search parameters from user queries
- **Intelligent Mapping**: Maps lead data to ERPNext CRM fields

### 🔗 ERPNext Integration
- **Custom ERP Credentials**: Each user can set their own ERPNext credentials
- **Connection Testing**: Test ERPNext connectivity before saving credentials
- **Seamless CRM Sync**: Automatic lead creation in user's ERPNext instance
- **Field Mapping**: Comprehensive mapping of lead data to CRM fields
- **Additional Notes**: Detailed lead information stored as notes
- **Status Management**: Lead status tracking and updates

### 📊 Dashboard & Analytics
- **Personal Dashboard**: User-specific dashboard with their lead statistics
- **Real-time Statistics**: Track generated leads and sync status per user
- **Connection Monitoring**: ERPNext connection status and health checks
- **Lead Management**: View, filter, export, and delete user's leads
- **Configuration Management**: Centralized settings for company info and ERP credentials

## Technology Stack

- **Backend**: Flask (Python)
- **AI/ML**: Langchain, Google Gemini 2.0
- **Lead Generation**: Apify Actors (Google Maps, LinkedIn, Apollo)
- **CRM Integration**: frappe-client for ERPNext
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Data Processing**: Python, JSON

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- ERPNext instance (for CRM integration) - Each user configures their own
- Apify account and API token (optional)
- Google API key (for Gemini AI) (optional)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Aida-Lead-intelligence
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   ENCRYPTION_KEY=your-encryption-key-here
   FLASK_ENV=development
   
   # Optional: Global API Keys (users can also set these individually)
   APIFY_TOKEN=your-apify-token
   GOOGLE_API_KEY=your-google-api-key
   APOLLO_API_KEY=your-apollo-api-key
   ```

5. **Initialize the database**
   The SQLite database will be automatically created when you first run the application.

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the platform**
   Open your browser and navigate to `http://localhost:5000`

## Usage

### Getting Started

1. **Register an Account**
   - Navigate to `http://localhost:5000/register`
   - Create a new user account with username, email, and password
   - Login with your credentials at `http://localhost:5000/login`

2. **Configure Your Settings**
   - After logging in, go to the Configuration section in the dashboard
   - Set up your company information
   - Configure your ERPNext credentials
   - Add any required API keys

3. **Test ERPNext Connection**
   - Use the "Test Connection" feature to verify your ERPNext setup
   - Ensure your credentials are working before generating leads

### Lead Generation

1. **Navigate to Lead Generation**
   - Click on "Lead Generation" in the dashboard sidebar

2. **Describe Your Requirements**
   - Enter a natural language description of the leads you need
   - Example: "Find 20 restaurants in Los Angeles with email addresses and at least 4 stars rating"

3. **AI Processing**
   - The AI agent will extract criteria from your description
   - Criteria include: location, business type, filters, lead count

4. **Lead Generation**
   - Leads are generated from Google Maps using Apify actors
   - Results include business name, address, contact info, ratings, and more
   - All generated leads are saved to your personal lead database

5. **Lead Management**
   - View all your generated leads in the Leads section
   - Export leads to CSV format
   - Delete unwanted leads
   - Sync leads to your ERPNext CRM

### Configuration Management

1. **Company Information**
   - Set up your company details for future outreach campaigns
   - Configure contact information and value proposition
   - This information is used when creating leads in ERPNext

2. **ERPNext Integration**
   - Configure your personal ERPNext instance URL and credentials
   - Test connection to ensure proper integration
   - Each user has their own ERPNext configuration

3. **API Keys**
   - Set up Google API key for Gemini AI (if not set globally)
   - Configure Apify token for lead generation actors
   - Add Apollo API key for additional lead sources

4. **User Profile**
   - Update your profile information
   - Change password
   - Manage account settings

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### User Management
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile

### Configuration
- `GET /api/config/erp` - Get user's ERP configuration
- `POST /api/config/erp` - Save user's ERP configuration
- `GET /api/config/company` - Get user's company information
- `POST /api/config/company` - Save user's company information

### Lead Management
- `GET /api/leads` - Get user's leads
- `POST /api/leads/generate` - Generate new leads
- `DELETE /api/leads/<lead_id>` - Delete a specific lead
- `GET /api/leads/export` - Export user's leads to CSV

### ERP Integration
- `POST /api/erp/test-connection` - Test ERPNext connection
- `POST /api/erp/sync` - Sync leads to ERPNext

### Dashboard
- `GET /api/dashboard/stats` - Get user's dashboard statistics

### Legacy Endpoints (for backward compatibility)
- `POST /api/generate-leads` - Generate leads from natural language query
- `GET /api/lead-sources` - Get available lead generation sources
- `GET /api/settings` - Get current platform settings
- `POST /api/settings` - Update platform settings

**Note**: All API endpoints (except authentication) require a valid session token.

## Lead Data Structure

Generated leads include the following information:

```json
{
  "source": "Google Maps",
  "company_name": "Business Name",
  "email": "contact@business.com",
  "phone": "+1-555-0123",
  "website": "https://business.com",
  "address": "123 Main St, City, State, ZIP",
  "city": "City",
  "state": "State",
  "country": "Country",
  "postal_code": "12345",
  "rating": 4.5,
  "review_count": 150,
  "category": "Restaurant",
  "description": "Business description",
  "google_maps_url": "https://maps.google.com/...",
  "social_media": {
    "instagram": ["https://instagram.com/business"],
    "facebook": ["https://facebook.com/business"]
  },
  "business_hours": [...],
  "additional_info": {...}
}
```

## ERPNext Integration

### Lead Mapping
The platform maps lead data to ERPNext Lead doctype fields:

- `lead_name` → Company name
- `company_name` → Business name
- `email_id` → Primary email
- `phone` → Primary phone
- `website` → Business website
- `address_line1` → Full address
- `city`, `state`, `country`, `pincode` → Location details
- `source` → "Lead Intelligence Platform"
- Custom fields for rating, Google Maps URL, coordinates, etc.

### Additional Information
Detailed lead information is stored as notes linked to the lead:
- Business description
- Social media profiles
- Business hours
- Additional services and amenities
- Raw data from lead generation source

## Future Enhancements

### Lead Outreach (Coming Soon)
- **Email Template Management**: Create and manage email templates
- **Personalized Email Generation**: AI-generated personalized emails
- **Campaign Management**: Organize and track outreach campaigns
- **Email Automation**: Automated email sending through ERPNext

### Additional Lead Sources
- **LinkedIn Integration**: Generate leads from LinkedIn profiles and companies
- **Apollo Integration**: Access Apollo's lead database
- **Custom Sources**: Add custom lead generation sources

### Advanced Features
- **Lead Scoring**: AI-powered lead quality scoring
- **Duplicate Detection**: Automatic duplicate lead detection and merging
- **Advanced Analytics**: Detailed reporting and analytics
- **Webhook Integration**: Real-time notifications and integrations

## Troubleshooting

### Common Issues

1. **ERPNext Connection Failed**
   - Verify ERPNext URL, username, and password
   - Ensure ERPNext instance is accessible
   - Check user permissions in ERPNext

2. **Lead Generation Errors**
   - Verify Apify token is valid
   - Check Apify account credits
   - Ensure Google Maps actor is accessible

3. **AI Processing Issues**
   - Verify Google API key is configured
   - Check Gemini API quotas and limits
   - Ensure API key has proper permissions

### Support

For support and questions:
- Check the troubleshooting section above
- Review error messages in the browser console
- Check application logs for detailed error information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ERPNext team for the excellent CRM platform
- Apify for providing powerful web scraping actors
- Google for Gemini AI capabilities
- Langchain for AI framework
- Bootstrap team for the UI framework