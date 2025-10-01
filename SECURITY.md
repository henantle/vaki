# Security Measures

## Token Sanitization

VÄKI implements comprehensive token sanitization to prevent credential leakage.

### Automatic Token Masking

All sensitive tokens are automatically masked in:
- ✅ Error messages
- ✅ Exception traces
- ✅ Subprocess output
- ✅ Git command output
- ✅ Log messages
- ✅ URLs

### How It Works

```python
from src.security import register_token, sanitize

# Register sensitive tokens at startup
register_token(github_token)
register_token(openai_api_key)

# All output is automatically sanitized
print(sanitize(error_message))  # Tokens masked as ghp_**** or sk-****
```

### Patterns Masked

1. **GitHub Tokens**: `ghp_*`, `gho_*`, `ghu_*`, `ghs_*`, `ghr_*`
2. **OpenAI Keys**: `sk-*`
3. **URLs with embedded tokens**: `https://token@github.com/...` → `https://***@github.com/...`
4. **Query parameters**: `?token=xxx` → `?token=****`
5. **Authorization headers**: `Bearer xxx` → `Bearer ****`

### Security Best Practices

1. **Never log raw URLs** - Always use `sanitize_url()`
2. **Never print subprocess output directly** - Use `sanitize()`
3. **Never store tokens in code** - Use environment variables
4. **Always catch and sanitize exceptions** - Use `sanitize(str(e))`

### Example

```python
# ❌ UNSAFE
print(f"Error: {error}")
print(f"URL: {git_url}")

# ✅ SAFE
print(f"Error: {sanitize(str(error))}")
print(f"URL: {sanitize_url(git_url)}")
```

## Secure Token Handling

### Environment Variables

All tokens must be stored in `.env`:

```bash
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk-your_key_here
```

**Never commit `.env` to version control.**

### Token Registration

Tokens are registered at startup in `main.py`:

```python
from src.security import register_token

register_token(github_token)
register_token(openai_api_key)
```

Once registered, all output is automatically sanitized.

## Git Operations

### Remote URLs

Git remote URLs may contain embedded tokens. All git command output is sanitized.

### Push/Pull Operations

GitHub authentication is handled via environment variables, not URL-embedded tokens.

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT open a public issue**
2. Email: [your-security-email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact

## Security Checklist

When contributing code:

- [ ] All subprocess output is sanitized
- [ ] All exception messages are sanitized
- [ ] No tokens in logs or print statements
- [ ] URLs are sanitized before display
- [ ] Error messages don't leak credentials
- [ ] No tokens in git commit messages
- [ ] `.env` is in `.gitignore`
