# Security and API Credentials

**Last Updated**: 2025-11-21

---

## ⚠️ IMPORTANT: Never Commit Credentials to Git

All API credentials are stored in files that are **gitignored** and will never be committed to version control.

---

## 📁 Where Credentials Are Stored

### Primary Credentials File (Recommended)

**File**: `config/api_credentials.json`
**Status**: ✅ Gitignored (see `.gitignore` line 38)
**Permissions**: `600` (read/write for owner only)

**How to use**:
```bash
# 1. Copy the template
cp config/api_credentials_template.json config/api_credentials.json

# 2. Edit with your actual credentials
nano config/api_credentials.json

# 3. Verify it's gitignored
git status  # Should NOT show api_credentials.json
```

### Alternative: Environment Variables

Set credentials as environment variables (useful for CI/CD):

```bash
# EPA AQS
export EPA_AQS_API_KEY="your_key"
export EPA_AQS_EMAIL="your@email.com"

# Census Bureau
export CENSUS_API_KEY="your_key"

# IPUMS NHGIS
export NHGIS_EMAIL="your@email.com"
export NHGIS_PASSWORD="your_password"
```

**Note**: Environment variables take precedence over config file.

---

## 🔑 Currently Configured Credentials

As of 2025-11-21, the following credentials are stored in `config/api_credentials.json`:

### ✅ EPA Air Quality System (AQS)
- **Status**: Active
- **Location**: `config/api_credentials.json` → `epa_aqs`
- **Fields**: `api_key`, `email`
- **Signup**: https://aqs.epa.gov/data/api/signup
- **Date Obtained**: 2025-11-21

### ✅ US Census Bureau API
- **Status**: Active
- **Location**: `config/api_credentials.json` → `census`
- **Fields**: `api_key`
- **Signup**: https://api.census.gov/data/key_signup.html
- **Date Obtained**: 2025-11-21

### ✅ IPUMS NHGIS
- **Status**: Active
- **Location**: `config/api_credentials.json` → `nhgis`
- **Fields**: `email`, `password`
- **Signup**: https://data2.nhgis.org/main
- **Date Obtained**: 2025-11-21
- **Note**: Requires account creation; manual extract definition

### ⏳ NASA Earthdata (Not Yet Configured)
- **Status**: Not configured
- **Required For**: ERA5 climate data, MODIS satellite data
- **Signup**: https://urs.earthdata.nasa.gov/users/new

### ⏳ NOAA NCDC (Not Yet Configured)
- **Status**: Not configured
- **Required For**: NOAA climate data
- **Signup**: https://www.ncdc.noaa.gov/cdo-web/token

---

## 🔒 Security Best Practices

### ✅ What We Do

1. **Gitignore credentials files**
   - `config/api_credentials.json` is in `.gitignore`
   - Never committed to version control

2. **Restrict file permissions**
   - Credentials file: `chmod 600` (owner read/write only)
   - No group or world access

3. **Provide template without credentials**
   - `config/api_credentials_template.json` is committed
   - Shows structure without exposing real keys

4. **Environment variable support**
   - Alternative to config file
   - Useful for CI/CD pipelines

5. **Documentation**
   - Clear instructions in README.md
   - This SECURITY.md file

### ⚠️ What You Should Do

1. **Never share credentials publicly**
   - Don't post API keys in GitHub issues
   - Don't include in screenshots
   - Don't commit to any repository

2. **Rotate credentials if exposed**
   - If accidentally committed, regenerate immediately
   - Most APIs allow key regeneration

3. **Use read-only keys when possible**
   - Most data APIs are read-only by default
   - Check API provider settings

4. **Keep credentials up to date**
   - Some APIs expire keys after inactivity
   - Check `date_obtained` field in config

---

## 🔧 How Downloaders Access Credentials

### Order of Precedence

Downloaders check for credentials in this order:

1. **Environment variables** (highest priority)
   ```python
   os.environ.get("EPA_AQS_API_KEY")
   ```

2. **Config file** (`config/api_credentials.json`)
   ```python
   with open("config/api_credentials.json") as f:
       creds = json.load(f)["epa_aqs"]["api_key"]
   ```

3. **Fail gracefully** with clear error message
   ```
   ERROR: EPA_AQS_API_KEY not found. Please configure credentials.
   See: https://aqs.epa.gov/data/api/signup
   ```

### Example: EPA AQS Downloader

```python
# src/downloaders/python/epa_aqs_downloader.py

def __init__(self):
    # Try environment variables first
    self.api_key = os.environ.get("EPA_AQS_API_KEY")
    self.email = os.environ.get("EPA_AQS_EMAIL")

    # Fall back to config file
    if not self.api_key:
        config_file = Path("config/api_credentials.json")
        if config_file.exists():
            with open(config_file) as f:
                creds = json.load(f).get("epa_aqs", {})
                self.api_key = creds.get("api_key")
                self.email = creds.get("email")

    # Warn if still not found
    if not self.api_key:
        logger.warning("EPA_AQS_API_KEY not set. Sign up at: https://aqs.epa.gov/data/api/signup")
```

---

## 🚨 If Credentials Are Accidentally Committed

If you accidentally commit credentials to git:

### Immediate Actions

1. **Regenerate the compromised credentials**
   - Go to the API provider and regenerate keys
   - Update `config/api_credentials.json` with new keys

2. **Remove from git history** (if in public repo)
   ```bash
   # Option 1: Use git filter-repo (recommended)
   pip install git-filter-repo
   git filter-repo --path config/api_credentials.json --invert-paths

   # Option 2: Use BFG Repo-Cleaner
   # Download from: https://rtyley.github.io/bfg-repo-cleaner/
   bfg --delete-files api_credentials.json
   ```

3. **Force push** (⚠️ WARNING: Coordinate with team)
   ```bash
   git push --force
   ```

4. **Notify collaborators**
   - Let them know to pull the cleaned history
   - Share new credentials securely

### Prevention for Future

- Set up pre-commit hooks to check for credentials
- Use tools like `git-secrets` or `truffleHog`
- Always review `git diff` before committing

---

## 📋 Checklist: Setting Up Credentials

- [ ] Copy template: `cp config/api_credentials_template.json config/api_credentials.json`
- [ ] Sign up for EPA AQS API: https://aqs.epa.gov/data/api/signup
- [ ] Add EPA credentials to `config/api_credentials.json`
- [ ] Sign up for Census API: https://api.census.gov/data/key_signup.html
- [ ] Add Census key to `config/api_credentials.json`
- [ ] Sign up for NHGIS: https://data2.nhgis.org/main
- [ ] Add NHGIS credentials to `config/api_credentials.json`
- [ ] Set file permissions: `chmod 600 config/api_credentials.json`
- [ ] Verify gitignored: `git status` (should not show credentials file)
- [ ] Test downloads work with credentials

---

## 📞 Support

If you have questions about API credentials or security:

1. **Check this file** for documentation
2. **Check README.md** for setup instructions
3. **Check API provider documentation** for credential management
4. **File an issue** (without posting credentials!)

---

**Last Updated**: 2025-11-21
**Configured Credentials**: EPA AQS ✅, Census ✅, NHGIS ✅
**Security Status**: All credentials properly gitignored and secured
