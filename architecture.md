# Candidate Information API System Architecture

## Overview

The Candidate Information API System is designed following a Layered Architecture pattern with clear separation of concerns, making it easy to extend, maintain, and develop. The system leverages both relational database (PostgreSQL) and knowledge graph (Neo4j) technologies to store and query data efficiently.

## Layered Architecture

### 1. Presentation Layer (API Layer)

This layer is responsible for handling HTTP requests, input validation, and returning responses. It includes:

- **Controllers/Routers**: Define API endpoints and handle request/response processing
- **DTOs (Data Transfer Objects)**: Define data structures for requests and responses
- **Middleware**: Handle authentication, logging, error handling

### 2. Business Logic Layer (Service Layer)

This layer contains the business logic of the application, handling business processes and orchestrating between repositories. It includes:

- **Services**: Implement business logic
- **Use Cases**: Implement specific use cases
- **Data Synchronization**: Ensure data is synchronized between PostgreSQL and Neo4j

### 3. Data Access Layer

This layer is responsible for interacting with databases, including:

- **Repositories**: Interact with PostgreSQL through SQLAlchemy
- **Graph Repositories**: Interact with Neo4j through Neo4j Driver
- **Query Builders**: Build complex queries

### 4. Domain Layer

This layer defines business entities and objects, including:

- **Models**: SQLAlchemy models for PostgreSQL
- **Graph Models**: Neo4j entity models
- **Enums/Constants**: Constant values and enumerations

### 5. Infrastructure Layer

This layer provides infrastructure services, including:

- **Database**: PostgreSQL connection configuration
- **Ontology**: Neo4j connection configuration and ontology definition
- **Cache**: Redis cache configuration
- **Logging**: Logging configuration

## Data Flow

1. **HTTP Request** → **Controller** → **Service** → **Repository/Graph Repository** → **Database/Neo4j**
2. **Database/Neo4j** → **Repository/Graph Repository** → **Service** → **Controller** → **HTTP Response**

## Data Synchronization Between PostgreSQL and Neo4j

The system uses a data synchronization mechanism between PostgreSQL and Neo4j through services. When performing CRUD operations on data, the service will:

1. Perform the operation on PostgreSQL through the repository
2. Synchronize data to Neo4j through the graph repository

This ensures data consistency between the two database systems.

## Neo4j Ontology

The knowledge graph in Neo4j is designed with the following nodes and relationships:

### Nodes

- **Candidate**: Student/candidate
- **School**: Educational institution
- **Exam**: Examination
- **Subject**: Academic subject
- **Major**: Field of study
- **Certificate**: Certification
- **Award**: Achievement award
- **ManagementUnit**: Administrative unit

### Relationships

- **STUDIES_AT**: Candidate studies at school
- **ATTENDS_EXAM**: Candidate participates in exam
- **HAS_SCORE**: Candidate has score in subject
- **ACHIEVES_CERTIFICATE**: Candidate achieves certificate
- **EARNS_AWARD**: Candidate earns award
- **BELONGS_TO**: School belongs to management unit
- **OFFERS_MAJOR**: School offers major
- **TEACHES_SUBJECT**: Major teaches subject
- **ORGANIZES_EXAM**: Unit organizes exam
- **INCLUDES_SUBJECT**: Exam includes subject
- **LOCATED_AT**: Exam takes place at location

## Caching Strategy

The system uses Redis to cache frequently accessed data:

- **List caching**: Lists of candidates, schools, exams
- **Detail caching**: Detailed information of candidates, schools, exams
- **Complex query result caching**: Results of complex graph queries

## Authentication and Authorization

The system uses a simplified authentication approach:

- **Public Access**: All candidate information endpoints are publicly accessible without authentication
- **Admin Authentication**: Administrative endpoints require JWT (JSON Web Token) authentication
- **Path-based Protection**: Only paths starting with `/api/v1/admin/` require authentication
- **Role-based Authorization**: Only users with the 'admin' role can access admin endpoints
- **Middleware Approach**: Authentication is handled by a dedicated middleware that only checks admin routes

This approach allows candidates to freely access their information while maintaining security for administrative functions.

## Deployment

The system is deployed using Docker and Docker Compose, with separate containers for:

- **API**: FastAPI application
- **PostgreSQL**: Relational database
- **Neo4j**: Knowledge graph
- **Redis**: Cache

## Monitoring and Logging

The system uses:

- **Logging**: Detailed logging of system activities
- **Request ID**: Each request is assigned a unique ID for tracking
- **Performance Metrics**: Measure performance of API endpoints 