# [Project Name] Project Context

## Project Overview

[Brief description of what this project does]

## Tech Stack

- **Backend**: Scala with Akka HTTP, Slick ORM
- **Database**: PostgreSQL
- **Build**: Maven
- **Testing**: ScalaTest
- **Authentication**: JWT tokens
- **API**: RESTful APIs with OpenAPI documentation

## Coding Standards

### Scala Backend

- Use `case class` for data models
- Use `object` for singletons and utilities
- Use `trait` for interfaces and mixins
- Use `val` for immutable values, `var` only when necessary
- Use `Option` for nullable values
- Use `Either` for error handling
- Use `Future` for asynchronous operations
- Use `for` comprehensions for monadic operations

### Database (Slick)

- Use Slick table definitions with `Table` trait
- Use `DBIO` for database operations
- Use transactions for multi-table operations
- Use proper indexes for performance
- Use prepared statements for security

### API Design

- Use Akka HTTP for REST endpoints
- Use `Route` for endpoint definitions
- Use `Directive` for request handling
- Use `Marshalling` for JSON serialization
- Use `Unmarshalling` for JSON deserialization
- Use proper HTTP status codes
- Use OpenAPI for API documentation

## Testing Requirements

- Write unit tests for all utility functions
- Write integration tests for API endpoints
- Write database tests with test containers
- Use ScalaTest for all tests
- Use `Mockito` for mocking
- Aim for 80%+ test coverage

## Security Considerations

- Validate all inputs on both frontend and backend
- Use proper authentication and authorization
- Implement rate limiting for API endpoints
- Sanitize user inputs to prevent XSS
- Use HTTPS in production
- Implement proper CORS policies
- Use JWT tokens for authentication

## Performance Guidelines

- Use `Future` for asynchronous operations
- Implement proper pagination for large datasets
- Use database indexes for frequently queried fields
- Implement caching where appropriate
- Use connection pooling for database connections
- Use proper error handling to avoid memory leaks

## Common Patterns

- Use `sealed trait` for ADTs
- Use `implicit` for type classes
- Use `type` aliases for complex types
- Use `companion object` for factory methods
- Use `apply` methods for constructors
- Use `unapply` methods for pattern matching

## File Structure

```
[project-name]/
├── src/
│   ├── main/
│   │   ├── scala/
│   │   │   ├── controllers/    # API controllers
│   │   │   ├── models/         # Data models
│   │   │   ├── services/       # Business logic
│   │   │   ├── repositories/   # Data access
│   │   │   └── utils/          # Utility functions
│   │   └── resources/
│   │       ├── application.conf
│   │       └── db/             # SQL migrations
│   └── test/
│       └── scala/
│           ├── controllers/    # Controller tests
│           ├── services/       # Service tests
│           └── utils/          # Utility tests
└── pom.xml                    # Maven configuration
```

## Project-Specific Notes

[Add any specific requirements, integrations, or patterns unique to this project]
