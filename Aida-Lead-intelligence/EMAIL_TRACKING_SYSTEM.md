# Email Tracking System Documentation

## 🎯 **Overview**

The Email Tracking System is a comprehensive solution that enables tracking of email engagement, automation of follow-up sequences, and detailed analytics for email campaigns. It's designed to work seamlessly with the Aida Lead Intelligence Platform.

## 📊 **Key Features**

### **1. Email Event Tracking**
- **Email Opens**: Tracks when emails are opened via tracking pixels
- **Link Clicks**: Tracks when links in emails are clicked
- **Email Replies**: Tracks when recipients reply to emails
- **Bounces**: Tracks failed email deliveries
- **Unsubscribes**: Tracks unsubscribe requests
- **Spam Reports**: Tracks when emails are marked as spam

### **2. Campaign Management**
- Create and manage email campaigns
- Track campaign performance metrics
- Segment campaigns by different criteria
- Campaign analytics and reporting

### **3. Sequence Automation**
- Multi-step email sequences
- Conditional logic based on engagement
- Time-based triggers
- Automated follow-up emails

### **4. Analytics & Reporting**
- Real-time email performance metrics
- Engagement rate tracking
- Conversion tracking
- Detailed event logs

## 🏗️ **System Architecture**

### **Database Schema**

#### **Email Tracking Tables**

```sql
-- Email campaigns table
CREATE TABLE email_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Email sequences table
CREATE TABLE email_sequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    campaign_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    steps JSON NOT NULL,
    triggers JSON,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (campaign_id) REFERENCES email_campaigns (id)
);

-- Email tracking table
CREATE TABLE email_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    campaign_id INTEGER,
    sequence_id INTEGER,
    lead_id INTEGER,
    email_address TEXT NOT NULL,
    subject TEXT,
    template_id INTEGER,
    status TEXT DEFAULT 'pending',
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    bounced_at TIMESTAMP,
    unsubscribed_at TIMESTAMP,
    spam_reported_at TIMESTAMP,
    tracking_id TEXT UNIQUE,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (campaign_id) REFERENCES email_campaigns (id),
    FOREIGN KEY (sequence_id) REFERENCES email_sequences (id),
    FOREIGN KEY (lead_id) REFERENCES leads (id),
    FOREIGN KEY (template_id) REFERENCES email_templates (id)
);

-- Email tracking events table
CREATE TABLE email_tracking_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSON,
    ip_address TEXT,
    user_agent TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tracking_id) REFERENCES email_tracking (id)
);

-- Email sequence instances table
CREATE TABLE email_sequence_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    sequence_id INTEGER NOT NULL,
    lead_id INTEGER NOT NULL,
    current_step INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    paused_at TIMESTAMP,
    resumed_at TIMESTAMP,
    next_step_due TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (sequence_id) REFERENCES email_sequences (id),
    FOREIGN KEY (lead_id) REFERENCES leads (id)
);

-- Email automation rules table
CREATE TABLE email_automation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    trigger_conditions JSON,
    action_type TEXT NOT NULL,
    action_data JSON,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## 🔧 **API Endpoints**

### **Tracking Endpoints**

#### **1. Email Open Tracking**
```
GET /api/email/track/open/{tracking_id}
```
- Tracks when an email is opened
- Returns a 1x1 transparent GIF
- Records IP address and user agent

#### **2. Email Click Tracking**
```
GET /api/email/track/click/{tracking_id}?url={redirect_url}
```
- Tracks when a link in an email is clicked
- Redirects to the original URL
- Records click data and redirect URL

#### **3. Email Unsubscribe Tracking**
```
GET /api/email/track/unsubscribe/{tracking_id}
```
- Tracks unsubscribe requests
- Updates lead status if needed

#### **4. Manual Event Tracking**
```
POST /api/email/track
{
    "tracking_id": "uuid",
    "event_type": "opened|clicked|replied|bounced|unsubscribed",
    "event_data": {}
}
```

### **Campaign Management Endpoints**

#### **1. Get Campaigns**
```
GET /api/email/campaigns
```

#### **2. Create Campaign**
```
POST /api/email/campaigns
{
    "name": "Campaign Name",
    "description": "Campaign Description",
    "status": "draft"
}
```

#### **3. Get Campaign**
```
GET /api/email/campaigns/{campaign_id}
```

#### **4. Update Campaign**
```
PUT /api/email/campaigns/{campaign_id}
```

#### **5. Delete Campaign**
```
DELETE /api/email/campaigns/{campaign_id}
```

### **Sequence Management Endpoints**

#### **1. Get Sequences**
```
GET /api/email/sequences
```

#### **2. Create Sequence**
```
POST /api/email/sequences
{
    "name": "Sequence Name",
    "description": "Sequence Description",
    "campaign_id": 1,
    "steps": [
        {
            "step": 1,
            "template_id": 1,
            "delay_days": 1,
            "trigger_conditions": {
                "event_type": "opened"
            }
        }
    ],
    "triggers": {
        "start_condition": "immediate"
    }
}
```

#### **3. Start Sequence**
```
POST /api/email/sequences/{sequence_id}/start
{
    "lead_id": 1
}
```

### **Analytics Endpoints**

#### **1. Email Analytics**
```
GET /api/email/analytics?days=30
```

#### **2. Tracking Details**
```
GET /api/email/tracking/{tracking_id}
```

### **Email Sending Endpoints**

#### **1. Send Tracked Email**
```
POST /api/email/send
{
    "lead_id": 1,
    "template_id": 1,
    "email_address": "recipient@example.com",
    "subject": "Email Subject",
    "content": "<html>Email content</html>",
    "campaign_id": 1,
    "sequence_id": 1
}
```

## 🎯 **Tracking Implementation**

### **1. Tracking Pixel Implementation**

When an email is sent, a tracking pixel is automatically added:

```html
<img src="http://localhost:5000/api/email/track/open/{tracking_id}" 
     width="1" height="1" style="display:none;" />
```

### **2. Link Tracking Implementation**

Links in emails are automatically converted to tracked links:

```html
<!-- Original link -->
<a href="https://example.com">Click here</a>

<!-- Becomes -->
<a href="http://localhost:5000/api/email/track/click/{tracking_id}?url=https://example.com">
    Click here
</a>
```

### **3. Event Processing**

When a tracking event occurs:

1. **Event Recording**: The event is recorded in the database
2. **Automation Check**: System checks for automation rules
3. **Sequence Update**: If part of a sequence, updates sequence progress
4. **Lead Status Update**: Updates lead status based on engagement

## 🤖 **Automation System**

### **Automation Rules**

The system supports various automation triggers:

#### **1. Email Event Triggers**
```json
{
    "trigger_type": "email_event",
    "trigger_conditions": {
        "event_type": "opened"
    }
}
```

#### **2. Time-based Triggers**
```json
{
    "trigger_type": "time_based",
    "trigger_conditions": {
        "days_since_last": 7
    }
}
```

#### **3. Engagement-based Triggers**
```json
{
    "trigger_type": "engagement_based",
    "trigger_conditions": {
        "min_opens": 3,
        "min_clicks": 1
    }
}
```

### **Automation Actions**

#### **1. Send Follow-up Email**
```json
{
    "action_type": "send_email",
    "action_data": {
        "template_id": 2,
        "subject": "Follow-up"
    }
}
```

#### **2. Update Lead Status**
```json
{
    "action_type": "update_lead_status",
    "action_data": {
        "status": "engaged"
    }
}
```

#### **3. Add to Sequence**
```json
{
    "action_type": "add_to_sequence",
    "action_data": {
        "sequence_id": 1
    }
}
```

## 📈 **Analytics & Metrics**

### **Key Metrics Tracked**

1. **Open Rate**: Percentage of emails opened
2. **Click Rate**: Percentage of emails with clicks
3. **Reply Rate**: Percentage of emails that received replies
4. **Bounce Rate**: Percentage of emails that bounced
5. **Unsubscribe Rate**: Percentage of unsubscribes
6. **Conversion Rate**: Percentage of emails leading to conversions

### **Analytics Data Structure**

```json
{
    "total_emails": 1000,
    "opened_emails": 250,
    "clicked_emails": 50,
    "replied_emails": 25,
    "bounced_emails": 20,
    "unsubscribed_emails": 10,
    "total_opens": 300,
    "total_clicks": 75,
    "open_rate": 25.0,
    "click_rate": 5.0,
    "reply_rate": 2.5,
    "bounce_rate": 2.0,
    "unsubscribe_rate": 1.0
}
```

## 🔄 **Sequence Management**

### **Sequence Structure**

```json
{
    "name": "Welcome Sequence",
    "description": "Welcome new leads",
    "steps": [
        {
            "step": 1,
            "template_id": 1,
            "delay_days": 0,
            "trigger_conditions": {
                "event_type": "immediate"
            }
        },
        {
            "step": 2,
            "template_id": 2,
            "delay_days": 3,
            "trigger_conditions": {
                "event_type": "opened"
            }
        },
        {
            "step": 3,
            "template_id": 3,
            "delay_days": 7,
            "trigger_conditions": {
                "event_type": "clicked"
            }
        }
    ]
}
```

### **Sequence Logic**

1. **Immediate**: Send email immediately when sequence starts
2. **Opened**: Send next email when previous email is opened
3. **Clicked**: Send next email when previous email has clicks
4. **Replied**: Send next email when previous email receives reply
5. **Time-based**: Send next email after specified delay

## 🛠️ **Frontend Components**

### **EmailTracking Component**

The main tracking dashboard includes:

1. **Overview Tab**: Performance metrics and recent activity
2. **Campaigns Tab**: Campaign management and analytics
3. **Sequences Tab**: Sequence management and automation
4. **Tracking Details Tab**: Detailed event tracking

### **Key Features**

- Real-time analytics display
- Campaign and sequence management
- Event filtering and search
- Export capabilities
- Quick action buttons

## 🔒 **Security Considerations**

### **1. Tracking ID Security**
- Unique UUIDs for each tracking record
- No sensitive data in tracking URLs
- Rate limiting on tracking endpoints

### **2. Data Privacy**
- IP address anonymization options
- GDPR compliance features
- Unsubscribe functionality
- Data retention policies

### **3. Access Control**
- User-specific data isolation
- Authentication required for management endpoints
- Role-based access control

## 🚀 **Usage Examples**

### **1. Send a Tracked Email**

```javascript
const sendEmail = async () => {
    const response = await axios.post('/api/email/send', {
        lead_id: 1,
        template_id: 1,
        email_address: 'recipient@example.com',
        subject: 'Welcome to our platform',
        content: '<html>Welcome email content</html>',
        campaign_id: 1
    });
    
    if (response.data.success) {
        console.log('Email sent with tracking ID:', response.data.tracking_id);
    }
};
```

### **2. Create a Campaign**

```javascript
const createCampaign = async () => {
    const response = await axios.post('/api/email/campaigns', {
        name: 'Q1 2024 Campaign',
        description: 'Campaign for Q1 leads',
        status: 'draft'
    });
    
    if (response.data.success) {
        console.log('Campaign created:', response.data.campaign_id);
    }
};
```

### **3. Start a Sequence**

```javascript
const startSequence = async () => {
    const response = await axios.post('/api/email/sequences/1/start', {
        lead_id: 1
    });
    
    if (response.data.success) {
        console.log('Sequence started:', response.data.instance_id);
    }
};
```

## 📋 **Configuration**

### **Environment Variables**

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
SENDER_NAME=Aida Lead Intelligence

# Tracking Configuration
BASE_URL=http://localhost:5000
```

### **Database Configuration**

The system uses SQLite by default, but can be configured for other databases by modifying the database connection in `models/database.py`.

## 🔧 **Troubleshooting**

### **Common Issues**

1. **Tracking Pixel Not Loading**
   - Check if the tracking URL is accessible
   - Verify CORS settings
   - Check server logs for errors

2. **Emails Not Sending**
   - Verify SMTP credentials
   - Check email template validity
   - Ensure tracking ID generation is working

3. **Analytics Not Updating**
   - Check if tracking events are being recorded
   - Verify database connections
   - Check for JavaScript errors in frontend

### **Debug Mode**

Enable debug logging by setting the log level in the application configuration.

## 📚 **Future Enhancements**

1. **Advanced Analytics**: Machine learning for engagement prediction
2. **A/B Testing**: Built-in A/B testing for email campaigns
3. **Advanced Segmentation**: More sophisticated lead segmentation
4. **Integration APIs**: Third-party integrations (Mailchimp, HubSpot, etc.)
5. **Mobile App**: Native mobile application for tracking
6. **Real-time Notifications**: WebSocket-based real-time updates
7. **Advanced Reporting**: Custom report builder
8. **API Rate Limiting**: Enhanced rate limiting and security

This email tracking system provides a solid foundation for email marketing automation and can be extended based on specific business requirements. 