# Security Policy

## Reporting a Vulnerability

The Legion project team is committed to addressing security vulnerabilities promptly and responsibly. If you discover a security vulnerability, please report it using one of the following methods:

### Responsible Disclosure

To report a security vulnerability responsibly:

1. **DO NOT** create a public GitHub issue for the vulnerability
2. Email the security team with details at: **security-report@legion.dev**
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### Response Timeline

We commit to:
- Acknowledging vulnerability reports within 48 hours
- Providing initial assessment within 1 week
- Releasing a security patch within 2 weeks (or explaining timeline)
- Crediting the researcher (if desired)

## Supported Versions

Security updates are provided for:

| Version | Supported          | EOL Date       |
|---------|--------------------|----------------|
| 2.2.x   | ✅ Yes             | TBD            |
| 2.1.x   | ⚠️ Limited         | 3 months       |
| < 2.1   | ❌ No              | Immediate      |

## Security Best Practices

### For Users
- Keep Legion updated to the latest version
- Review environment variables and configuration
- Use strong, unique credentials for database connections
- Enable branch protection on production deployments
- Monitor logs for suspicious activity

### For Contributors
- Never commit sensitive credentials or API keys
- Use environment variables for all sensitive data
- Review security implications before submitting PRs
- Follow OWASP guidelines for authentication and authorization
- Use type hints and input validation

## Security Scanning

The Legion project implements:
- Automated dependency scanning
- Static application security testing (SAST)
- Branch protection and code review requirements
- Regular security audits

## Known Issues

No known security issues at this time.

## Acknowledgments

We appreciate the security research community's efforts to keep Legion secure.

---

*Last Updated: 2024*
*For questions, contact: security@legion.dev*
