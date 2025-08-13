# Frappe Gemini Integration

A Frappe Framework application that integrates Google's Gemini AI models for intelligent chat assistance.

## Features

- **Gemini AI Integration**: Connect to Google's Gemini models (gemini-1.5-flash, gemini-1.5-pro, etc.)
- **Chat Interface**: Built-in chatbot interface for interacting with Gemini AI
- **Chat History**: Persistent storage of conversations
- **User Management**: Individual chat histories for each user
- **Easy Configuration**: Simple setup through Frappe Desk

## Installation

1. **Install the app**:
   ```bash
   bench get-app frappe_gemini_integration
   bench install-app frappe_gemini_integration
   ```

2. **Install Python dependencies**:
   ```bash
   bench pip install google-generativeai
   ```

3. **Configure Gemini API**:
   - Go to **Frappe Desk > Gemini Integration Settings**
   - Enter your Google Gemini API key
   - Select your preferred model

## Usage

1. **Access the Chatbot**:
   - Navigate to **Frappe Desk > Frappe ChatBot**
   - Start chatting with Gemini AI

2. **API Usage**:
   ```python
   from frappe_gemini_integration.api import ask_gemini
   
   response = ask_gemini("What is artificial intelligence?")
   print(response)
   ```

## Configuration

### API Key
Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Available Models
- `gemini-1.5-flash` - Fast and efficient
- `gemini-1.5-pro` - More capable model
- `gemini-1.0-pro` - Standard model
- `gemini-1.0-pro-vision` - Vision-enabled model

## Development

### Structure
```
frappe_gemini_integration/
├── api.py                    # Main API functions
├── hooks.py                  # Frappe hooks
├── frappe_gemini_integration/
│   ├── doctype/
│   │   ├── gemini_integration_settings/  # Settings configuration
│   │   └── gemini_prompt_log/            # Chat history storage
│   └── page/
│       └── frappe_chatbot/               # Chat interface
└── public/
    └── css/
        └── chatbot.css                   # Chat interface styling
```

### Adding New Features
1. Extend the API functions in `api.py`
2. Update the frontend in the chatbot page
3. Modify doctypes as needed

## License

MIT License - see [license.txt](license.txt) for details.

## Support

For issues and questions, please contact: manavmandli2990@gmail.com

