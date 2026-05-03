#windows
python -m venv venv
venv\Scripts\activate

#linux
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

 py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

alembic revision --autogenerate -m "create users table"
alembic upgrade head

