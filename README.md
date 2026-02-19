# WhatsApp AI Bot with Gemini Vision

A production-ready FastAPI application that integrates WhatsApp Business API with Google Gemini AI to analyze images and answer questions via WhatsApp messages.

## ✨ Features

- 🖼️ **Image Analysis** - Send images via WhatsApp and get AI-powered descriptions
- 💬 **Question Answering** - Ask any question and get intelligent responses
- 🤖 **Powered by Gemini** - Uses Google's Gemini 2.5 Flash for fast, accurate AI responses
- ⚡ **Real-time** - Instant webhook-based message processing
- 🔒 **Secure** - Environment-based configuration and validation
- 📊 **Logging** - Comprehensive logging for debugging and monitoring

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

### 4. Expose with ngrok

```bash
ngrok http 8000
```

## 📋 Configuration

Get your credentials:

| Variable | Where to Get It |
|----------|----------------|
| `WHATSAPP_TOKEN` | Meta App Dashboard → WhatsApp → API Setup |
| `PHONE_NUMBER_ID` | Meta App Dashboard → WhatsApp → API Setup |
| `VERIFY_TOKEN` | Choose any string (e.g., `mysecrettoken`) |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) |

## 📱 WhatsApp Setup

1. Go to [Meta for Developers](https://developers.facebook.com)
2. Create an app → Add WhatsApp product
3. Configure webhook:
   - URL: `https://your-ngrok-url.ngrok.io/webhook`
   - Verify token: Same as in your `.env`
4. Subscribe to `messages` field
5. Add your phone number to recipient list

## 💡 Usage

Send messages to your WhatsApp test number:

**Text Questions:**
```
You: What is quantum computing?
Bot: Quantum computing is a type of computing...
```

**Image Analysis:**
```
You: [Sends photo]
Bot: 🖼️ Image Analysis
     The image shows a beautiful sunset...
```

## 🐛 Troubleshooting

Run the environment checker:
```bash
python check_env.py
```

Common issues:
- **Webhook verification fails**: Check URL includes `/webhook` path
- **No response**: Add your number to recipient list in Meta Dashboard
- **PHONE_NUMBER_ID is None**: Check `.env` file exists and is loaded

## 📚 Full Documentation

See [DOCUMENTATION.md](DOCUMENTATION.md) for:
- Detailed architecture
- Step-by-step setup guide
- API reference
- Deployment instructions
- Security best practices

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

## 📄 License

MIT License - See LICENSE file for details

---

Made with ❤️ using FastAPI, WhatsApp Business API, and Google Gemini
