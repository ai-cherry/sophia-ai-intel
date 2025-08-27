"""
Support MCP Service - FastAPI service for Intercom integration
Handles customer support interactions and webhook events
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import hashlib
import hmac

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
INTERCOM_ACCESS_TOKEN = os.getenv("INTERCOM_ACCESS_TOKEN", "")
INTERCOM_APP_ID = os.getenv("INTERCOM_APP_ID", "")
INTERCOM_WEBHOOK_SECRET = os.getenv("INTERCOM_WEBHOOK_SECRET", "")
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY", "")
SERVICE_NAME = "support-mcp"
SERVICE_VERSION = "1.0.0"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    yield
    logger.info(f"Shutting down {SERVICE_NAME}")

# Initialize FastAPI app
app = FastAPI(
    title="Support MCP Service",
    description="MCP service for Intercom integration and customer support",
    version=SERVICE_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ConversationCreate(BaseModel):
    """Model for creating a new conversation"""
    user_id: str
    body: str
    subject: Optional[str] = None
    tags: Optional[List[str]] = []

class MessageCreate(BaseModel):
    """Model for creating a new message"""
    conversation_id: str
    body: str
    type: str = "comment"  # comment, note, assignment
    author_type: str = "admin"  # admin, user

class UserUpdate(BaseModel):
    """Model for updating user information"""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = {}

class WebhookEvent(BaseModel):
    """Model for Intercom webhook events"""
    type: str
    id: str
    created_at: int
    topic: str
    data: Dict[str, Any]

class TicketCreate(BaseModel):
    """Model for creating support tickets"""
    user_email: str
    subject: str
    description: str
    priority: str = "normal"  # low, normal, high, urgent
    tags: Optional[List[str]] = []

# Helper functions
def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Intercom webhook signature"""
    if not INTERCOM_WEBHOOK_SECRET:
        logger.warning("INTERCOM_WEBHOOK_SECRET not configured, skipping verification")
        return True
    
    expected_signature = hmac.new(
        INTERCOM_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

async def make_intercom_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None
) -> Dict[str, Any]:
    """Make authenticated request to Intercom API"""
    headers = {
        "Authorization": f"Bearer {INTERCOM_ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        url = f"https://api.intercom.io/{endpoint}"
        
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Intercom API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Intercom API error: {str(e)}")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint"""
    checks = {
        "intercom_configured": bool(INTERCOM_ACCESS_TOKEN),
        "webhook_secret_configured": bool(INTERCOM_WEBHOOK_SECRET),
        "portkey_configured": bool(PORTKEY_API_KEY)
    }
    
    is_ready = all(checks.values())
    
    return {
        "ready": is_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

# Conversation endpoints
@app.post("/api/conversations")
async def create_conversation(conversation: ConversationCreate):
    """Create a new Intercom conversation"""
    data = {
        "from": {
            "type": "user",
            "id": conversation.user_id
        },
        "body": conversation.body
    }
    
    if conversation.subject:
        data["subject"] = conversation.subject
    
    result = await make_intercom_request("POST", "conversations", data)
    
    # Add tags if provided
    if conversation.tags:
        conversation_id = result.get("id")
        for tag in conversation.tags:
            await make_intercom_request(
                "POST",
                f"conversations/{conversation_id}/tags",
                {"name": tag}
            )
    
    return result

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details"""
    return await make_intercom_request("GET", f"conversations/{conversation_id}")

@app.post("/api/conversations/{conversation_id}/reply")
async def reply_to_conversation(conversation_id: str, message: MessageCreate):
    """Reply to an existing conversation"""
    data = {
        "type": message.type,
        "body": message.body,
        "author": {
            "type": message.author_type
        }
    }
    
    return await make_intercom_request(
        "POST",
        f"conversations/{conversation_id}/reply",
        data
    )

@app.post("/api/conversations/{conversation_id}/close")
async def close_conversation(conversation_id: str):
    """Close a conversation"""
    return await make_intercom_request(
        "POST",
        f"conversations/{conversation_id}/close",
        {}
    )

# User management endpoints
@app.post("/api/users")
async def create_or_update_user(user: UserUpdate):
    """Create or update an Intercom user"""
    data = {
        "user_id": user.user_id
    }
    
    if user.email:
        data["email"] = user.email
    if user.name:
        data["name"] = user.name
    if user.custom_attributes:
        data["custom_attributes"] = user.custom_attributes
    
    return await make_intercom_request("POST", "users", data)

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Get user details"""
    return await make_intercom_request("GET", f"users/{user_id}")

@app.get("/api/users/{user_id}/conversations")
async def get_user_conversations(user_id: str, limit: int = 20, page: int = 1):
    """Get conversations for a specific user"""
    params = f"?user_id={user_id}&per_page={limit}&page={page}"
    return await make_intercom_request("GET", f"conversations{params}")

# Ticket management endpoints
@app.post("/api/tickets")
async def create_ticket(ticket: TicketCreate):
    """Create a support ticket"""
    # First, find or create the user
    user_data = {
        "email": ticket.user_email
    }
    user = await make_intercom_request("POST", "users", user_data)
    
    # Create a conversation as a ticket
    conversation_data = {
        "from": {
            "type": "user",
            "id": user["id"]
        },
        "body": ticket.description,
        "subject": ticket.subject
    }
    
    conversation = await make_intercom_request("POST", "conversations", conversation_data)
    
    # Add priority tag
    priority_tag = f"priority:{ticket.priority}"
    await make_intercom_request(
        "POST",
        f"conversations/{conversation['id']}/tags",
        {"name": priority_tag}
    )
    
    # Add additional tags
    if ticket.tags:
        for tag in ticket.tags:
            await make_intercom_request(
                "POST",
                f"conversations/{conversation['id']}/tags",
                {"name": tag}
            )
    
    return {
        "ticket_id": conversation["id"],
        "status": "created",
        "priority": ticket.priority,
        "user_id": user["id"]
    }

@app.get("/api/tickets/stats")
async def get_ticket_stats():
    """Get support ticket statistics"""
    try:
        # Get open conversations
        open_convos = await make_intercom_request(
            "GET",
            "conversations?open=true&per_page=1"
        )
        
        # Get closed conversations from last 7 days
        from_timestamp = int((datetime.utcnow().timestamp() - 7 * 24 * 3600))
        closed_convos = await make_intercom_request(
            "GET",
            f"conversations?open=false&created_since={from_timestamp}&per_page=1"
        )
        
        return {
            "open_tickets": open_convos.get("total_count", 0),
            "closed_last_7_days": closed_convos.get("total_count", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting ticket stats: {str(e)}")
        return {
            "error": "Unable to fetch statistics",
            "timestamp": datetime.utcnow().isoformat()
        }

# Webhook endpoints
@app.post("/webhooks/intercom")
async def handle_webhook(
    request: Request,
    x_hub_signature: Optional[str] = Header(None)
):
    """Handle Intercom webhook events"""
    body = await request.body()
    
    # Verify webhook signature
    if x_hub_signature and not verify_webhook_signature(body, x_hub_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    try:
        event = await request.json()
        event_type = event.get("type")
        topic = event.get("topic", "")
        
        logger.info(f"Received webhook event: {event_type} - {topic}")
        
        # Handle different event types
        if topic.startswith("conversation."):
            await handle_conversation_event(event)
        elif topic.startswith("user."):
            await handle_user_event(event)
        elif topic.startswith("contact."):
            await handle_contact_event(event)
        
        return {"status": "processed", "event_id": event.get("id")}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

async def handle_conversation_event(event: Dict[str, Any]):
    """Handle conversation-related webhook events"""
    topic = event.get("topic")
    data = event.get("data", {})
    
    if topic == "conversation.user.created":
        logger.info(f"New conversation created: {data.get('id')}")
        # Trigger any automated responses or notifications
    elif topic == "conversation.user.replied":
        logger.info(f"User replied to conversation: {data.get('id')}")
        # Handle user replies
    elif topic == "conversation.admin.replied":
        logger.info(f"Admin replied to conversation: {data.get('id')}")
        # Track admin responses
    elif topic == "conversation.admin.closed":
        logger.info(f"Conversation closed: {data.get('id')}")
        # Handle conversation closure

async def handle_user_event(event: Dict[str, Any]):
    """Handle user-related webhook events"""
    topic = event.get("topic")
    data = event.get("data", {})
    
    if topic == "user.created":
        logger.info(f"New user created: {data.get('id')}")
        # Trigger onboarding workflows
    elif topic == "user.deleted":
        logger.info(f"User deleted: {data.get('id')}")
        # Clean up user data

async def handle_contact_event(event: Dict[str, Any]):
    """Handle contact-related webhook events"""
    topic = event.get("topic")
    data = event.get("data", {})
    
    if topic == "contact.created":
        logger.info(f"New contact created: {data.get('id')}")
        # Process new contact
    elif topic == "contact.signed_up":
        logger.info(f"Contact signed up: {data.get('id')}")
        # Trigger welcome flow

# Search endpoints
@app.get("/api/search/conversations")
async def search_conversations(
    query: str,
    limit: int = 20,
    state: Optional[str] = None  # open, closed, all
):
    """Search conversations"""
    params = f"?query={query}&per_page={limit}"
    if state and state != "all":
        params += f"&open={'true' if state == 'open' else 'false'}"
    
    return await make_intercom_request("GET", f"conversations/search{params}")

@app.get("/api/search/users")
async def search_users(
    email: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 20
):
    """Search users"""
    query_parts = []
    if email:
        query_parts.append(f"email='{email}'")
    if name:
        query_parts.append(f"name~'{name}'")
    
    if not query_parts:
        raise HTTPException(status_code=400, detail="Provide email or name to search")
    
    query = " AND ".join(query_parts)
    params = f"?query={query}&per_page={limit}"
    
    return await make_intercom_request("GET", f"users/search{params}")

# Analytics endpoints
@app.get("/api/analytics/response-time")
async def get_response_time_analytics(days: int = 7):
    """Get average response time analytics"""
    # This is a simplified example - Intercom's actual analytics API may differ
    from_timestamp = int((datetime.utcnow().timestamp() - days * 24 * 3600))
    
    try:
        conversations = await make_intercom_request(
            "GET",
            f"conversations?created_since={from_timestamp}&per_page=100"
        )
        
        # Calculate metrics
        total_response_time = 0
        conversations_with_response = 0
        
        for convo in conversations.get("conversations", []):
            if convo.get("first_contact_reply_at"):
                created = convo.get("created_at", 0)
                replied = convo.get("first_contact_reply_at", 0)
                if replied > created:
                    total_response_time += (replied - created)
                    conversations_with_response += 1
        
        avg_response_time = (
            total_response_time / conversations_with_response
            if conversations_with_response > 0
            else 0
        )
        
        return {
            "period_days": days,
            "total_conversations": conversations.get("total_count", 0),
            "conversations_with_response": conversations_with_response,
            "average_response_time_seconds": avg_response_time,
            "average_response_time_hours": avg_response_time / 3600,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error calculating response time: {str(e)}")
        raise HTTPException(status_code=500, detail="Error calculating analytics")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)