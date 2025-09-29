# [Project Name] Project Context

## Project Overview

[Brief description of what this project does - a full-stack monorepo with shared code]

## Tech Stack

- **Frontend**: React with TypeScript, Vite, Tailwind CSS
- **Backend**: Node.js with Express, TypeScript
- **Database**: PostgreSQL with Prisma ORM
- **Shared**: TypeScript types and utilities
- **Build**: Turborepo for monorepo management
- **Testing**: Jest, Testing Library, Supertest
- **Package Manager**: pnpm for efficient dependency management

## Coding Standards

### Frontend (React/TypeScript)

- Use functional components with hooks
- Prefer TypeScript interfaces over types
- Use Tailwind CSS for all styling
- Follow React best practices (key props, proper state management)
- Use React Query for API calls
- Implement proper error boundaries
- Use shared types from the shared package

### Backend (Node.js/Express/TypeScript)

- Use TypeScript for type safety
- Use async/await for all async operations
- Implement proper error handling with try-catch
- Use Prisma for all database operations
- Follow RESTful API conventions
- Implement proper input validation
- Use middleware for authentication and logging
- Use shared types from the shared package

### Shared Code

- Use TypeScript for all shared utilities
- Export types and interfaces for frontend/backend use
- Use Zod for runtime validation
- Keep shared code framework-agnostic
- Use proper TypeScript strict mode
- Follow single responsibility principle

### Database (PostgreSQL/Prisma)

- Use Prisma migrations for schema changes
- Follow proper normalization principles
- Use appropriate indexes for performance
- Implement soft deletes where appropriate
- Use transactions for multi-table operations
- Use Prisma Client for type-safe database access

## Testing Requirements

- Write unit tests for all utility functions
- Write integration tests for API endpoints
- Write component tests for React components
- Write tests for shared utilities
- Use Jest and Testing Library for frontend tests
- Use Jest and Supertest for backend tests
- Aim for 80%+ test coverage across all packages

## Security Considerations

- Validate all inputs on both frontend and backend
- Use proper authentication and authorization
- Implement rate limiting for API endpoints
- Sanitize user inputs to prevent XSS
- Use HTTPS in production
- Implement proper CORS policies
- Use JWT tokens for authentication
- Use environment variables for configuration

## Performance Guidelines

- Use React.memo for expensive components
- Implement proper pagination for large datasets
- Use database indexes for frequently queried fields
- Implement caching where appropriate
- Optimize bundle size with code splitting
- Use lazy loading for routes
- Use Turborepo for efficient builds
- Use pnpm for efficient dependency management

## Common Patterns

- Use custom hooks for shared logic
- Implement proper loading and error states
- Use TypeScript strict mode
- Follow the single responsibility principle
- Implement proper logging throughout the application
- Use environment variables for configuration
- Use shared types for API contracts
- Use Zod for runtime validation

## File Structure

```
[project-name]/
├── apps/
│   ├── web/                    # React frontend
│   │   ├── src/
│   │   │   ├── components/     # Reusable components
│   │   │   ├── pages/         # Page components
│   │   │   ├── hooks/         # Custom hooks
│   │   │   ├── services/      # API services
│   │   │   └── utils/         # Utility functions
│   │   ├── public/            # Static assets
│   │   ├── package.json
│   │   └── vite.config.ts
│   └── api/                   # Node.js backend
│       ├── src/
│       │   ├── controllers/   # Route handlers
│       │   ├── middleware/    # Express middleware
│       │   ├── services/      # Business logic
│       │   ├── utils/         # Utility functions
│       │   └── app.ts         # Express app
│       ├── package.json
│       └── tsconfig.json
├── packages/
│   ├── shared/                # Shared utilities and types
│   │   ├── src/
│   │   │   ├── types/         # TypeScript types
│   │   │   ├── utils/         # Utility functions
│   │   │   └── validation/    # Zod schemas
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── database/              # Prisma schema and client
│       ├── prisma/
│       │   ├── schema.prisma  # Database schema
│       │   └── migrations/   # Database migrations
│       ├── src/
│       │   └── client.ts     # Prisma client
│       ├── package.json
│       └── tsconfig.json
├── tools/
│   ├── eslint-config/         # Shared ESLint config
│   ├── typescript-config/     # Shared TypeScript config
│   └── tailwind-config/      # Shared Tailwind config
├── package.json               # Root package.json
├── turbo.json                 # Turborepo configuration
├── pnpm-workspace.yaml        # pnpm workspace configuration
└── README.md
```

## Monorepo Management

### Turborepo Configuration

- Use `turbo.json` for build pipeline configuration
- Configure task dependencies and caching
- Use `--filter` for package-specific commands
- Use `--parallel` for concurrent execution

### Package Management

- Use pnpm for efficient dependency management
- Use workspace protocol for internal dependencies
- Use `pnpm -r` for recursive commands
- Use `pnpm --filter` for package-specific commands

### Shared Dependencies

- Use shared ESLint configuration
- Use shared TypeScript configuration
- Use shared Tailwind configuration
- Use shared testing utilities

## Project-Specific Notes

[Add any specific requirements, integrations, or patterns unique to this project]

## Common Commands

```bash
# Install dependencies
pnpm install

# Run all tests
pnpm test

# Build all packages
pnpm build

# Run frontend
pnpm --filter web dev

# Run backend
pnpm --filter api dev

# Run database migrations
pnpm --filter database db:migrate

# Generate Prisma client
pnpm --filter database db:generate
```
