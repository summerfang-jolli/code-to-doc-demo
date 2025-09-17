"""
Sample FastAPI application for testing the Code Analyzer Agent.
This file demonstrates various Python constructs that our analyzer should capture.
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="Sample API",
    description="A sample API for testing code documentation generation",
    version="1.0.0"
)

class User(BaseModel):
    """User model for API requests and responses."""
    id: Optional[int] = None
    name: str
    email: str
    created_at: Optional[datetime] = None
    is_active: bool = True

class UserCreate(BaseModel):
    """Model for creating new users."""
    name: str
    email: str

# In-memory storage (for demo purposes)
users_db: List[User] = []
_user_counter = 0

def get_next_user_id() -> int:
    """Generate next user ID."""
    global _user_counter
    _user_counter += 1
    return _user_counter

def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise
    """
    return "@" in email and "." in email.split("@")[1]

async def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Retrieve user by ID from database.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        User object if found, None otherwise

    Raises:
        ValueError: If user_id is invalid
    """
    if user_id <= 0:
        raise ValueError("User ID must be positive")

    # Simulate async database lookup
    await asyncio.sleep(0.1)

    for user in users_db:
        if user.id == user_id:
            return user
    return None

class UserService:
    """Service class for user-related operations."""

    def __init__(self, db: List[User] = None):
        """Initialize user service."""
        self.db = db or users_db

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user object

        Raises:
            ValueError: If email is invalid
        """
        if not validate_email(user_data.email):
            raise ValueError("Invalid email format")

        # Check if email already exists
        if any(u.email == user_data.email for u in self.db):
            raise ValueError("Email already exists")

        user = User(
            id=get_next_user_id(),
            name=user_data.name,
            email=user_data.email,
            created_at=datetime.now()
        )

        self.db.append(user)
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return next((u for u in self.db if u.id == user_id), None)

    def list_users(self, active_only: bool = True) -> List[User]:
        """
        List all users.

        Args:
            active_only: If True, return only active users

        Returns:
            List of users
        """
        if active_only:
            return [u for u in self.db if u.is_active]
        return self.db.copy()

    @staticmethod
    def validate_user_data(user_data: UserCreate) -> bool:
        """Validate user creation data."""
        return bool(user_data.name and user_data.email)

# Initialize service
user_service = UserService()

@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "message": "Welcome to the Sample API",
        "version": "1.0.0",
        "endpoints": ["/users", "/users/{user_id}"]
    }

@app.get("/users", response_model=List[User])
async def list_users(active_only: bool = True):
    """
    List all users.

    Args:
        active_only: Filter for active users only

    Returns:
        List of users
    """
    return user_service.list_users(active_only=active_only)

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """
    Get a specific user by ID.

    Args:
        user_id: User ID to retrieve

    Returns:
        User object

    Raises:
        HTTPException: If user not found
    """
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users", response_model=User)
async def create_user(user_data: UserCreate):
    """
    Create a new user.

    Args:
        user_data: User creation data

    Returns:
        Created user object

    Raises:
        HTTPException: If creation fails
    """
    try:
        user = user_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """
    Soft delete a user (mark as inactive).

    Args:
        user_id: ID of user to delete

    Returns:
        Success message

    Raises:
        HTTPException: If user not found
    """
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    return {"message": f"User {user_id} deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)