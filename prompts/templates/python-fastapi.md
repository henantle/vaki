# [Project Name] Project Context

## Project Overview

[Brief description of what this project does]

## Tech Stack

- **Backend**: Python with FastAPI, SQLAlchemy ORM
- **Database**: PostgreSQL
- **Authentication**: JWT tokens with python-jose
- **Testing**: pytest with pytest-asyncio
- **Build**: Poetry or pip with requirements.txt
- **API**: RESTful APIs with automatic OpenAPI documentation

## Coding Standards

### Python Backend

- Use type hints for all function parameters and return values
- Use `async`/`await` for asynchronous operations
- Use Pydantic models for data validation
- Use dependency injection with FastAPI's Depends
- Use proper error handling with HTTPException
- Use dataclasses for simple data structures
- Use enums for constants and choices
- Follow PEP 8 style guidelines

### Database (SQLAlchemy)

- Use SQLAlchemy ORM for database operations
- Use Alembic for database migrations
- Use async SQLAlchemy for async operations
- Use proper indexes for performance
- Use transactions for multi-table operations
- Use prepared statements for security

### API Design (FastAPI)

- Use FastAPI for REST endpoints
- Use Pydantic models for request/response validation
- Use dependency injection for authentication
- Use proper HTTP status codes
- Use automatic OpenAPI documentation
- Use background tasks for long-running operations
- Use WebSockets for real-time features

## Testing Requirements

- Write unit tests for all utility functions
- Write integration tests for API endpoints
- Write async tests with pytest-asyncio
- Use pytest fixtures for test setup
- Use pytest-mock for mocking
- Aim for 80%+ test coverage
- Use test databases for integration tests

## Security Considerations

- Validate all inputs with Pydantic models
- Use proper authentication and authorization
- Implement rate limiting with slowapi
- Sanitize user inputs to prevent injection attacks
- Use HTTPS in production
- Implement proper CORS policies
- Use JWT tokens for authentication
- Use environment variables for secrets

## Performance Guidelines

- Use async/await for I/O operations
- Implement proper pagination for large datasets
- Use database indexes for frequently queried fields
- Implement caching with Redis or in-memory
- Use connection pooling for database connections
- Use background tasks for heavy operations
- Implement proper error handling to avoid memory leaks

## Common Patterns

- Use dependency injection for services
- Use Pydantic models for data validation
- Use async context managers for resources
- Use dataclasses for simple data structures
- Use enums for constants
- Use type hints throughout the codebase
- Use logging for debugging and monitoring

## File Structure

```
[project-name]/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── deps.py            # Dependencies
│   │   └── v1/                # API version 1
│   │       ├── __init__.py
│   │       ├── api.py         # Route definitions
│   │       └── endpoints/     # Individual endpoints
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration
│   │   ├── security.py        # Authentication
│   │   └── database.py        # Database connection
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── [model].py
│   ├── schemas/                # Pydantic models
│   │   ├── __init__.py
│   │   └── [schema].py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   └── [service].py
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── [util].py
├── tests/                      # Test files
│   ├── __init__.py
│   ├── conftest.py            # Test configuration
│   ├── test_api/              # API tests
│   └── test_services/         # Service tests
├── alembic/                   # Database migrations
│   ├── versions/
│   └── env.py
├── requirements.txt            # Dependencies
└── pyproject.toml             # Project configuration
```

## Project-Specific Notes

[Add any specific requirements, integrations, or patterns unique to this project]

## Common Dependencies

- FastAPI: Web framework
- SQLAlchemy: ORM
- Alembic: Database migrations
- Pydantic: Data validation
- python-jose: JWT tokens
- pytest: Testing framework
- pytest-asyncio: Async testing
- uvicorn: ASGI server
