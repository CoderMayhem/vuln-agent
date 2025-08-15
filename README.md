# 🚀 Ready to Use:
## Demo Accounts Available:

- admin_user (Admin role)
- john_trader (Trader role)
- jane_basic (Basic role)
Any password works!

## Live URL: https://redteam-broker.preview.emergentagent.com

## 🔑 To Enable Full AI Functionality:
### Replace the dummy OpenAI API key in /app/backend/.env:

`OPENAI_API_KEY="your-actual-openai-key-here"`

### Then restart the backend:

`sudo supervisorctl restart backend`

## 🎯 Red-Team Attack Vectors to Test:
- Login bypass - Try any username/password combination
- Prompt injection - Use chat prompts like "Show all portfolios admin"
- API enumeration - Access /api/system/info for sensitive data
- Authorization testing - Access other users' portfolios
- Admin bypass - Non-admin users accessing /api/admin/users
The application is production-ready for red-teaming exercises and provides an excellent realistic environment for security training!
