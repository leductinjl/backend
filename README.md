# Candidate Information API System

An API system that provides endpoints to query candidate information, including personal details, education history, exam results, certificates, and awards.

## Technologies Used

- **Backend**: FastAPI (Python)
- **Relational Database**: PostgreSQL with SQLAlchemy
- **Knowledge Graph**: Neo4j
- **Cache**: Redis
- **Containers**: Docker, Docker Compose

## Project Structure

```
backend/
├── app/                            # Main source code
│   ├── api/                        # API Layer
│   │   ├── controllers/            # API Routers
│   │   ├── dto/                    # Data Transfer Objects
│   │   └── middleware/             # Middleware
│   ├── core/                       # Core functionality
│   ├── domain/                     # Domain Layer
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── graph_models/           # Neo4j models
│   │   └── enums/                  # Enums and constants
│   ├── infrastructure/             # Infrastructure Layer
│   │   ├── database/               # PostgreSQL connection
│   │   ├── ontology/               # Neo4j connection
│   │   ├── cache/                  # Redis connection
│   │   └── logging/                # Logging configuration
│   ├── repositories/               # Data Access Layer (PostgreSQL)
│   ├── graph_repositories/         # Data Access Layer (Neo4j)
│   ├── services/                   # Business Logic Layer
│   ├── utils/                      # Utility functions
│   ├── schemas/                    # Pydantic schemas
│   ├── main.py                     # Entry point
│   └── config.py                   # Configuration
├── tests/                          # Unit and integration tests
├── alembic/                        # Database migrations
├── docker-compose.yml              # Docker Compose configuration
├── Dockerfile                      # Docker configuration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables example
├── .gitignore                      # Git ignore file
└── README.md                       # Project documentation
```

## Installation and Setup

### Using Docker

1. Copy the `.env.example` file to `.env` and configure environment variables:

```bash
cp .env.example .env
```

2. Start containers with Docker Compose:

```bash
docker-compose up -d
```

3. The API will be available at: http://localhost:8000

4. Access API documentation at: http://localhost:8000/api/v1/docs

### Direct Execution (Development)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure environment variables.

3. Run the application:

```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Public Endpoints

These endpoints are available to anyone without authentication:

- `GET /api/v1/candidates`: Get list of candidates
- `GET /api/v1/candidates/{candidate_id}`: Get candidate details
- `GET /api/v1/candidates/search`: Search candidates
- `GET /api/v1/candidates/{candidate_id}/education`: Get education history
- `GET /api/v1/candidates/{candidate_id}/exams`: Get exam history
- `GET /api/v1/exams`: Get list of exams
- `GET /api/v1/exams/{exam_id}`: Get exam details
- `GET /api/v1/schools`: Get list of schools
- `GET /api/v1/schools/{school_id}`: Get school details

### Admin Endpoints

These endpoints require administrator authentication:

- `POST /api/v1/admin/login`: Admin login
- `GET /api/v1/admin/dashboard`: Admin dashboard
- `POST /api/v1/admin/candidates`: Create new candidate
- `PUT /api/v1/admin/candidates/{candidate_id}`: Update candidate information
- `DELETE /api/v1/admin/candidates/{candidate_id}`: Delete candidate

## Authentication

The system uses a simple authentication approach:

- **Public access**: All candidate, exam, and school information can be accessed without authentication
- **Admin access**: Administrative functions require JWT authentication
- **Demo admin credentials**: 
  - Email: admin@example.com
  - Password: adminpassword123

## Documentation

API documentation is automatically generated using Swagger UI and is available at `/api/v1/docs` when the application is running.

## Development

### Database Migrations

Use Alembic to manage database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

### Data Synchronization with Neo4j

Data is automatically synchronized from PostgreSQL to Neo4j when performing CRUD operations through services. 