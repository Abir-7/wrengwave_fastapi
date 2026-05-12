import json
import os
from sqlalchemy import select
from app.database.models.base import Base
from app.database.models.car_data import CarData
from app.database.models.user import User
from app.database.models.enum import UserRole
from app.database.session import engine, SessionLocal
from app.utils.hash import get_password_hash
from app.database.models import * # ensures ALL models register with Base.metadata
from app.core.config import settings

async def seed_car_data():
    async with SessionLocal() as session:
        result = await session.execute(select(CarData).limit(1))
        if result.scalar_one_or_none():
            print("Car data already seeded.")
            return

        json_path = os.path.join("app", "preload_car_data", "car_data.json")
        if not os.path.exists(json_path):
            print(f"File not found: {json_path}")
            return

        try:
            with open(json_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON: {e}")
            return

        car_objects = [
            CarData(brand=brand, model=model)
            for brand, models in data.items()
            for model in models
        ]

        if car_objects:
            session.add_all(car_objects)
            await session.commit()
            print(f"Successfully seeded {len(car_objects)} car records.")
        else:
            print("No car data found in JSON.")


async def seed_admin():
    async with SessionLocal() as session:
        admin_email = settings.ADMIN_EMAIL
        admin_password = settings.ADMIN_PASSWORD

        result = await session.execute(select(User).where(User.email == admin_email))
        if result.scalar_one_or_none():
            print("Admin user already exists.")
            return

        admin_user = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            role=UserRole.admin,
            is_active=True
        )

        session.add(admin_user)
        await session.commit()
        print(f"Successfully seeded admin user: {admin_email}")


async def run_seeders():
    # Create all tables using the shared Base that all models are registered to
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables ensured.")

    await seed_car_data()
    await seed_admin()