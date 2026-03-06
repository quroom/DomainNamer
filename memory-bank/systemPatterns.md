# System Patterns: DomaiNamer

## Architecture Overview
DomaiNamer follows a traditional Django MVC pattern with HTMX for dynamic interactions, emphasizing server-side rendering and progressive enhancement.

## Application Structure
```
DomaiNamer/
├── core/                    # Django project configuration
├── domainamer/             # Core domain generation logic
├── plans/                  # Subscription and payment handling
├── templates/              # Shared templates (base.html)
├── static/                 # TailwindCSS compiled assets
└── memory-bank/            # Project documentation
```

## Key Design Patterns

### 1. Session-Based State Management
- **Pattern**: No user accounts required for core functionality
- **Implementation**: Django sessions for usage tracking and favorites
- **Benefits**: Lower friction, privacy-focused, easier development
- **Trade-offs**: Limited cross-device continuity

### 2. HTMX-First Dynamic Updates
- **Pattern**: Server-side HTML generation with targeted DOM updates
- **Implementation**: HTMX attributes on forms and buttons
- **Benefits**: Simple development, no complex JavaScript state
- **Trade-offs**: Less interactive than SPA approaches

### 3. Progressive Enhancement
- **Pattern**: Full functionality without JavaScript, enhanced with JS
- **Implementation**: Form submissions work via POST, enhanced via HTMX
- **Benefits**: Universal accessibility, SEO-friendly
- **Trade-offs**: Some UX constraints for complex interactions

### 4. External Service Integration
- **Pattern**: Server-side API calls with local caching
- **Implementation**: Django views handle OpenAI and WHOIS calls
- **Benefits**: API key security, request optimization, error handling
- **Trade-offs**: Increased server load, potential latency

## Data Models Design

### Domain Generation Models
- **DomainQuery**: Stores generation requests and parameters
- **GeneratedDomain**: Individual domain candidates with metadata
- **UserSession**: Tracks usage limits and preferences
- **Favorite**: Session-based favorite domain storage

### Payment Models
- **UserPlan**: Current subscription status and limits
- **PaymentTransaction**: Paddle transaction records
- **UsageCounter**: Daily/monthly usage tracking

## API Integration Patterns

### OpenAI Integration
- **Prompt Engineering**: Structured prompts for quality generation
- **Response Parsing**: Extract and validate domain candidates
- **Error Handling**: Graceful fallbacks for API failures
- **Rate Limiting**: Respect OpenAI API limits

### WHOIS Integration
- **Bulk Checking**: Optimize multiple domain queries
- **Caching Strategy**: Cache availability results for performance
- **Fallback Methods**: Multiple WHOIS sources for reliability
- **Result Validation**: Confirm availability accuracy

### Paddle Payment Integration
- **Webhook Handling**: Secure payment status updates
- **Session Management**: Link payments to user sessions
- **Security**: Vendor authentication, no stored card data
- **Plan Activation**: Automatic feature unlocking

## Caching Strategy
- **Domain Availability**: 5-minute cache for WHOIS results
- **Generated Names**: 1-hour cache for identical queries
- **User Sessions**: Database-backed session storage
- **Static Assets**: CDN caching for TailwindCSS builds

## Error Handling Patterns
- **API Failures**: Graceful degradation with user-friendly messages
- **Rate Limiting**: Clear communication of limits and retry timing
- **Payment Issues**: Comprehensive error states and recovery flows
- **Validation**: Client and server-side input validation

## Performance Considerations
- **Async Processing**: Background domain checking where possible
- **Database Indexing**: Optimized queries for session and usage data
- **Static Asset Optimization**: Minified CSS, optimized images
- **CDN Strategy**: Static asset delivery optimization

## Security Patterns
- **CSRF Protection**: Django CSRF middleware for all forms
- **API Key Management**: Environment-based configuration
- **Payment Security**: Paddle handles all sensitive data
- **Rate Limiting**: IP-based and session-based limits
- **Input Validation**: Comprehensive sanitization and validation 