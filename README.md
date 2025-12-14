# Urban Tree REST API

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Create superuser:
```bash
python manage.py createsuperuser
```

4. Run the development server:
```bash
python manage.py runserver
```

## API Endpoints

- POST `/api/auth/register/` - Register new user
- POST `/api/auth/login/` - Login
- POST `/api/auth/logout/` - Logout
- GET `/api/profile/me/` - Get current user profile
- PATCH `/api/profile/update-role/<user_id>/` - Update user role (admin only)
- GET `/api/users/` - List all users
- GET `/api/profiles/` - List all profiles

## Testing

Run tests:
```bash
python manage.py test
```

## Admin Panel

Access at: http://localhost:8000/admin/



-- Login to postgres as postgres user
psql -U postgres

CREATE DATABASE urbantree;
-- we need a user in a database as well because we can provide granular 
-- permissions to each user of the database as per the needs of the application.
CREATE USER urbantree;
ALTER USER urbantree WITH PASSWORD 'urbantree';

-- The application does not require sophisticated database design 
-- neither does the class needs ask for a complex 
-- database design

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tree_schema TO urbantree;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO urbantree;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA tree_schema TO urbantree;
-- GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA tree_schema TO urbantree;

GRANT ALL PRIVILEGES ON DATABASE urbantree TO urbantree;
-- switch user
SET ROLE urbantree;
-- check if able to execute commands as urbantree user
\dt 

-- # Example command to run with production settings
export DJANGO_ENV=production
python manage.py runserver --settings=urbantree.settings

python manage.py migrate

python manage.py makemigrations dbmodels

pip install -r requirements.txt

# Create migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver

joyw
joy_super

supabase password joy_super
