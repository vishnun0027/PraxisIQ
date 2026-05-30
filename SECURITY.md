# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in PraxisIQ, please report it responsibly. We take security seriously and appreciate your help in keeping our project safe.

### How to Report

**Please do NOT open a public issue for security vulnerabilities.**

Instead, email your findings to:
- vishnun0027@gmail.com

Include the following details:
- Description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact
- Suggested fix (if you have one)

### What to Expect

- We will acknowledge receipt of your report within 48 hours
- We will work on a fix and keep you updated on progress
- We will credit you for the discovery (unless you prefer anonymity)
- We will release a security update as soon as possible

## Security Best Practices

When using PraxisIQ:

- **Keep API Keys Safe** – Never commit Groq API keys or Telegram tokens to version control
- **Use HTTPS** – Always use secure connections
- **Update Dependencies** – Keep all packages up to date
- **Secure Your Database** – Use strong passwords and limit access to your PostgreSQL instance
- **Environment Variables** – Use `.env` files and never expose them in repositories

## Supported Versions

Security updates are provided for:
- Latest stable release

Please keep your installation updated to receive security patches.

## Disclaimer

While we strive to maintain security best practices, PraxisIQ is provided "as-is." Users are responsible for:
- Securing their own API keys and credentials
- Configuring their database securely
- Following deployment best practices

## Additional Resources

- [PostgreSQL Security](https://www.postgresql.org/docs/current/sql-syntax.html#SQL-SYNTAX-IDENTIFIERS)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

Thank you for helping keep PraxisIQ secure! 🛡️
