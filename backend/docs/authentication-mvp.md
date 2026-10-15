# Findr MVP 0.1 Authentication Architecture

## Overview
Findr MVP 0.1 adopts a streamlined, least-complexity authentication architecture built around a single service-driven design. This avoids unnecessary abstraction layers, multi-file boilerplate, and complex ORM mapping while maintaining enterprise-grade security standards.

## Key Components

### 1. Password Hashing
- **Library**: `argon2-cffi`
- **Algorithm**: Argon2id (resistant to GPU and side-channel attacks).
- **Usage**: Passwords are securely hashed before persistence and verified during login requests.

### 2. Token Management
- **Library**: `python-jose[cryptography]`
- **Format**: JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`).
- **Claims**:
  - `sub`: User identifier (subject).
  - `exp`: Expiration timestamp (short-lived access tokens, e.g., 15 minutes).

### 3. Simplified Single-Service Design
- Core auth logic resides in a single, cohesive service class (`AuthService`).
- Direct integration with FastAPI dependencies for request validation and user context injection.
- Zero unnecessary repository or DTO abstractions for the MVP phase.

## Security Considerations
- Secrets and keys (`SECRET_KEY`) must be configured via environment variables.
- HTTPS / secure transport enforced in production deployments.
- CORS restricted to trusted frontend origins.
