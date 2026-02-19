"""
WhatsApp AI Bot with Google Gemini Vision

This FastAPI application integrates WhatsApp Business API with Google Gemini AI
to provide image analysis and question answering capabilities via WhatsApp.

Features:
- Image analysis using Gemini Vision
- Text question answering using Gemini
- Real-time webhook-based message processing
- Comprehensive error handling and logging

Author: Your Name
License: MIT
Repository: https://github.com/yourusername/whatsapp-gemini-bot
"""

import os
import httpx
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import base64

# Load environment variables from .env file
load_dotenv()

# Configure logging with emoji indicators for better readability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(title="WhatsApp Image Bot")

# ── ENV VARS ────────────────────────────────────────────────────────────────
WHATSAPP_TOKEN      = os.getenv("WHATSAPP_TOKEN")        # Meta access token
PHONE_NUMBER_ID     = os.getenv("PHONE_NUMBER_ID")       # Your WA phone number ID
VERIFY_TOKEN        = os.getenv("VERIFY_TOKEN", "mysecrettoken")  # Webhook verify token
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY")        # Google Gemini API key

WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

# ── STARTUP VALIDATION ──────────────────────────────────────────────────────
def validate_env_vars():
    """Check that all required environment variables are set"""
    missing = []
    
    if not WHATSAPP_TOKEN:
        missing.append("WHATSAPP_TOKEN")
    if not PHONE_NUMBER_ID:
        missing.append("PHONE_NUMBER_ID")
    if not GEMINI_API_KEY:
        logger.warning("⚠️ GEMINI_API_KEY not set - AI features will be disabled")
    
    if missing:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing)}")
        logger.error("💡 Please check your .env file and make sure these are set:")
        for var in missing:
            logger.error(f"   - {var}=your_value_here")
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    
    logger.info("✅ Environment variables validated")
    logger.info(f"📱 Phone Number ID: {PHONE_NUMBER_ID}")
    logger.info(f"🔑 WhatsApp Token: {WHATSAPP_TOKEN[:20]}...")
    logger.info(f"🤖 Gemini API: {'Connected' if GEMINI_API_KEY else 'Not configured'}")

# Validate on startup
validate_env_vars()


# ── HELPERS ──────────────────────────────────────────────────────────────────

async def download_whatsapp_media(media_id: str) -> bytes:
    """Download media from WhatsApp servers using the media ID."""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        # Step 1: Get the media URL
        meta_resp = await client.get(
            f"https://graph.facebook.com/v18.0/{media_id}",
            headers=headers
        )
        meta_resp.raise_for_status()
        media_url = meta_resp.json().get("url")

        # Step 2: Download the actual image bytes
        img_resp = await client.get(media_url, headers=headers)
        img_resp.raise_for_status()
        return img_resp.content


async def analyze_image(image_bytes: bytes) -> str:
    """
    Analyze the image using Google Gemini Vision.
    Replace this function with your own model/logic as needed.
    """
    if not GEMINI_API_KEY:
        return "✅ Image received! (Connect your AI model here to analyze it.)"

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
                headers={
                    "Content-Type": "application/json",
                },
                json={
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": "Describe what you see in this image in 2-3 sentences."
                                },
                                {
                                    "inline_data": {
                                        "mime_type": "image/jpeg",
                                        "data": b64_image
                                    }
                                }
                            ]
                        }
                    ]
                },
            )
            
            if response.status_code == 429:
                logger.warning("⚠️ Gemini rate limit hit")
                return "✅ Image received! (AI is temporarily busy - please try again in a moment)"
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the text from Gemini's response
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API error: {e}")
        if e.response.status_code == 429:
            return "✅ Image received! (AI is temporarily busy - please try again in a moment)"
        logger.error(f"Response body: {e.response.text}")
        return f"✅ Image received! (Analysis temporarily unavailable: {e.response.status_code})"
    except Exception as e:
        logger.error(f"Unexpected error in analyze_image: {e}")
        return "✅ Image received! (Analysis encountered an error)"


async def answer_question(question: str) -> str:
    """
    Answer text questions using Google Gemini.
    """
    if not GEMINI_API_KEY:
        return "🤖 AI is not configured. Please set up GEMINI_API_KEY."

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
                headers={
                    "Content-Type": "application/json",
                },
                json={
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": question
                                }
                            ]
                        }
                    ]
                },
            )
            
            if response.status_code == 429:
                logger.warning("⚠️ Gemini rate limit hit")
                return "⏳ I'm a bit busy right now. Please try again in a moment!"
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the text from Gemini's response
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API error: {e}")
        if e.response.status_code == 429:
            return "⏳ I'm a bit busy right now. Please try again in a moment!"
        logger.error(f"Response body: {e.response.text}")
        return f"⚠️ Sorry, I encountered an error. Please try again later."
    except Exception as e:
        logger.error(f"Unexpected error in answer_question: {e}")
        return "⚠️ Sorry, something went wrong. Please try again."


async def send_whatsapp_message(to: str, text: str) -> dict:
    """Send a text message back to a WhatsApp user."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(WHATSAPP_API_URL, headers=headers, json=payload)
        
        # Log the response for debugging
        if resp.status_code != 200:
            logger.error(f"❌ WhatsApp API error: {resp.status_code} - {resp.text}")
            resp.raise_for_status()
        
        logger.info(f"✅ Message sent to {to}: {resp.json()}")
        return resp.json()


async def send_whatsapp_typing(to: str):
    """Send a typing indicator to improve UX while processing."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": "⏳ Analyzing your image, please wait..."},
    }
    async with httpx.AsyncClient() as client:
        await client.post(WHATSAPP_API_URL, headers=headers, json=payload)


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    WhatsApp webhook verification.
    Meta calls this once when you register your webhook URL.
    """
    params = dict(request.query_params)
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.info(f"Verification request: mode={mode}, token={token}, challenge={challenge}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified!")
        return PlainTextResponse(content=challenge)
    
    logger.error(f"Verification failed - Expected token: {VERIFY_TOKEN}, Got: {token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Receive incoming WhatsApp messages.
    Handles image messages and responds with analysis.
    """
    body = await request.json()
    logger.info(f"📩 Raw webhook payload: {body}")

    try:
        # Check if this is a status update (not a message)
        if "entry" not in body:
            logger.warning("⚠️ No 'entry' field in webhook payload")
            return {"status": "ignored - no entry"}

        entry   = body["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]
        
        # Log what type of webhook this is
        logger.info(f"📋 Webhook value keys: {value.keys()}")
        
        messages = value.get("messages")

        if not messages:
            logger.info("ℹ️ Webhook received but no messages (likely a status update)")
            return {"status": "no messages"}

        message = messages[0]
        from_number = message["from"]
        msg_type    = message.get("type")
        
        logger.info(f"📨 Message type: {msg_type} from {from_number}")

        # ── Handle IMAGE messages ──────────────────────────────────────────
        if msg_type == "image":
            # Meta sends 'id' not 'media_id' in the webhook
            media_id = message["image"].get("id") or message["image"].get("media_id")
            caption  = message["image"].get("caption", "")

            logger.info(f"🖼️ Image received from {from_number}, media_id={media_id}")

            # Download + analyze the image
            try:
                image_bytes = await download_whatsapp_media(media_id)
                logger.info(f"✅ Downloaded image: {len(image_bytes)} bytes")
                
                analysis    = await analyze_image(image_bytes)
                logger.info(f"🤖 Analysis complete: {analysis[:100]}...")

                reply = f"🖼️ *Image Analysis*\n\n{analysis}"
                if caption:
                    reply = f"📝 Caption: _{caption}_\n\n" + reply

                try:
                    await send_whatsapp_message(from_number, reply)
                    logger.info(f"✅ Reply sent successfully")
                except httpx.HTTPStatusError as e:
                    logger.error(f"❌ Failed to send reply: {e}")
                    # Don't crash - just log the error
                    if "131030" in str(e.response.text):
                        logger.error("💡 TIP: Add this phone number to your allowed list in Meta Dashboard!")
                
            except Exception as e:
                logger.error(f"❌ Error processing image: {str(e)}")
                try:
                    await send_whatsapp_message(
                        from_number,
                        f"⚠️ Sorry, I encountered an error processing your image: {str(e)}"
                    )
                except:
                    logger.error("❌ Could not send error message to user")
                    pass

        # ── Handle TEXT messages ───────────────────────────────────────────
        elif msg_type == "text":
            text = message["text"]["body"]
            logger.info(f"💬 Text from {from_number}: {text}")
            
            # Use Gemini to answer the question
            try:
                answer = await answer_question(text)
                await send_whatsapp_message(from_number, answer)
                logger.info(f"✅ Answer sent successfully")
            except Exception as e:
                logger.error(f"❌ Error answering question: {e}")
                try:
                    await send_whatsapp_message(
                        from_number,
                        "⚠️ Sorry, I couldn't process your question. Please try again!"
                    )
                except:
                    logger.error("❌ Could not send error message to user")
                    pass

        # ── Handle unsupported types ───────────────────────────────────────
        else:
            logger.info(f"⚠️ Unsupported message type: {msg_type}")
            await send_whatsapp_message(
                from_number,
                "⚠️ Sorry, I only support image messages right now."
            )

    except (KeyError, IndexError) as e:
        logger.error(f"❌ Unexpected webhook structure: {e}")
        logger.error(f"Full body: {body}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)

    # Always return 200 to WhatsApp so it doesn't retry
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    return {
        "status": "running",
        "phone_number_id": PHONE_NUMBER_ID,
        "gemini_connected": bool(GEMINI_API_KEY),
    }


@app.get("/debug")
async def debug_config():
    """Debug endpoint to verify configuration"""
    return {
        "whatsapp_token_set": bool(WHATSAPP_TOKEN),
        "whatsapp_token_preview": WHATSAPP_TOKEN[:20] + "..." if WHATSAPP_TOKEN else None,
        "phone_number_id": PHONE_NUMBER_ID,
        "verify_token": VERIFY_TOKEN,
        "gemini_key_set": bool(GEMINI_API_KEY),
    }
