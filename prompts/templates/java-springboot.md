# [Project Name] Project Context

## Project Overview

[Brief description of what this project does]

## Tech Stack

- **Backend**: Java with Spring Boot, Spring Data JPA
- **Database**: PostgreSQL with Hibernate
- **Authentication**: Spring Security with JWT
- **Testing**: JUnit 5, Mockito, TestContainers
- **Build**: Maven or Gradle
- **API**: RESTful APIs with Spring Web

## Coding Standards

### Java Backend

- Use Java 17+ features (records, switch expressions, text blocks)
- Use `@Service`, `@Repository`, `@Controller` annotations
- Use dependency injection with `@Autowired` or constructor injection
- Use `@Transactional` for database operations
- Use proper exception handling with `@ControllerAdvice`
- Use `@Valid` for input validation
- Use `@Configuration` for configuration classes
- Follow Java naming conventions

### Database (JPA/Hibernate)

- Use JPA entities with proper annotations
- Use `@Entity`, `@Table`, `@Column` for mapping
- Use `@OneToMany`, `@ManyToOne`, `@ManyToMany` for relationships
- Use `@Query` for custom queries
- Use `@Modifying` for update/delete operations
- Use proper indexes with `@Index`
- Use `@Version` for optimistic locking

### API Design (Spring Web)

- Use `@RestController` for REST endpoints
- Use `@RequestMapping`, `@GetMapping`, `@PostMapping` for routes
- Use `@RequestBody` for request data
- Use `@ResponseEntity` for response control
- Use `@PathVariable` for path parameters
- Use `@RequestParam` for query parameters
- Use proper HTTP status codes

## Testing Requirements

- Write unit tests for all service classes
- Write integration tests for API endpoints
- Write repository tests with TestContainers
- Use `@SpringBootTest` for integration tests
- Use `@MockBean` for mocking dependencies
- Use `@TestConfiguration` for test configuration
- Aim for 80%+ test coverage

## Security Considerations

- Use Spring Security for authentication
- Implement JWT token authentication
- Use `@PreAuthorize` for method-level security
- Validate all inputs with Bean Validation
- Implement rate limiting
- Use HTTPS in production
- Implement proper CORS policies
- Use environment variables for secrets

## Performance Guidelines

- Use `@Async` for asynchronous operations
- Implement proper pagination with `Pageable`
- Use database indexes for frequently queried fields
- Implement caching with `@Cacheable`
- Use connection pooling for database connections
- Use `@Transactional(readOnly = true)` for read operations
- Implement proper error handling

## Common Patterns

- Use dependency injection for services
- Use `@ConfigurationProperties` for configuration
- Use `@EventListener` for application events
- Use `@Scheduled` for scheduled tasks
- Use `@Conditional` for conditional beans
- Use `@Profile` for environment-specific configuration
- Use proper logging with SLF4J

## File Structure

```
[project-name]/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/
│   │   │       └── [company]/
│   │   │           └── [project]/
│   │   │               ├── [Project]Application.java
│   │   │               ├── config/          # Configuration classes
│   │   │               │   ├── SecurityConfig.java
│   │   │               │   ├── DatabaseConfig.java
│   │   │               │   └── WebConfig.java
│   │   │               ├── controller/      # REST controllers
│   │   │               │   ├── [Entity]Controller.java
│   │   │               │   └── AuthController.java
│   │   │               ├── service/         # Business logic
│   │   │               │   ├── [Entity]Service.java
│   │   │               │   └── AuthService.java
│   │   │               ├── repository/      # Data access
│   │   │               │   ├── [Entity]Repository.java
│   │   │               │   └── UserRepository.java
│   │   │               ├── model/           # JPA entities
│   │   │               │   ├── [Entity].java
│   │   │               │   └── User.java
│   │   │               ├── dto/             # Data transfer objects
│   │   │               │   ├── [Entity]Dto.java
│   │   │               │   └── UserDto.java
│   │   │               ├── exception/        # Custom exceptions
│   │   │               │   ├── [Entity]NotFoundException.java
│   │   │               │   └── GlobalExceptionHandler.java
│   │   │               └── util/            # Utility classes
│   │   │                   ├── JwtUtil.java
│   │   │                   └── PasswordUtil.java
│   │   └── resources/
│   │       ├── application.yml              # Configuration
│   │       ├── application-dev.yml         # Development config
│   │       ├── application-prod.yml        # Production config
│   │       └── db/migration/              # Flyway migrations
│   └── test/
│       ├── java/
│       │   └── com/
│       │       └── [company]/
│       │           └── [project]/
│       │               ├── controller/     # Controller tests
│       │               ├── service/        # Service tests
│       │               └── repository/     # Repository tests
│       └── resources/
│           └── application-test.yml        # Test configuration
├── pom.xml                                 # Maven configuration
└── README.md
```

## Project-Specific Notes

[Add any specific requirements, integrations, or patterns unique to this project]

## Common Dependencies

- Spring Boot Starter Web: Web framework
- Spring Boot Starter Data JPA: JPA/Hibernate
- Spring Boot Starter Security: Security
- Spring Boot Starter Validation: Bean validation
- Spring Boot Starter Test: Testing
- PostgreSQL Driver: Database driver
- JWT: JSON Web Tokens
- Flyway: Database migrations
- TestContainers: Integration testing
