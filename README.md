py -m uvicorn app.main:app --reload

alembic revision --autogenerate -m "create users table"
alembic upgrade head