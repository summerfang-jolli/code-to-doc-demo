# Sample Markdown Document

This is a sample Markdown file for testing RAGFlow upload functionality with standard MD format.

## Project Documentation

### Overview

This document contains technical documentation that can be processed by RAGFlow for semantic search and retrieval. Markdown files are perfect for creating searchable knowledge bases.

### Installation Guide

Follow these steps to set up the project:

1. **Clone the repository**
   ```bash
   git clone https://github.com/example/project.git
   cd project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### API Reference

#### Authentication

All API requests require authentication using an API key:

```http
GET /api/v1/data
Authorization: Bearer your-api-key
Content-Type: application/json
```

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/datasets` | List all datasets |
| POST | `/api/v1/datasets` | Create new dataset |
| PUT | `/api/v1/datasets/{id}` | Update dataset |
| DELETE | `/api/v1/datasets/{id}` | Delete dataset |

### Configuration Options

The following configuration parameters are available:

- **database_url**: PostgreSQL connection string
- **api_key**: Authentication key for external services
- **debug_mode**: Enable/disable debug logging
- **max_file_size**: Maximum upload file size (default: 10MB)

### Troubleshooting

#### Common Issues

**Connection Refused Error**
```
Error: Connection refused on port 5432
```
*Solution*: Ensure PostgreSQL is running and accessible.

**Authentication Failed**
```
Error: Invalid API key
```
*Solution*: Check your API key in the environment variables.

#### Performance Optimization

1. **Database Indexing**
   - Create indexes on frequently queried columns
   - Use partial indexes for conditional queries
   - Monitor query performance with EXPLAIN

2. **Caching Strategy**
   - Implement Redis for session storage
   - Cache API responses for static data
   - Use CDN for static assets

### Code Examples

#### Python Client Example

```python
import requests

class APIClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def get_datasets(self):
        response = requests.get(
            f'{self.base_url}/api/v1/datasets',
            headers=self.headers
        )
        return response.json()
```

#### JavaScript Integration

```javascript
const client = new APIClient({
  apiKey: process.env.API_KEY,
  baseUrl: 'https://api.example.com'
});

async function fetchData() {
  try {
    const datasets = await client.getDatasets();
    console.log('Datasets:', datasets);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

### Best Practices

1. **Security**
   - Always use HTTPS in production
   - Rotate API keys regularly
   - Implement rate limiting
   - Validate all input data

2. **Error Handling**
   - Use structured error responses
   - Log errors with context
   - Provide meaningful error messages
   - Implement retry mechanisms

3. **Documentation**
   - Keep API docs up to date
   - Include code examples
   - Document all configuration options
   - Provide troubleshooting guides

### FAQ

**Q: How do I reset my API key?**
A: Contact support or use the key rotation endpoint in your dashboard.

**Q: What file formats are supported?**
A: We support PDF, TXT, MD, MDX, DOC, DOCX, and HTML files.

**Q: Is there a rate limit?**
A: Yes, 1000 requests per hour for free tier, 10000 for premium.

### Contact Information

- **Support Email**: support@example.com
- **Documentation**: https://docs.example.com
- **GitHub Issues**: https://github.com/example/project/issues
- **Community Forum**: https://community.example.com

---

*Last updated: 2024-01-15*
*Version: 1.2.0*