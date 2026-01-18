# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Notion Sidecar seriously. If you believe you have found a security vulnerability in this project, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

### How to Report

Please report security vulnerabilities by creating a [Draft Security Advisory](https://github.com/contact/security-advisory) or emailing the maintainers directly.

You should receive a response within 48 hours. Use the PGP key to encrypt sensitive information.

### API Keys and Secrets

This project involves integrations with Notion and Google Gemini APIs.
- **NEVER** commit your `.env` file or any file containing real API keys.
- Ensure `.env` is listed in `.gitignore`.
- If you accidentally commit a key, revoke it immediately from the respective provider.

## Security Best Practices

When using this agent:
- Run it in a trusted environment.
- Be aware that the agent has write access to your Notion page.
- Review the code before running it against critical production data.
