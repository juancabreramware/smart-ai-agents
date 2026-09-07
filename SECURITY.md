# Security

## Secrets

Do not commit API keys, `.env` files, credentials, private certificates, or service-account material. Use the provided `.env.example` as a template and keep real values local.

## Generated capabilities

Chapter 3 stores learned runtime capability JSON under `capabilities/registry/`. These generated files are ignored by Git. Treat learned artifacts as untrusted until they pass the validation and promotion controls described in the chapter.

## Live-site experiments

The controlled benchmark is the recommended reproducible environment. If you use the optional live-web path, respect site terms, robots policies, rate limits, authentication boundaries, and applicable law.

## Reporting a security issue

Please do not publish credentials or sensitive exploit details in a public issue. Contact the repository owner privately through the contact methods available on the GitHub profile.
