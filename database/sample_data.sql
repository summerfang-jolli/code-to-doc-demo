-- Sample data for testing the code-to-documentation schema

-- Insert a sample project
INSERT INTO projects (id, name, description, repository_url, language, framework, documentation_style)
VALUES (
    '123e4567-e89b-12d3-a456-426614174000',
    'Sample Python API',
    'A sample Python FastAPI project for testing documentation generation',
    'https://github.com/example/sample-api',
    'python',
    'fastapi',
    'google'
);

-- Insert sample code files
INSERT INTO code_files (id, project_id, file_path, file_type, content, content_hash, file_size, line_count)
VALUES
(
    '223e4567-e89b-12d3-a456-426614174000',
    '123e4567-e89b-12d3-a456-426614174000',
    'src/main.py',
    'python',
    'from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Sample API", description="A sample API for testing")

class User(BaseModel):
    """User model for API requests and responses."""
    id: int
    name: str
    email: str

@app.get("/")
def read_root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Welcome to the Sample API"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    """Get a user by ID."""
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    return {"id": user_id, "name": "John Doe", "email": "john@example.com"}

@app.post("/users", response_model=User)
def create_user(user: User):
    """Create a new user."""
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)',
    'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
    1024,
    28
),
(
    '323e4567-e89b-12d3-a456-426614174000',
    '123e4567-e89b-12d3-a456-426614174000',
    'src/models.py',
    'python',
    'from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user model with common fields."""
    name: str
    email: EmailStr

class UserCreate(UserBase):
    """User creation model."""
    password: str

class User(UserBase):
    """User model for API responses."""
    id: int
    created_at: datetime
    is_active: bool = True

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    """User update model with optional fields."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None',
    'b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567',
    512,
    24
);

-- Insert sample code elements
INSERT INTO code_elements (file_id, element_type, name, full_name, signature, docstring, start_line, end_line, complexity_score, parameters, return_type, visibility)
VALUES
-- From main.py
(
    '223e4567-e89b-12d3-a456-426614174000',
    'class',
    'User',
    'main.User',
    'class User(BaseModel):',
    'User model for API requests and responses.',
    8,
    11,
    1.0,
    '[]'::jsonb,
    'User',
    'public'
),
(
    '223e4567-e89b-12d3-a456-426614174000',
    'function',
    'read_root',
    'main.read_root',
    'def read_root():',
    'Root endpoint that returns a welcome message.',
    13,
    15,
    1.0,
    '[]'::jsonb,
    'dict',
    'public'
),
(
    '223e4567-e89b-12d3-a456-426614174000',
    'function',
    'get_user',
    'main.get_user',
    'def get_user(user_id: int):',
    'Get a user by ID.',
    17,
    21,
    2.0,
    '[{"name": "user_id", "type": "int", "required": true}]'::jsonb,
    'dict',
    'public'
),
(
    '223e4567-e89b-12d3-a456-426614174000',
    'function',
    'create_user',
    'main.create_user',
    'def create_user(user: User):',
    'Create a new user.',
    23,
    25,
    1.0,
    '[{"name": "user", "type": "User", "required": true}]'::jsonb,
    'User',
    'public'
),
-- From models.py
(
    '323e4567-e89b-12d3-a456-426614174000',
    'class',
    'UserBase',
    'models.UserBase',
    'class UserBase(BaseModel):',
    'Base user model with common fields.',
    4,
    7,
    1.0,
    '[]'::jsonb,
    'UserBase',
    'public'
),
(
    '323e4567-e89b-12d3-a456-426614174000',
    'class',
    'UserCreate',
    'models.UserCreate',
    'class UserCreate(UserBase):',
    'User creation model.',
    9,
    11,
    1.0,
    '[]'::jsonb,
    'UserCreate',
    'public'
),
(
    '323e4567-e89b-12d3-a456-426614174000',
    'class',
    'User',
    'models.User',
    'class User(UserBase):',
    'User model for API responses.',
    13,
    19,
    1.0,
    '[]'::jsonb,
    'User',
    'public'
);

-- Insert sample documentation
INSERT INTO documentation (id, element_id, doc_type, title, content, generated_by, quality_score, completeness_score, clarity_score, accuracy_score, approved, word_count)
VALUES
(
    '423e4567-e89b-12d3-a456-426614174000',
    (SELECT id FROM code_elements WHERE name = 'read_root' AND file_id = '223e4567-e89b-12d3-a456-426614174000'),
    'api',
    'read_root - Root API Endpoint',
    '# read_root Function

## Overview
The `read_root` function serves as the root endpoint for the Sample API. It provides a simple welcome message to users accessing the base URL of the API.

## Signature
```python
def read_root() -> dict:
```

## Returns
- **Type**: `dict`
- **Content**: A dictionary containing a welcome message

## Example Response
```json
{
    "message": "Welcome to the Sample API"
}
```

## Usage
This endpoint is typically used for:
- Health checks
- API availability verification
- Welcome message display

## HTTP Method
- **GET** `/`

## Status Codes
- **200**: Successful response with welcome message',
    'gpt-4',
    0.85,
    0.9,
    0.8,
    0.85,
    true,
    156
),
(
    '523e4567-e89b-12d3-a456-426614174000',
    (SELECT id FROM code_elements WHERE name = 'get_user' AND file_id = '223e4567-e89b-12d3-a456-426614174000'),
    'api',
    'get_user - Retrieve User Information',
    '# get_user Function

## Overview
The `get_user` function retrieves user information based on the provided user ID. It includes input validation and error handling for invalid user IDs.

## Signature
```python
def get_user(user_id: int) -> dict:
```

## Parameters
- **user_id** (`int`): The unique identifier for the user to retrieve. Must be a positive integer.

## Returns
- **Type**: `dict`
- **Content**: User information including ID, name, and email

## Validation
- User ID must be greater than 0
- Invalid user IDs result in HTTP 400 error

## Example Response
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
}
```

## Error Responses
- **400 Bad Request**: When user_id <= 0
  ```json
  {
    "detail": "Invalid user ID"
  }
  ```

## HTTP Method
- **GET** `/users/{user_id}`',
    'gpt-4',
    0.92,
    0.95,
    0.9,
    0.9,
    true,
    203
);

-- Insert sample embeddings (using dummy vectors for testing)
INSERT INTO document_embeddings (documentation_id, chunk_index, chunk_text, embedding, embedding_model, token_count, char_count)
VALUES
(
    '423e4567-e89b-12d3-a456-426614174000',
    0,
    'The read_root function serves as the root endpoint for the Sample API. It provides a simple welcome message to users accessing the base URL of the API.',
    array_fill(0.1, ARRAY[1536])::vector,
    'text-embedding-ada-002',
    32,
    156
),
(
    '423e4567-e89b-12d3-a456-426614174000',
    1,
    'Returns a dictionary containing a welcome message. This endpoint is typically used for health checks, API availability verification, and welcome message display.',
    array_fill(0.2, ARRAY[1536])::vector,
    'text-embedding-ada-002',
    28,
    145
),
(
    '523e4567-e89b-12d3-a456-426614174000',
    0,
    'The get_user function retrieves user information based on the provided user ID. It includes input validation and error handling for invalid user IDs.',
    array_fill(0.3, ARRAY[1536])::vector,
    'text-embedding-ada-002',
    26,
    140
);

-- Insert sample code relationships
INSERT INTO code_relationships (source_element_id, target_element_id, relationship_type, strength)
VALUES
(
    (SELECT id FROM code_elements WHERE name = 'create_user' AND file_id = '223e4567-e89b-12d3-a456-426614174000'),
    (SELECT id FROM code_elements WHERE name = 'User' AND file_id = '223e4567-e89b-12d3-a456-426614174000'),
    'uses',
    1.0
),
(
    (SELECT id FROM code_elements WHERE name = 'User' AND file_id = '223e4567-e89b-12d3-a456-426614174000'),
    (SELECT id FROM code_elements WHERE name = 'UserBase' AND file_id = '323e4567-e89b-12d3-a456-426614174000'),
    'references',
    0.8
);

-- Insert sample search queries
INSERT INTO search_queries (project_id, query_text, query_type, results_found, response_time_ms, feedback_score)
VALUES
(
    '123e4567-e89b-12d3-a456-426614174000',
    'How to get user information?',
    'semantic',
    3,
    45,
    5
),
(
    '123e4567-e89b-12d3-a456-426614174000',
    'user endpoint documentation',
    'hybrid',
    2,
    38,
    4
),
(
    '123e4567-e89b-12d3-a456-426614174000',
    'API root welcome message',
    'semantic',
    1,
    22,
    5
);