# PlanMyBudget API — Python Edition

FastAPI backend for PlanMyBudget, replacing the Node.js/Express version.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL via SQLAlchemy 2.0 (async)
- **Auth**: JWT with bcrypt, API keys, Google OAuth
- **Deployment**: Render / any ASGI server

## Setup

```bash
# Clone
cd planmybudget-api-python

# Create virtual env
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and secrets

# Run
uvicorn app.main:app --reload --port 4000
```

## API Docs

Once running, visit:
- Swagger UI: http://localhost:4000/docs
- ReDoc: http://localhost:4000/redoc

## Endpoints

### Auth
- `POST /api/users/register` — Register
- `POST /api/users/login` — Login
- `POST /api/logout` — Logout
- `POST /api/auth/send-otp` — Send OTP email
- `POST /api/auth/verify-otp` — Verify OTP & create account
- `POST /api/auth/google` — Google OAuth
- `PUT /api/change-password` — Change password

### Accounts
- `GET /api/accounts` — List accounts
- `POST /api/accounts` — Create account
- `PUT /api/accounts/:id` — Update account
- `DELETE /api/accounts/:id` — Delete account

### Transactions
- `GET /api/transactions` — List transactions
- `POST /api/transactions` — Create transaction
- `PUT /api/transactions/:id` — Update transaction
- `DELETE /api/transactions/:id` — Delete transaction

### Categories
- `GET /api/categories` — List categories
- `POST /api/categories` — Create category
- `PUT /api/categories/:id` — Update category
- `DELETE /api/categories/:id` — Delete category

### Budgets
- `GET /api/budgets` — List budgets
- `POST /api/budgets` — Create budget
- `PUT /api/budgets/:id` — Update budget
- `DELETE /api/budgets/:id` — Delete budget
- `GET /api/budgets/alerts` — Budget alerts
- `POST /api/budgets/send-alert` — Send alert

### Goals
- `GET /api/goals` — List goals
- `POST /api/goals` — Create goal
- `PUT /api/goals/:id` — Update goal
- `DELETE /api/goals/:id` — Delete goal

### Recurring
- `GET /api/recurring` — List recurring items
- `POST /api/recurring` — Create recurring item
- `PUT /api/recurring/:id` — Update recurring item
- `DELETE /api/recurring/:id` — Delete recurring item
- `POST /api/recurring/:id/process` — Process recurring

### Reminders
- `GET /api/reminders` — List reminders
- `POST /api/reminders` — Create reminder
- `PUT /api/reminders/:id` — Update reminder
- `DELETE /api/reminders/:id` — Delete reminder

### Profile & Settings
- `GET /api/profile` — Get profile
- `PUT /api/profile` — Update profile
- `GET /api/preferences` — Get preferences
- `PUT /api/preferences` — Update preferences
- `POST /api/api-keys` — Create API key
- `GET /api/api-keys` — List API keys
- `DELETE /api/api-keys/:id` — Delete API key

### Other
- `GET /api/status` — Status check
- `GET /api/health` — Health check
- `GET /api/exchange-rates` — Exchange rates

## Deploy on Render

1. Create a new **Web Service** on Render
2. Set **Runtime** to `Python 3`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`
6. Deploy!
