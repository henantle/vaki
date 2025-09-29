# [Project Name] Project Context

## Project Overview

[Brief description of what this project does]

## Tech Stack

- **Backend**: Clojure with Ring, Compojure, and PostgreSQL
- **Frontend**: ClojureScript with Reagent (React wrapper)
- **Database**: PostgreSQL with custom SQL migrations
- **Testing**: Clojure test framework
- **Build**: Leiningen
- **Styling**: Less CSS

## Coding Standards

### Clojure Backend

- Use `defn` for all functions
- Prefer pure functions and immutable data structures
- Use `let` for local bindings
- Use `->` and `->>` threading macros for data transformation
- Use `cond` instead of nested `if` statements
- Use `some->` for safe navigation
- Implement proper error handling with `try-catch`

### ClojureScript Frontend

- Use Reagent components with `defn` and `[props]` destructuring
- Use `atom` for component state
- Use `reagent/with-let` for component lifecycle
- Use `reagent/create-class` for complex components
- Prefer functional components over class components
- Use `reagent.core/as-element` for JSX-like syntax

### Database (PostgreSQL)

- Use custom SQL migrations in `resources/db/`
- Follow proper normalization principles
- Use appropriate indexes for performance
- Use transactions for multi-table operations
- Use prepared statements for security

## Testing Requirements

- Write unit tests for all utility functions
- Write integration tests for API endpoints
- Write component tests for Reagent components
- Use `clojure.test` for backend tests
- Use `cljs.test` for frontend tests
- Aim for 80%+ test coverage

## Security Considerations

- Validate all inputs on both frontend and backend
- Use proper authentication and authorization
- Implement rate limiting for API endpoints
- Sanitize user inputs to prevent XSS
- Use HTTPS in production
- Implement proper CORS policies

## Performance Guidelines

- Use `memoize` for expensive computations
- Implement proper pagination for large datasets
- Use database indexes for frequently queried fields
- Implement caching where appropriate
- Optimize bundle size with advanced compilation
- Use lazy sequences for large data processing

## Common Patterns

- Use `defmulti` and `defmethod` for polymorphism
- Use `spec` for data validation
- Use `core.async` for asynchronous operations
- Use `re-frame` for state management
- Use `reagent-forms` for form handling
- Use `cljs-http` for API calls

## File Structure

```
[project-name]/
├── src/
│   ├── clj/                    # Clojure backend
│   │   ├── [project-name]/
│   │   │   ├── handlers/       # Ring handlers
│   │   │   ├── middleware/     # Ring middleware
│   │   │   ├── models/         # Data models
│   │   │   └── utils/          # Utility functions
│   ├── cljs/                   # ClojureScript frontend
│   │   ├── [project-name]/
│   │   │   ├── components/     # Reagent components
│   │   │   ├── pages/          # Page components
│   │   │   ├── handlers/       # Event handlers
│   │   │   └── utils/          # Utility functions
│   └── cljc/                   # Shared code
├── resources/
│   ├── db/                     # SQL migrations
│   ├── public/                 # Static assets
│   └── templates/              # HTML templates
├── test/                       # Test files
└── project.clj                 # Leiningen configuration
```

## Project-Specific Notes

[Add any specific requirements, integrations, or patterns unique to this project]
