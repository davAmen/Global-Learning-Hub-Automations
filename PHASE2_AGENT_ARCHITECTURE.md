# Phase 2: WhatsApp Agent Architecture
## Autonomous Agent for Global Learning Hub

**Version:** 1.0  
**Date:** 2026-10-07  
**Status:** DESIGN PHASE — Ready for Implementation

---

## 1. Executive Summary

Build an autonomous AI agent (using LangGraph) that operates within WhatsApp Communities to:
- Monitor the "Official Training Provider" community (282 participants) for new materials, announcements, courses
- Extract and classify content (flyers, announcements, new courses, schedule changes)
- Route content to appropriate Global Learning Hub groups (announcement, class-specific, proof submission)
- Generate course flyers with admin contact details
- Manage payment verification workflows
- Create and manage WhatsApp groups via WasenderAPI
- Operate with **human-in-the-loop approval** for ALL outbound actions
- Maintain full audit trail

---

## 2. Agent Architecture (LangGraph)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT STATE MACHINE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│   │ MONITOR  │───►│ EXTRACT  │───►│  ROUTE   │───►│ APPROVE  │         │
│   │  (15m)   │    │  (LLM)   │    │  (Rules) │    │ (Admin)  │         │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘         │
│        │              │              │              │                   │
│        ▼              ▼              ▼              ▼                   │
│   ┌──────────────────────────────────────────────────────────┐         │
│   │                    AGENT STATE (PostgreSQL)               │         │
│   │  - Session ID  - Current Task  - Last Run  - Config      │         │
│   └──────────────────────────────────────────────────────────┘         │
│        │              │              │              │                   │
│        ▼              ▼              ▼              ▼                   │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│   │  SEND    │───►│   LOG    │───►│ FOLLOWUP │───►│  WAIT    │         │
│   │(Wasender)│    │(AuditDB) │    │ (Checks) │    │ (NextRun)│         │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.1 LangGraph Node Definitions

```python
# src/agent/nodes.py

from typing import TypedDict, List, Optional, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class AgentState(TypedDict):
    """Persistent agent state stored in PostgreSQL."""
    session_id: str
    current_task: Optional[dict]
    last_run: datetime
    config: dict
    messages: List[dict]  # For LLM conversation history
    pending_approvals: List[dict]
    completed_tasks: List[dict]

class MonitorResult(BaseModel):
    """Result of monitoring the Training Provider community."""
    new_items: List[dict]  # Each item: {type, content, source_url, timestamp}
    checked_at: datetime

class ExtractedContent(BaseModel):
    """LLM-extracted structured content."""
    type: Literal["flyer", "announcement", "new_course", "schedule_change", "material"]
    title: str
    description: str
    course_name: Optional[str]
    schedule: Optional[dict]  # {start_date, end_date, days, time, timezone}
    price: Optional[float]
    currency: Optional[str]
    payment_methods: List[dict]
    images: List[str]  # URLs
    source_url: str
    raw_text: str

class RoutingDecision(BaseModel):
    """Where to send the content."""
    target_groups: List[str]  # Group JIDs
    message_template: str
    requires_approval: bool = True
    priority: Literal["high", "normal", "low"] = "normal"

class ApprovalRequest(BaseModel):
    """Human-in-the-loop approval request."""
    id: UUID
    action_type: Literal["send_message", "create_group", "add_participant", "send_flyer", "verify_payment", "broadcast"]
    content: str
    target_group_jid: str
    target_course_id: Optional[UUID]
    metadata: dict
    status: Literal["pending", "approved", "rejected", "modified"] = "pending"
    created_at: datetime
```

---

## 3. Core Components

### 3.1 Training Provider Scraper (Playwright)

```python
# src/agent/scraper.py

from playwright.async_api import async_playwright
from typing import List, dict
import os

class TrainingProviderScraper:
    """Scrapes laplagemetaverse.org for new content."""
    
    def __init__(self):
        self.base_url = "https://app.laplagemetaverse.org"
        self.community_url = "https://app.laplagemetaverse.org/community/official-training-provider"
        self.email = os.getenv("LAPLAGE_EMAIL")
        self.password = os.getenv("LAPLAGE_PASSWORD")
    
    async def login(self, page):
        """Login to Laplage Metaverse."""
        await page.goto(f"{self.base_url}/login")
        await page.fill('input[name="email"]', self.email)
        await page.fill('input[name="password"]', self.password)
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard**")
    
    async def get_community_posts(self, page, last_checked: datetime) -> List[dict]:
        """Extract new posts since last check."""
        await page.goto(self.community_url)
        # Wait for posts to load
        await page.wait_for_selector('[data-testid="post-card"]')
        
        posts = await page.evaluate("""() => {
            const cards = document.querySelectorAll('[data-testid="post-card"]');
            return Array.from(cards).map(card => ({
                id: card.dataset.postId,
                title: card.querySelector('[data-testid="post-title"]')?.innerText,
                content: card.querySelector('[data-testid="post-content"]')?.innerText,
                author: card.querySelector('[data-testid="post-author"]')?.innerText,
                timestamp: card.querySelector('[data-testid="post-timestamp"]')?.dataset.timestamp,
                images: Array.from(card.querySelectorAll('img')).map(img => img.src),
                links: Array.from(card.querySelectorAll('a')).map(a => a.href),
                type: card.dataset.postType  // flyer, announcement, course, material
            }));
        }""")
        
        # Filter by timestamp
        new_posts = [p for p in posts if datetime.fromisoformat(p['timestamp']) > last_checked]
        return new_posts
    
    async def scrape(self, last_checked: datetime) -> List[dict]:
        """Main scrape entry point."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await self.login(page)
            posts = await self.get_community_posts(page, last_checked)
            await browser.close()
            return posts
```

### 3.2 Content Classifier & Extractor (LLM)

```python
# src/agent/extractor.py

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.agent.nodes import ExtractedContent

llm = ChatOpenAI(model="gpt-4o", temperature=0)

EXTRACTION_PROMPT = ChatPromptTemplate.from_template("""
You are an expert at extracting structured course information from training provider posts.

Analyze this post from the "Official Training Provider" community:

Title: {title}
Content: {content}
Author: {author}
Images: {images}
Links: {links}
Post Type: {post_type}

Extract the following information as JSON:
{{
    "type": "flyer|announcement|new_course|schedule_change|material",
    "title": "string",
    "description": "string",
    "course_name": "string or null",
    "schedule": {{
        "start_date": "YYYY-MM-DD or null",
        "end_date": "YYYY-MM-DD or null",
        "days": ["Monday", "Wednesday"] or null,
        "time": "18:00-20:00 or null",
        "timezone": "GMT or null"
    }},
    "price": "number or null",
    "currency": "GHS|USD|EUR or null",
    "payment_methods": [
        {{"type": "momo", "number": "+233...", "name": "MoMo"}},
        {{"type": "telecel", "number": "+233...", "name": "Telecel Cash"}}
    ],
    "images": ["url1", "url2"],
    "source_url": "string",
    "raw_text": "original post text"
}}

Rules:
- If it's a course flyer, type = "new_course" or "flyer"
- If it's a schedule change, type = "schedule_change"
- If it's general info, type = "announcement"
- If it's learning material, type = "material"
- Extract ALL payment details if present
- Course name should be the official course title
""")

async def extract_content(post: dict) -> ExtractedContent:
    """Use LLM to extract structured content from post."""
    chain = EXTRACTION_PROMPT | llm.with_structured_output(ExtractedContent)
    result = await chain.ainvoke(post)
    return result
```

### 3.3 Content Router

```python
# src/agent/router.py

from typing import List
from src.agent.nodes import ExtractedContent, RoutingDecision
from src.config import get_settings

class ContentRouter:
    """Routes extracted content to appropriate WhatsApp groups."""
    
    def __init__(self):
        self.settings = get_settings()
        self.group_mapping = {
            "announcement": self.settings.ielts_announcement_group_jid,
            "proof_submission": self.settings.ielts_proof_group_jid,
            "class_access": self.settings.ielts_class_access_group_jid,
        }
    
    def route(self, content: ExtractedContent) -> RoutingDecision:
        """Determine where to send content based on type and rules."""
        
        # Default: send to announcement group
        target_groups = [self.group_mapping["announcement"]]
        message_template = self._build_message(content)
        priority = "normal"
        
        if content.type == "new_course":
            # New course: create group, send flyer to announcement
            priority = "high"
            message_template = self._build_course_flyer_message(content)
            
        elif content.type == "flyer":
            # Flyer: send to announcement + admin's WhatsApp status
            priority = "high"
            message_template = self._build_flyer_message(content)
            
        elif content.type == "schedule_change":
            # Schedule change: send to class access group
            target_groups = [self.group_mapping["class_access"]]
            priority = "high"
            
        elif content.type == "material":
            # Materials: send to class access group
            target_groups = [self.group_mapping["class_access"]]
            
        elif content.type == "announcement":
            # General announcement: send to announcement group
            pass  # defaults already set
        
        return RoutingDecision(
            target_groups=target_groups,
            message_template=message_template,
            requires_approval=True,
            priority=priority
        )
    
    def _build_message(self, content: ExtractedContent) -> str:
        """Build standard message from extracted content."""
        return f"""📢 *{content.title.upper()}*

{content.description}

📅 {content.schedule.get('time', 'TBD')} {content.schedule.get('timezone', 'GMT')}
💰 {content.currency} {content.price}""" if content.price else ""
    
    def _build_course_flyer_message(self, content: ExtractedContent) -> str:
        """Build course flyer message with admin details."""
        payment_info = ""
        if content.price:
            payment_info = f"""
💰 *PRICE: {content.currency} {content.price}*
💳 *PAYMENT METHODS:*
{chr(10).join([f"{i+1}. {m['name']}: {m['number']}" for i, m in enumerate(content.payment_methods)])}
📝 *PROOF SUBMISSION:* {self.group_mapping['proof_submission']}"""
        
        return f"""🎓 *NEW COURSE: {content.course_name or content.title}*

{content.description}

📅 *SCHEDULE:* {content.schedule.get('start_date')} - {content.schedule.get('end_date')}
⏰ *TIME:* {content.schedule.get('time', 'TBD')} {content.schedule.get('timezone', 'GMT')}
{payment_info}

👨‍💼 *ADMIN CONTACT:*
David Amenuku
📧 amenukudavid20@gmail.com
📱 +233206967251

---
Global Learning Hub | Skills. Growth. Certification."""
    
    def _build_flyer_message(self, content: ExtractedContent) -> str:
        """Build flyer message for announcement + status."""
        return self._build_course_flyer_message(content)
```

### 3.4 Approval Manager

```python
# src/agent/approval.py

from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional
from src.database import get_db
from src.agent.nodes import ApprovalRequest

class ApprovalManager:
    """Manages human-in-the-loop approval workflow."""
    
    def __init__(self):
        self.db = get_db()
    
    async def create_approval(self, routing: RoutingDecision, content: ExtractedContent) -> str:
        """Create approval record in database."""
        approval_id = str(uuid4())
        
        approval_data = {
            "id": approval_id,
            "action_type": "send_message",
            "content": routing.message_template,
            "target_group_jid": routing.target_groups[0] if routing.target_groups else None,
            "target_course_id": None,  # Will be filled if course exists
            "metadata": {
                "routing": routing.model_dump(),
                "extracted_content": content.model_dump(),
                "priority": routing.priority
            },
            "status": "pending",
            "requested_by": "agent",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        self.db.table("approvals").insert(approval_data).execute()
        
        # Audit log
        self.db.table("audit_log").insert({
            "actor": "agent",
            "action": "approval_created",
            "entity_type": "approval",
            "entity_id": approval_id,
            "details": {"content_type": content.type, "target_groups": routing.target_groups},
        }).execute()
        
        return approval_id
    
    async def wait_for_approval(self, approval_id: str, timeout: int = 3600) -> Optional[str]:
        """Poll for approval decision (called by agent)."""
        import asyncio
        start_time = datetime.now(timezone.utc).timestamp()
        
        while (datetime.now(timezone.utc).timestamp() - start_time) < timeout:
            resp = self.db.table("approvals").select("status, content, target_group_jid").eq("id", approval_id).limit(1).execute()
            if resp.data:
                approval = resp.data[0]
                if approval["status"] == "approved":
                    return approval["content"]
                elif approval["status"] in ["rejected", "cancelled"]:
                    return None
            await asyncio.sleep(30)  # Poll every 30 seconds
        
        return None  # Timeout
    
    async def check_pending_approvals(self) -> list:
        """Get all pending approvals for admin UI."""
        resp = self.db.table("approvals").select("*").eq("status", "pending").order("created_at").execute()
        return resp.data or []
```

### 3.5 WasenderAPI Group Manager

```python
# src/agent/group_manager.py

import httpx
from typing import Optional
from src.config import get_settings

class WasenderGroupManager:
    """Manages WhatsApp groups via WasenderAPI."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.wasender_base_url
        self.api_key = self.settings.wasender_api_key
    
    async def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make authenticated request to WasenderAPI."""
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            url = f"{self.base_url}{endpoint}"
            if method == "GET":
                resp = await client.get(url, headers=headers)
            else:
                resp = await client.post(url, headers=headers, json=data)
            resp.raise_for_status()
            return resp.json()
    
    async def create_group(self, name: str, participants: list = None) -> dict:
        """Create a new WhatsApp group."""
        data = {"name": name}
        if participants:
            data["participants"] = participants
        return await self._request("POST", "/api/groups/create", data)
    
    async def add_participants(self, group_jid: str, participants: list) -> dict:
        """Add participants to group."""
        data = {"participants": participants}
        return await self._request("POST", f"/api/groups/{group_jid}/participants/add", data)
    
    async def remove_participant(self, group_jid: str, participant: str) -> dict:
        """Remove participant from group."""
        data = {"participants": [participant]}
        return await self._request("POST", f"/api/groups/{group_jid}/participants/remove", data)
    
    async def get_group_info(self, group_jid: str) -> dict:
        """Get group information."""
        return await self._request("GET", f"/api/groups/{group_jid}")
    
    async def get_invite_link(self, group_jid: str) -> str:
        """Get group invite link."""
        result = await self._request("GET", f"/api/groups/{group_jid}/invite")
        return result.get("invite_link", "")
    
    async def send_message(self, to: str, text: str) -> dict:
        """Send message to group or individual."""
        data = {"to": to, "text": text}
        return await self._request("POST", "/api/send-message", data)
    
    async def send_image(self, to: str, image_url: str, caption: str = "") -> dict:
        """Send image to group or individual."""
        data = {"to": to, "image": {"url": image_url, "caption": caption}}
        return await self._request("POST", "/api/send-image", data)
```

### 3.6 Agent Orchestrator (Main Loop)

```python
# src/agent/orchestrator.py

import asyncio
from datetime import datetime, timezone, timedelta
from src.agent.scraper import TrainingProviderScraper
from src.agent.extractor import extract_content
from src.agent.router import ContentRouter
from src.agent.approval import ApprovalManager
from src.agent.group_manager import WasenderGroupManager
from src.agent.nodes import AgentState
from src.database import get_db

class AgentOrchestrator:
    """Main agent orchestration loop."""
    
    def __init__(self):
        self.scraper = TrainingProviderScraper()
        self.router = ContentRouter()
        self.approval = ApprovalManager()
        self.group_manager = WasenderGroupManager()
        self.db = get_db()
    
    async def run_monitoring_cycle(self):
        """Single monitoring cycle (runs every 15 minutes)."""
        # Get last run time from agent_state
        state = self._get_agent_state()
        last_run = state.get("last_run") or (datetime.now(timezone.utc) - timedelta(hours=1))
        
        # 1. MONITOR: Scrape Training Provider
        new_posts = await self.scraper.scrape(last_run)
        
        if not new_posts:
            self._update_last_run()
            return
        
        # 2. EXTRACT & ROUTE each new post
        for post in new_posts:
            try:
                content = await extract_content(post)
                routing = self.router.route(content)
                
                # 3. APPROVE: Create approval request
                approval_id = await self.approval.create_approval(routing, content)
                
                # 4. WAIT for approval (or auto-approve if configured)
                approved_content = await self._handle_approval(approval_id, routing)
                
                if approved_content:
                    # 5. SEND to target groups
                    for group_jid in routing.target_groups:
                        await self.group_manager.send_message(group_jid, approved_content)
                    
                    # Log success
                    self._log_action(approval_id, "sent", {"groups": routing.target_groups})
                else:
                    self._log_action(approval_id, "rejected_or_timeout", {})
                    
            except Exception as e:
                self._log_error(post, e)
        
        # 6. Update last run
        self._update_last_run()
    
    async def _handle_approval(self, approval_id: str, routing: RoutingDecision) -> Optional[str]:
        """Handle approval workflow."""
        # Check if auto-approve is enabled
        config = self.db.table("system_config").select("value").eq("key", "auto_approve_agent_actions").limit(1).execute()
        auto_approve = config.data and config.data[0]["value"].get("enabled", False)
        
        if auto_approve and routing.priority != "high":
            # Auto-approve low/normal priority
            return await self.approval.approve(approval_id, "agent_auto")
        
        # Wait for human approval
        return await self.approval.wait_for_approval(approval_id)
    
    def _get_agent_state(self) -> dict:
        resp = self.db.table("agent_state").select("*").eq("session_id", "main").limit(1).execute()
        return resp.data[0] if resp.data else {}
    
    def _update_last_run(self):
        self.db.table("agent_state").upsert({
            "session_id": "main",
            "last_run": datetime.now(timezone.utc).isoformat(),
        }).execute()
    
    def _log_action(self, approval_id: str, action: str, details: dict):
        self.db.table("audit_log").insert({
            "actor": "agent",
            "action": action,
            "entity_type": "approval",
            "entity_id": approval_id,
            "details": details,
        }).execute()
    
    def _log_error(self, post: dict, error: Exception):
        self.db.table("audit_log").insert({
            "actor": "agent",
            "action": "error",
            "entity_type": "scraper",
            "details": {"post_id": post.get("id"), "error": str(error)},
        }).execute()

# Scheduler integration
async def run_agent_cycle():
    """Entry point for APScheduler."""
    orchestrator = AgentOrchestrator()
    await orchestrator.run_monitoring_cycle()
```

---

## 4. Database Schema Additions

```sql
-- agent_state (persistent agent state)
create table if not exists agent_state (
  session_id    text primary key,
  current_task  jsonb,
  last_run      timestamptz not null default now(),
  config        jsonb not null default '{}',
  updated_at    timestamptz not null default now()
);

-- Add to existing approvals table (already exists from Phase 1)
-- approvals table already has: id, action_type, content, target_group_jid, 
-- target_course_id, metadata, status, requested_by, reviewed_by, reviewed_at, review_notes, created_at, updated_at

-- Index for agent_state
create index if not exists idx_agent_state_session on agent_state(session_id);
```

---

## 5. Configuration (New .env Variables)

```env
# LLM Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Laplage Metaverse Credentials (encrypted in production)
LAPLAGE_EMAIL=your-email@example.com
LAPLAGE_PASSWORD=your-password

# Agent Configuration
AGENT_MONITOR_INTERVAL_MINUTES=15
AGENT_AUTO_APPROVE_LOW_PRIORITY=false
AGENT_MAX_CONCURRENT_TASKS=3

# WasenderAPI (already in Phase 1)
# WASENDER_API_KEY=
# WASENDER_BASE_URL=

# Feature Flags
ENABLE_AGENT_MONITORING=true
ENABLE_AUTO_FLYER_GENERATION=false
```

---

## 6. Implementation Phases

### Phase 2A: Core Agent Infrastructure (Week 1-2)
- [ ] Set up LangGraph project structure
- [ ] Implement agent_state table and persistence
- [ ] Build TrainingProviderScraper with Playwright
- [ ] Create basic LangGraph workflow (Monitor → Extract → Route → Approve → Send)
- [ ] Unit tests for each node

### Phase 2B: Content Intelligence (Week 3-4)
- [ ] Implement LLM-based content extractor (GPT-4o)
- [ ] Build content classifier (flyer, announcement, course, material, schedule_change)
- [ ] Create ContentRouter with rule-based routing
- [ ] Test with real Training Provider posts (stored samples)

### Phase 2C: Approval & Action Layer (Week 5-6)
- [ ] Implement ApprovalManager with database persistence
- [ ] Build WasenderGroupManager (create group, add participants, send media)
- [ ] Integrate with existing approval API endpoints
- [ ] Add admin notification (Telegram/email) for pending approvals

### Phase 2D: Payment & Follow-up (Week 7-8)
- [ ] Enhance payment verification workflow
- [ ] Implement follow-up checks (payment reminders, access confirmation)
- [ ] Add group participant sync
- [ ] End-to-end testing with real WhatsApp groups

---

## 7. Security Considerations

1. **Credential Management**: Laplage credentials in Vault/encrypted env vars
2. **Rate Limiting**: Respect WasenderAPI and WhatsApp Business API limits
3. **Approval Enforcement**: ZERO sends without approval (configurable)
4. **Audit Trail**: Every agent action logged with timestamp, actor, details
5. **Data Privacy**: No PII in LLM prompts; redact phone numbers before sending to LLM
6. **Error Handling**: Graceful degradation, alerting on critical failures

---

## 8. Monitoring & Observability

- **Structured Logging**: JSON logs with correlation IDs
- **Metrics**: Cycle duration, posts processed, approvals pending/approved/rejected, send success rate
- **Alerting**: On scraper failures, approval timeouts, send failures
- **Dashboard**: Admin UI shows agent status, recent actions, pending approvals

---

## 9. Next Steps

1. **Confirm architecture** with stakeholder
2. **Set up LangGraph development environment**
3. **Create test fixtures** from real Training Provider posts
4. **Begin Phase 2A implementation**

---

## 10. Questions for Clarification

1. **LaplageMetaverse API**: Does `app.laplagemetaverse.org` have a REST API, or must we scrape via Playwright?
2. **WhatsApp Status API**: Does WasenderAPI support posting to Status? (Check dashboard)
3. **Payment Verification**: Manual only, or integrate with MoMo/Telecel APIs?
4. **Flyer Templates**: Design specifications? Brand assets?
5. **Agent Autonomy Level**: Start with "propose only, admin approves all" — confirm?
6. **Team**: Solo dev, or will others contribute?