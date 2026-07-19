import app.db.models
from sqlmodel import Session
from app.database import engine
from app.categories.models import Category

categories = [
    {"name": "Electronics", "description": "Electronic devices and accessories"},
    {"name": "Clothing", "description": "Men and women clothing"},
    {"name": "Food & Beverages", "description": "Food and drinks"},
    {"name": "Books", "description": "Books and educational materials"},
    {"name": "Sports & Fitness", "description": "Sports and fitness equipment"},
    {"name": "Home & Living", "description": "Furniture and home accessories"},
    {"name": "Beauty & Personal Care", "description": "Beauty and grooming products"},
    {"name": "Automotive", "description": "Car parts and accessories"},
    {
        "name": "Health & Wellness",
        "description": "Health supplements and medical supplies",
    },
    {"name": "Toys & Games", "description": "Toys and games for all ages"},
]

with Session(engine) as session:
    for cat in categories:
        category = Category(**cat)
        session.add(category)
    session.commit()
    print("Categories seeded successfully")
