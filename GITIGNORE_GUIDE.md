# .gitignore Configuration Guide

## Overview
This project uses three .gitignore files to properly exclude unnecessary and sensitive files from version control:

1. **Root `.gitignore`** - Project-wide exclusions
2. **`frontend/.gitignore`** - Next.js/React specific exclusions
3. **`backend/.gitignore`** - Django/Python specific exclusions

## File Structure

```
multivendor-ecommerce/
├── .gitignore                 # Root level
├── frontend/
│   └── .gitignore            # Frontend specific
└── backend/
    └── .gitignore            # Backend specific
```

## What's Ignored

### 🔒 Security & Sensitive Data
- `.env` files (all variants)
- `secrets.json`
- SSL certificates (`.pem`, `.key`, `.crt`)
- Database files (`*.sqlite3`, `*.db`)
- API keys and tokens

### 📦 Dependencies
- `node_modules/` (Frontend)
- `venv/`, `env/`, `ENV/` (Backend)
- Package lock files (optional)
- Python packages (`*.egg-info/`)

### 🏗️ Build Artifacts
- `.next/` (Next.js build)
- `out/` (Next.js export)
- `dist/`, `build/` (Build outputs)
- `__pycache__/` (Python bytecode)
- `*.pyc`, `*.pyo` (Compiled Python)

### 📁 Generated Files
- `staticfiles/` (Django static files)
- `media/` (User uploads)
- `coverage/` (Test coverage reports)
- `.pytest_cache/` (Pytest cache)

### 💻 IDE & Editor Files
- `.vscode/` (VS Code)
- `.idea/` (JetBrains IDEs)
- `*.swp`, `*.swo` (Vim)
- `*.sublime-*` (Sublime Text)

### 🖥️ OS Files
- `.DS_Store` (macOS)
- `Thumbs.db` (Windows)
- `desktop.ini` (Windows)

### 📝 Logs & Temporary Files
- `*.log` (All log files)
- `logs/` (Log directories)
- `*.tmp`, `*.temp` (Temporary files)
- `.cache/` (Cache directories)

## Important Files to Track

### ✅ Always Commit These:
- Source code (`.py`, `.tsx`, `.ts`, `.js`)
- Configuration templates (`.env.example`)
- Requirements files (`requirements.txt`, `package.json`)
- Migration files (`*/migrations/*.py`)
- Static assets (images, fonts in `/public`)
- Documentation (`.md` files)
- Docker files (`Dockerfile`, `docker-compose.yml`)
- CI/CD configs (`.github/workflows/`)

### ❌ Never Commit These:
- Environment variables (`.env`)
- Database files (`db.sqlite3`)
- User uploaded files (`media/`)
- Compiled files (`__pycache__/`, `.next/`)
- Dependencies (`node_modules/`, `venv/`)
- IDE settings (`.vscode/`, `.idea/`)
- Logs (`*.log`)
- Secrets and keys

## Environment Variables Setup

### Create `.env.example` Files

**Backend `.env.example`:**
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Payment Gateways
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
CHAPA_PUBLIC_KEY=CHASECK_TEST-xxxxx
CHAPA_SECRET_KEY=CHASECK_TEST-xxxxx

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
```

**Frontend `.env.example`:**
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Payment Keys (Public only)
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_xxxxx
NEXT_PUBLIC_CHAPA_PUBLIC_KEY=CHASECK_TEST-xxxxx

# App Configuration
NEXT_PUBLIC_APP_NAME=Multivendor Marketplace
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Setup Instructions

### For New Developers

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd multivendor-ecommerce
   ```

2. **Setup Backend:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your actual values
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   ```

3. **Setup Frontend:**
   ```bash
   cd frontend
   cp .env.example .env.local
   # Edit .env.local with your actual values
   npm install
   ```

4. **Verify .gitignore is working:**
   ```bash
   git status
   # Should NOT show .env, node_modules/, venv/, etc.
   ```

## Maintenance

### Adding New Patterns

When you need to ignore new file types:

1. **Identify the scope:**
   - Project-wide? → Add to root `.gitignore`
   - Frontend only? → Add to `frontend/.gitignore`
   - Backend only? → Add to `backend/.gitignore`

2. **Add the pattern:**
   ```bash
   echo "new-pattern/" >> .gitignore
   ```

3. **Test it:**
   ```bash
   git status
   # Verify the files are ignored
   ```

### Removing Tracked Files

If you accidentally committed files that should be ignored:

```bash
# Remove from Git but keep locally
git rm --cached <file-name>

# Remove directory from Git but keep locally
git rm -r --cached <directory-name>

# Commit the removal
git commit -m "Remove ignored files from tracking"
```

### Force Add Ignored Files (Rare Cases)

If you need to commit a file that's ignored:

```bash
git add -f <file-name>
```

## Common Issues

### Issue: `.env` file was committed
**Solution:**
```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
# Make sure .env is in .gitignore
```

### Issue: `node_modules/` is being tracked
**Solution:**
```bash
git rm -r --cached node_modules/
git commit -m "Remove node_modules from tracking"
```

### Issue: Media files are too large
**Solution:**
```bash
# Add to .gitignore
echo "media/*" >> backend/.gitignore
echo "!media/.gitkeep" >> backend/.gitignore

# Remove from tracking
git rm -r --cached backend/media/
git commit -m "Stop tracking media files"
```

## Best Practices

1. **Never commit sensitive data** - Always use environment variables
2. **Keep .gitignore updated** - Add patterns as project grows
3. **Use .env.example** - Document required environment variables
4. **Review before committing** - Check `git status` before `git add`
5. **Test .gitignore** - Verify files are ignored before committing
6. **Document exceptions** - If you must commit an ignored file, document why

## Security Checklist

Before pushing to remote repository:

- [ ] No `.env` files committed
- [ ] No `secrets.json` or API keys
- [ ] No database files (`*.sqlite3`)
- [ ] No SSL certificates or private keys
- [ ] No user uploaded files (unless intentional)
- [ ] No compiled binaries
- [ ] No IDE-specific settings with personal info

## Additional Resources

- [Git Documentation - gitignore](https://git-scm.com/docs/gitignore)
- [GitHub's gitignore templates](https://github.com/github/gitignore)
- [gitignore.io](https://www.toptal.com/developers/gitignore) - Generate .gitignore files

## Project-Specific Notes

### Media Files
The `media/` directory contains user uploads (product images, vendor documents, etc.). These are ignored by default. For production, use cloud storage (AWS S3, Cloudinary, etc.).

### Database
`db.sqlite3` is ignored. For production, use PostgreSQL or MySQL. Never commit database files.

### Migrations
Django migration files ARE tracked. They should be committed to ensure database schema consistency across environments.

### Static Files
`staticfiles/` (collected static files) is ignored. Run `python manage.py collectstatic` in production.

### Node Modules
`node_modules/` is ignored. Run `npm install` to install dependencies from `package.json`.
