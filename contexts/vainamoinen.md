# Vainamoinen Project Context

## Project Overview

Vainamoinen is a full-stack web application for managing educational content.

## Tech Stack

- **Frontend**: React 18 with TypeScript, Tailwind CSS
- **Backend**: Node.js with Express, Prisma ORM
- **Database**: PostgreSQL
- **Authentication**: JWT tokens
- **Testing**: Jest + Testing Library

## Coding Standards

### Frontend (React/TypeScript)

- If you import a component, make sure it appears in your JSX return statement.
- Use functional components with hooks
- Prefer TypeScript interfaces over types
- Use Tailwind CSS for all styling
- Follow React best practices (key props, proper state management)
- Use React Query for API calls
- Implement proper error boundaries

### Backend (Node.js/Express)

- Use async/await for all async operations
- Implement proper error handling with try-catch
- Use Prisma for all database operations
- Follow RESTful API conventions
- Implement proper input validation
- Use middleware for authentication and logging

### Database (PostgreSQL/Prisma)

- Use Prisma migrations for schema changes
- Follow proper normalization principles
- Use appropriate indexes for performance
- Implement soft deletes where appropriate
- Use transactions for multi-table operations

## Testing Requirements

- Write unit tests for all utility functions
- Write integration tests for API endpoints
- Write component tests for React components
- Aim for 80%+ test coverage
- Use Jest and Testing Library for frontend tests
- Use Jest and Supertest for backend tests

## Security Considerations

- Validate all inputs on both frontend and backend
- Use proper authentication and authorization
- Implement rate limiting for API endpoints
- Sanitize user inputs to prevent XSS
- Use HTTPS in production
- Implement proper CORS policies

## Performance Guidelines

- Use React.memo for expensive components
- Implement proper pagination for large datasets
- Use database indexes for frequently queried fields
- Implement caching where appropriate
- Optimize bundle size with code splitting
- Use lazy loading for routes

## Common Patterns

- Use custom hooks for shared logic
- Implement proper loading and error states
- Use TypeScript strict mode
- Follow the single responsibility principle
- Implement proper logging throughout the application
- Use environment variables for configuration

## File Structure

```
vainamoinen/
├── frontend/          # React application
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API services
│   │   └── utils/        # Utility functions
├── backend/           # Node.js API
│   ├── src/
│   │   ├── controllers/  # Route handlers
│   │   ├── models/       # Prisma models
│   │   ├── middleware/   # Express middleware
│   │   ├── services/     # Business logic
│   │   └── utils/        # Utility functions
└── prisma/           # Database schema and migrations
```
