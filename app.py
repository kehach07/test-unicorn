from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import re
import logging
from datetime import datetime
# from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SecureAI Prompt Injection Validator")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all (for testing)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app = FastAPI(title="SecureAI Prompt Injection Validator")

# -------- Logging Setup --------
logging.basicConfig(
    filename="security.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------- Request Model --------
class SecurityRequest(BaseModel):
    userId: str
    input: str
    category: str


# -------- Injection Patterns --------
OVERRIDE_PATTERNS = [
    r"ignore (all|previous|system) instructions",
    r"override (system|rules)",
    r"you are now",
    r"act as (admin|developer|system)",
]

SYSTEM_EXTRACTION_PATTERNS = [
    r"show (me )?system prompt",
    r"reveal system instructions",
    r"what is your system message",
    r"print hidden prompt",
]

ROLE_MANIPULATION_PATTERNS = [
    r"as an admin",
    r"as a developer",
    r"i am the system",
    r"pretend you are root",
]

SUSPICIOUS_PATTERNS = (
    OVERRIDE_PATTERNS +
    SYSTEM_EXTRACTION_PATTERNS +
    ROLE_MANIPULATION_PATTERNS
)


# -------- Helper Functions --------
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
        "input": input_text[:200]
    })


# -------- API Endpoint --------
@app.post("/validate")
async def validate_security(request: SecurityRequest):

    # Validate category
    if request.category != "Prompt Injection":
        raise HTTPException(
            status_code=400,
            detail="Invalid category"
        )

    try:
        is_blocked, pattern = detect_prompt_injection(request.input)

        if is_blocked:
            reason = "Prompt injection attempt detected"
            confidence = 0.95

            log_event(request.userId, request.input, True, reason)

            return {
                "blocked": True,
                "reason": reason,
                "sanitizedOutput": "",
                "confidence": confidence
            }

        # Legitimate input
        sanitized = sanitize_output(request.input)
        confidence = 0.90

        log_event(request.userId, request.input, False, "Passed validation")

        return {
            "blocked": False,
            "reason": "Input passed all security checks",
            "sanitizedOutput": sanitized,
            "confidence": confidence
        }

    except Exception:
        # Do NOT leak system info
        raise HTTPException(
            status_code=400,
            detail="Validation error"
        )
