# Findr MVP 0.1 Authentication Requirements

## Functional Requirements

### 1. User Registration (`POST /api/v1/auth/register`)
- **Input**: Username/Email and password.
- **Validation**:
  - Email format validation.
  - Minimum password length (8+ characters).
- **Processing**: Hash password using Argon2id and store user record.
- **Output**: Created user summary (excluding password hash).

### 2. User Authentication (`POST /api/v1/auth/login`)
- **Input**: Username/Email and password.
- **Processing**: Verify credentials against stored password hash.
- **Output**: Signed JWT access token.

### 3. Current User Profile (`GET /api/v1/auth/me`)
- **Input**: Bearer token in `Authorization` header.
- **Processing**: Decode and validate JWT signature and expiration.
- **Output**: Authenticated user details.

## Non-Functional Requirements

### 1. Security
- Strong password hashing (Argon2id).
- Stateless JWT authentication with secure secret keys.

### 2. Simplicity & Maintainability
- Single-service design (`AuthService`) to minimize code complexity for MVP 0.1.
- Clear separation of HTTP routing and business logic.

### 3. Performance
- Low overhead token verification for rapid API responsiveness.
