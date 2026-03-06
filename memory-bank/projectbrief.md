# Project Brief: DomaiNamer

## Project Overview
DomaiNamer is a web application that automatically generates memorable and pronounceable domain names with real-time .com availability checking. It serves creators, entrepreneurs, and developers who need quality domain names for their projects.

## Core Purpose
- Generate memorable, pronounceable domain names using AI
- Provide instant .com domain availability verification
- Offer a seamless, HTMX-powered user experience
- Monetize through tiered subscription plans

## Target Users
- Startup founders needing brand names
- Product managers launching new services
- Side project developers
- Marketing professionals and designers

## Key Success Metrics
- Domain generation quality and user satisfaction
- Conversion rate from free to paid plans
- Session engagement and return usage
- Domain availability accuracy

## Project Constraints
- Minimal JavaScript usage (HTMX-first approach)
- Mobile-optimized responsive design
- Works fully without JavaScript enabled
- No personal data storage requirements
- Payment processing via Paddle (no sensitive data storage)

## Business Model
- **Free Tier**: 5 generations per day
- **Basic Plan**: Unlimited generations + advanced filters
- **Premium Plan**: All features + priority support + advanced analytics

## Technical Boundaries
- Django backend with SQLite (dev) / PostgreSQL (prod)
- OpenAI GPT API for name generation
- Python WHOIS for domain checking
- Paddle for payment processing
- TailwindCSS + DaisyUI for styling 