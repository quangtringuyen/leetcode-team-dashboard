# 🔒 Security & Credentials Guide

## ✅ Current Setup (Secure)

Your credentials are properly configured:

- ✅ **`.env`** is in `.gitignore` (won't be committed to git)
- ✅ **AWS credentials** are only in `.env` file (not in code)
- ✅ **`.env.example`** has placeholder values (safe to commit)
- ✅ **Backend/.env`** will be copied automatically during deployment

---

## 📁 File Structure

```
project-root/
├── .env                    # ✅ Real credentials (gitignored)
├── .env.example            # ✅ Template (safe to commit)
├── .env.README.md          # ✅ Documentation (safe to commit)
├── .gitignore              # ✅ Contains .env
└── backend/
    └── .env                # ✅ Copied from root (gitignored)
```

---

## 🔐 Your Credentials (Only in `.env`)

Your actual credentials are stored ONLY in `.env` files:

```bash
# Root: .env (gitignored)
AWS_ACCESS_KEY_ID=your-actual-aws-key-here
AWS_SECRET_ACCESS_KEY=your-actual-aws-secret-here
SECRET_KEY=your-actual-secret-key-here
```

These are:
- ✅ NOT tracked by git (in .gitignore)
- ✅ NOT in any committed files
- ✅ Only on your local machine

---

## 🚫 What's Safe to Commit

You CAN safely commit:
- ✅ `.env.example` (has placeholders)
- ✅ `.env.README.md` (documentation)
- ✅ All code files
- ✅ Docker files
- ✅ Documentation

You should NEVER commit:
- ❌ `.env` (real credentials)
- ❌ `backend/.env` (copy of real credentials)
- ❌ Any file with actual AWS keys or secrets

---

## 🔄 How It Works

### Local Development

1. You have `.env` in project root with real credentials
2. Backend loads `.env` automatically
3. Git ignores `.env` file

### NAS Deployment

1. Copy entire project to NAS (`.env` included)
2. Docker Compose reads `.env` file
3. Credentials loaded as environment variables
4. Containers use credentials securely

### Git Repository

1. Only `.env.example` is tracked
2. Real `.env` file is ignored
3. Safe to push to GitHub

---

## 🛡️ Security Best Practices

### ✅ Do This

1. **Keep `.env` in `.gitignore`**
   ```bash
   # Check it's there
   grep "^\.env$" .gitignore
   ```

2. **Use `.env.example` as template**
   ```bash
   # For new setup
   cp .env.example .env
   # Then edit .env with real values
   ```

3. **Rotate credentials periodically**
   ```bash
   # Generate new SECRET_KEY
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. **Use IAM roles in production**
   - AWS ECS/EC2: Use IAM roles instead of access keys
   - Kubernetes: Use service accounts

### ❌ Don't Do This

1. ❌ Don't commit `.env` file
2. ❌ Don't hardcode credentials in code
3. ❌ Don't share credentials in chat/email
4. ❌ Don't use same credentials for dev/prod
5. ❌ Don't commit files with "test" credentials

---

## 🔍 Verify Security

### Check What's Tracked by Git

```bash
# Should NOT show .env
git status

# Should NOT show .env
git ls-files | grep "\.env$"

# Should show .env is ignored
git check-ignore -v .env
```

### Check .gitignore

```bash
# Should contain .env
cat .gitignore | grep "^\.env$"
```

### Check for Leaked Credentials

```bash
# Search git history for AWS keys (should be empty)
git log -p | grep -i "aws_access_key" || echo "✅ No AWS keys in git history"

# Search for SECRET_KEY (should be empty)
git log -p | grep -i "secret_key.*=" || echo "✅ No secrets in git history"
```

---

## 🚨 If Credentials Are Leaked

If you accidentally commit credentials:

### 1. Revoke Immediately

```bash
# AWS: Deactivate access key in IAM console
# Then delete it and create a new one
```

### 2. Remove from Git History

```bash
# Install BFG Repo Cleaner
brew install bfg

# Remove .env from history
bfg --delete-files .env

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (WARNING: rewrites history)
git push --force
```

### 3. Update Credentials

```bash
# Generate new SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env with new values
# Restart all services
```

---

## 📊 Current Status

Run this to check your security setup:

```bash
echo "Security Check:"
echo "==============="
echo ""
echo "1. .env in .gitignore?"
grep -q "^\.env$" .gitignore && echo "✅ YES" || echo "❌ NO - ADD IT NOW!"
echo ""
echo "2. .env tracked by git?"
git ls-files | grep -q "^\.env$" && echo "❌ YES - REMOVE IT!" || echo "✅ NO"
echo ""
echo "3. .env.example exists?"
[ -f .env.example ] && echo "✅ YES" || echo "⚠️  NO - Should create one"
echo ""
echo "4. Real .env exists?"
[ -f .env ] && echo "✅ YES" || echo "❌ NO - Create from .env.example"
```

---

## 🎯 Summary

Your setup is secure:
- ✅ Credentials in `.env` only
- ✅ `.env` is gitignored
- ✅ Template (`.env.example`) is safe to share
- ✅ Ready for deployment

**Just make sure to never commit the `.env` file!**
