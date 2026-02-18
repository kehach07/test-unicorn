from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import logging
from datetime import datetime

# ==============================
# App Initialization
# ==============================
app = FastAPI(title="SecureAI Prompt Injection Validator")

# Enable CORS (Required for Render / external testers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# Logging Setup
# ==============================
logging.basicConfig(
    filename="security.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ==============================
# Request Model
# ==============================
class SecurityRequest(BaseModel):
    userId: str
    input: str
    category: str


# ==============================
# Root Health Endpoint
# ==============================
@app.get("/")
def root():
    return {"status": "SecureAI Validator is running"}


# ==============================
# Prompt Injection Patterns
# ==============================
OVERRIDE_PATTERNS = [
    r"ignore (all|previous|system) instructions",
    r"override (system|rules)",
    r"disregard previous instructions",
    r"you are now",
    r"act as (admin|developer|system|root)",
]

SYSTEM_EXTRACTION_PATTERNS = [
    r"show (me )?system prompt",
    r"reveal system instructions",
    r"what is your system message",
    r"print hidden prompt",
    r"expose hidden instructions",
]

ROLE_MANIPULATION_PATTERNS = [
    r"as an admin",
    r"as a developer",
    r"i am the system",
    r"pretend you are root",
    r"grant me full access",
]

SUSPICIOUS_PATTERNS = (
    OVERRIDE_PATTERNS +
    SYSTEM_EXTRACTION_PATTERNS +
    ROLE_MANIPULATION_PATTERNS
)


# ==============================
# Helper Functions
# ==============================
def detect_prompt_injection(text: str):
    text_lower = text.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text_lower):
            return True, pattern
    return False, None


def sanitize_output(text: str):
    # Basic XSS protection
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text


def log_event(user_id, input_text, blocked, reason):
    logging.info({
        "timestamp": str(datetime.utcnow()),
        "userId": user_id,
        "blocked": blocked,
        "reason": reason,
        "input_sample": input_text[:200]
    })


# ==============================
# Validation Endpoint
# ==============================
@app.post("/validate")
async def validate_security(request: SecurityRequest):

    # Category validation
    if request.category != "Prompt Injection":
        raise HTTPException(
            status_code=400,
            detail="Invalid category"
        )

    try:
        # Detect injection
        is_blocked, pattern = detect_prompt_injection(request.input)

        if is_blocked:
            reason = "Prompt injection attempt detected"
            confidence = 0.96

            log_event(request.userId, request.input, True, reason)

            return {
                "blocked": True,
                "reason": reason,
                "sanitizedOutput": "",
                "confidence": confidence
            }

        # Legitimate input
        sanitized = sanitize_output(request.input)
        confidence = 0.92

        log_event(request.userId, request.input, False, "Passed validation")

        return {
            "blocked": False,
            "reason": "Input passed all security checks",
            "sanitizedOutput": sanitized,
            "confidence": confidence
        }

    except Exception:
        # Do NOT expose system details
        raise HTTPException(
            status_code=400,
            detail="Validation error"
        )
