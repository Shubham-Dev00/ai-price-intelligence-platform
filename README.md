# AI-Enhanced E-Commerce Price Intelligence and Alert Platform

A advanced level Flask web application for tracking product prices from e-commerce websites such as Amazon and Flipkart, analyzing price history, detecting suspicious price anomalies, and notifying users when prices drop below their target thresholds.

It uses modular Flask architecture, background job support, normalized SQLAlchemy models, analytics services, explainable AI-style insights, and deployment-ready structure.

---

## Features

### Core Product Tracking
- Multi-user authentication with registration, login, logout, and hashed passwords
- Role support for **admin** and **normal users**
- Add products by URL
- Automatic source-site detection
- Track target price per product
- Enable or disable tracking
- Delete tracked products
- Per-user duplicate protection
- Product detail view with history and status

### Price Monitoring
- Scheduled background checks
- Price snapshot history storage
- Scrape attempt logging
- Failed scrape tracking
- Safe currency parsing and normalization
- Retry-aware scraping flow

### Alerts and Notifications
- Email alert abstraction layer
- Alert deduplication to prevent spam
- Alert reset when price rises again
- Structured notification model for future SMS/WhatsApp support

### Dashboard and Analytics
- KPI summary cards
- Total tracked products
- Products below target
- Total alerts sent
- Recent scrape failures
- Product history chart
- Lowest / highest / latest / average metrics
- Status badges such as:
  - success
  - failed
  - scrape blocked
  - below target
  - anomaly detected

### AI-Style Intelligence
- Trend insight generation from historical prices
- Lightweight anomaly detection for suspicious price spikes/drops
- Smart alert prioritization
- Duplicate detection using fuzzy matching
- Explainable rule-based logic instead of fake AI claims

### Reliability and Safety
- Blocked-page detection for anti-bot retailer responses
- Manual fallback when scraping is blocked
- No blind trust in suspicious prices
- Graceful failure instead of crashing
- Centralized error handling
- Secure environment-variable based configuration

---

## Why This Project Matters

Many price tracker demos only work on ideal HTML and break immediately in the real world.

This project is different:
- it uses modular site parsers
- it logs failures instead of hiding them
- it safely detects blocked/anti-bot pages
- it supports manual fallback when live scrape verification fails
- it is structured to evolve into a SaaS-style platform

---

## Tech Stack

### Backend
- Python
- Flask
- SQLAlchemy
- Flask-Migrate
- Flask-Login
- Flask-WTF

### Frontend
- HTML
- CSS
- Bootstrap 5
- Jinja2
- Chart.js

### Data / Jobs / Infra
- PostgreSQL for production
- SQLite fallback for local development
- Celery + Redis architecture support
- APScheduler fallback for local development
- Docker
- Docker Compose
- Gunicorn

### Scraping
- requests
- BeautifulSoup
- Selenium-ready architecture path for future fallback hardening

### Testing
- pytest
- pytest-flask
- pytest-mock

---

### High-Level Flow

1. User registers and logs in
2. User adds a product URL and target price
3. Scraper tries to fetch title/price from Amazon or Flipkart
4. If scraping succeeds:
   - price snapshot is stored
   - analytics and insight generation can run
   - alert logic checks target threshold
5. If scraping is blocked:
   - product can still be saved using manual fallback
   - price is marked as not verified
   - status becomes `scrape_blocked`
   - background refresh can retry later
6. Dashboard and product detail pages visualize history, metrics, and status

---
