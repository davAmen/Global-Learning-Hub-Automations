# Global Learning Hub - Deployment Guide

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │
│   (Vercel)      │     │   (Railway)     │
│   Next.js       │     │   FastAPI       │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Supabase      │
                        │   (PostgreSQL)  │
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   WasenderAPI   │
                        │   (WhatsApp)    │
                        └─────────────────┘
```

---

## Prerequisites

- GitHub repository
- Supabase project
- WasenderAPI account with connected WhatsApp session
- Railway account
- Vercel account

---

## Backend Deployment (Railway)

### 1. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select your repository
4. Set root directory to `backend`

### 2. Add Environment Variables

In Railway Dashboard → Variables, add:

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | `your-supabase-anon-key` |
| `WASENDER_API_KEY` | `your-wasender-api-key` |
| `WASENDER_BASE_URL` | `https://www.wasenderapi.com` |
| `ACTIVE_CHANNEL` | `whatsapp` |
| `BACKUP_CHANNEL` | `telegram` |
| `ADMIN_EMAIL` | `amenukudavid20@gmail.com` |
| `ADMIN_PHONE` | `+233548014157` |
| `JOB_HOUR` | `8` |
| `JOB_MINUTE` | `0` |
| `RATE_LIMIT_DELAY_SECONDS` | `6` |
| `TZ` | `GMT` |

### 3. Configure Webhook URL

After deployment, Railway gives you a URL like `https://your-app.railway.app`

In **WasenderAPI Dashboard → Sessions → Your Session → Webhooks**:
- Add webhook URL: `https://your-app.railway.app/webhooks/whatsapp`
- Enable events: `messages.received`, `messages.sent`, `groups.update`

### 4. Run Database Migrations

In Supabase Dashboard → SQL Editor, run the migration from `backend/supabase_migration.sql`

---

## Frontend Deployment (Vercel)

### 1. Import Project

1. Go to [vercel.com](https://vercel.com)
2. Import Project → Select GitHub repository
3. Set root directory to `frontend`
4. Framework: Next.js (auto-detected)

### 2. Add Environment Variables

In Vercel Dashboard → Settings → Environment Variables:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://your-railway-app.railway.app` |

### 3. Deploy

Vercel auto-deploys on push to main.

---

## GitHub Secrets (for CI/CD)

In GitHub Repository → Settings → Secrets → Actions, add:

| Secret | Description |
|--------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon key |
| `WASENDER_API_KEY` | WasenderAPI key |
| `ADMIN_EMAIL` | Admin email |
| `ADMIN_PHONE` | Admin phone |
| `RAILWAY_TOKEN` | Railway API token |
| `RAILWAY_SERVICE_BACKEND` | Railway service ID |
| `VERCEL_TOKEN` | Vercel access token |
| `VERCEL_ORG_ID` | Vercel organization ID |
| `VERCEL_PROJECT_ID` | Vercel project ID |

---

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
cp .env.example .env  # Fill in values
python -m uvicorn src.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/run-daily-job` | POST | Trigger daily reminders |
| `/reports/today` | GET | Today's engagement report |
| `/students` | GET | List all students |
| `/courses` | GET | List all courses |
| `/groups` | GET/POST | Manage WhatsApp groups |
| `/payments` | GET/POST | Manage payments |
| `/approvals` | GET/POST | Review approvals |
| `/webhooks/whatsapp` | POST | WasenderAPI webhooks |

---

## Key Flows

### IELTS Daily Reminder (5am GMT)
1. Scheduler triggers `send_ielts_reminder_now()`
2. Builds message with payment info
3. Creates approval record
4. Auto-approves (for testing) or waits for admin
4. Sends to announcement group via WasenderAPI

### Payment Verification
1. Student sends proof in proof group
2. Webhook receives `messages.received`
3. Creates payment record with `proof_url`
4. Creates approval for admin verification
5. Admin approves via `/approvals/{id}/review`
6. System adds student to class access group

---

## Monitoring

- **Logs**: Railway dashboard → Deployments → View logs
- **Health**: `GET https://your-app.railway.app/health`
- **Metrics**: Supabase dashboard → Database → Metrics

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| WhatsApp not sending | Check WasenderAPI session is connected |
| 429 rate limit | Increase `RATE_LIMIT_DELAY_SECONDS` to 6+ |
| Webhook not receiving | Verify webhook URL in WasenderAPI dashboard |
| DB connection failed | Check Supabase URL/key in Railway variables |
| Frontend can't reach API | Verify `NEXT_PUBLIC_API_URL` in Vercel |

---

## Support

For issues, check:
1. Railway logs
2. Supabase logs
3. WasenderAPI dashboard → Logs
4. Vercel function logs