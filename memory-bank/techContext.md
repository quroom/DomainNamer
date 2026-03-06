# Technical Context: DomaiNamer

## Technology Stack

### Backend Framework
- **Django 5.0.1**: Web framework and ORM
- **Python 3.11+**: Core language
- **SQLite**: Development database
- **PostgreSQL**: Production database

### Frontend Technologies
- **Django Templates**: Server-side HTML rendering
- **HTMX**: Dynamic interactions without complex JavaScript
- **TailwindCSS**: Utility-first CSS framework
- **DaisyUI**: Component library for TailwindCSS

### External Services
- **OpenAI GPT-4 API**: Domain name generation
- **Python WHOIS Library**: Domain availability checking
- **Paddle API**: Payment processing and subscriptions

### Development Tools
- **Django Development Server**: Local development
- **TailwindCSS CLI**: CSS compilation
- **Git**: Version control
- **Environment Variables**: Configuration management

## Dependencies Management

### Core Requirements
```
Django>=5.0.1
openai>=1.0.0
python-whois>=0.9.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### Development Requirements
```
django-debug-toolbar>=4.0.0
black>=23.0.0
flake8>=6.0.0
```

### Production Requirements
```
psycopg2-binary>=2.9.0
gunicorn>=21.0.0
whitenoise>=6.0.0
```

## Environment Configuration

### Required Environment Variables
```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# PortOne Payment
PORTONE_API_KEY=your_portone_api_key
PORTONE_WEBHOOK_SECRET=your_webhook_secret

# Django Settings
SECRET_KEY=your_django_secret_key
DEBUG=True/False
ALLOWED_HOSTS=localhost,your-domain.com

# Database (Production)
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### Development Setup
1. **Clone Repository**: `git clone <repo-url>`
2. **Virtual Environment**: `python -m venv venv && source venv/bin/activate`
3. **Install Dependencies**: `pip install -r requirements.txt`
4. **Environment Setup**: Copy `.env.example` to `.env` and configure
5. **Database Migration**: `python manage.py migrate`
6. **Static Assets**: `npm run build` (for TailwindCSS)
7. **Run Server**: `python manage.py runserver`

## Database Design

### Core Tables
- **django_session**: Session management
- **domainamer_domainquery**: Generation requests
- **domainamer_generateddomain**: Domain candidates
- **domainamer_favorite**: User favorites
- **plans_userplan**: Subscription status
- **plans_paymenttransaction**: Payment records

### Indexes Strategy
- Session key indexing for fast lookups
- Query timestamp indexing for usage analytics
- Domain name indexing for duplicate prevention
- User plan indexing for permission checks

## API Integration Details

### OpenAI API Integration
- **Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Model**: GPT-4 or GPT-3.5-turbo
- **Authentication**: Bearer token via API key
- **Rate Limits**: 3,500 requests per minute (tier dependent)
- **Error Handling**: Exponential backoff with jitter

### WHOIS Integration
- **Library**: python-whois
- **Fallback**: Direct WHOIS servers query
- **Rate Limiting**: 1 request per second per domain
- **Caching**: 5-minute cache for availability results

### PortOne Integration
- **Checkout API**: Session creation and management
- **Webhook API**: Payment status updates
- **Authentication**: API key and webhook secret validation
- **Testing**: Sandbox environment for development

## Build and Deployment

### Static Asset Pipeline
1. **TailwindCSS**: Compile utility classes to CSS
2. **Django collectstatic**: Gather all static files
3. **Whitenoise**: Serve static files in production
4. **CDN Integration**: Optional CloudFront/CloudFlare

### Deployment Strategy
- **Platform**: Railway, Heroku, or DigitalOcean App Platform
- **Database**: Managed PostgreSQL service
- **Environment**: Production environment variables
- **Monitoring**: Error tracking and performance monitoring

## Performance Considerations

### Database Optimization
- Connection pooling for production
- Query optimization with select_related/prefetch_related
- Database indexes on frequently queried fields
- Regular VACUUM and ANALYZE for PostgreSQL

### Caching Strategy
- Django cache framework with Redis (production)
- Template fragment caching for expensive renders
- API response caching for external services
- Static asset caching with proper headers

### Monitoring and Logging
- Django logging configuration
- Error tracking (Sentry integration possible)
- Performance monitoring (APM tools)
- Usage analytics and metrics collection

## Security Configuration

### Django Security Settings
- CSRF protection enabled
- Secure cookie settings for production
- HTTPS redirect configuration
- Content Security Policy headers

### API Security
- Environment-based secret management
- Request rate limiting
- Input validation and sanitization
- SQL injection prevention via ORM 