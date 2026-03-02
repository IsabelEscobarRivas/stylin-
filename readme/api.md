# Stylin' — API Reference

**Version:** 1.0 | **Date:** 2026-03-02
**Base URL:** `https://core-api.dev.deploy.ai`
**Auth URL:** `https://api-auth.dev.deploy.ai/oauth2/token`

---

## Authentication

Stylin' uses **OAuth2 Client Credentials** flow for all API calls.

### Get Access Token

```http
POST https://api-auth.dev.deploy.ai/oauth2/token
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**

| Field | Type | Description |
|---|---|---|
| `grant_type` | string | Always `client_credentials` |
| `client_id` | string | Your Deploy AI client ID |
| `client_secret` | string | Your Deploy AI client secret |

**Response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Python Example:**

```python
import requests
import os

def get_access_token() -> str:
    data = {
        'grant_type': 'client_credentials',
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET')
    }
    response = requests.post(os.getenv('AUTH_URL'), data=data)
    return response.json()['access_token']
```

---

## Chat Sessions

### Create Chat

Initiates a new chat session with an agent.

```http
POST /chats
Authorization: Bearer <access_token>
X-Org: <org_id>
Content-Type: application/json
```

**Request Body:**

```json
{
  "agentId": "AGENT_ID_HERE",
  "stream": false
}
```

| Field | Type | Description |
|---|---|---|
| `agentId` | string | Target agent ID (Vision Scout, Style Curator, etc.) |
| `stream` | boolean | `false` for synchronous responses (recommended for MVP) |

**Response:**

```json
{
  "id": "chat_abc123xyz",
  "agentId": "AGENT_ID_HERE",
  "createdAt": "2026-03-02T13:33:47Z"
}
```

**Python Example:**

```python
def create_chat(access_token: str, agent_id: str) -> str:
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'X-Org': os.getenv('ORG_ID')
    }
    payload = {
        'agentId': agent_id,
        'stream': False
    }
    response = requests.post(
        f'{os.getenv("API_URL")}/chats',
        headers=headers,
        json=payload
    )
    if response.status_code == 200:
        return response.json()['id']
    raise Exception(f"Failed to create chat: {response.status_code} {response.text}")
```

---

## Messages

### Send Message

Sends a message to an active chat session and receives the agent response.

```http
POST /messages
Authorization: Bearer <access_token>
X-Org: <org_id>
Content-Type: application/json
```

**Request Body:**

```json
{
  "chatId": "chat_abc123xyz",
  "stream": false,
  "content": [
    {
      "type": "text",
      "value": "Analyze this look and find me similar outfits"
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `chatId` | string | Active chat session ID |
| `stream` | boolean | `false` for synchronous |
| `content` | array | Array of content objects |
| `content[].type` | string | `"text"` or `"image"` |
| `content[].value` | string | Message text or image URL |

**Response:**

```json
{
  "id": "msg_xyz789",
  "chatId": "chat_abc123xyz",
  "content": [
    {
      "type": "text",
      "value": "Here are three looks based on that photo..."
    }
  ],
  "createdAt": "2026-03-02T13:33:48Z"
}
```

**Python Example:**

```python
def send_message(access_token: str, chat_id: str, message: str) -> str:
    headers = {
        'X-Org': os.getenv('ORG_ID'),
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'chatId': chat_id,
        'stream': False,
        'content': [
            {
                'type': 'text',
                'value': message
            }
        ]
    }
    response = requests.post(
        f'{os.getenv("API_URL")}/messages',
        headers=headers,
        json=payload
    )
    if response.status_code == 200:
        return response.json()['content'][0]['value']
    raise Exception(f"Failed to send message: {response.status_code} {response.text}")
```

---

## Multi-Turn Conversations

To continue a conversation (maintain context), reuse the same `chat_id`:

```python
# Turn 1: Analyze an image
response_1 = send_message(token, chat_id, "Here's the look: [image_url]")

# Turn 2: Follow-up in same conversation
response_2 = send_message(token, chat_id, "Show me the budget version only")

# Turn 3: Another follow-up
response_3 = send_message(token, chat_id, "What's the Style Persona for this?")
```

---

## Agent IDs

| Agent | Purpose | agentId |
|---|---|---|
| Vision Scout | Image analysis & style signal extraction | Configured in Deploy AI dashboard |
| Style Curator | Product matching & outfit recommendations | Configured in Deploy AI dashboard |
| General Fallback | General queries | `GPT_4O` |

---

## Error Handling

| Status Code | Meaning | Action |
|---|---|---|
| `200` | Success | Parse response normally |
| `400` | Bad request | Check request body format |
| `401` | Unauthorized | Refresh access token and retry |
| `403` | Forbidden | Check ORG_ID and agent permissions |
| `429` | Rate limited | Back off and retry after delay |
| `500` | Server error | Log and retry with exponential backoff |

---

## Full Integration Example

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_access_token() -> str:
    data = {
        'grant_type': 'client_credentials',
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET')
    }
    response = requests.post(os.getenv('AUTH_URL'), data=data)
    return response.json()['access_token']

def create_chat(access_token: str) -> str:
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'X-Org': os.getenv('ORG_ID')
    }
    response = requests.post(
        f'{os.getenv("API_URL")}/chats',
        headers=headers,
        json={'agentId': 'GPT_4O', 'stream': False}
    )
    if response.status_code == 200:
        return response.json()['id']
    raise Exception(f"Failed to create chat: {response.status_code}")

def send_message(access_token: str, chat_id: str, message: str) -> str:
    headers = {
        'X-Org': os.getenv('ORG_ID'),
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(
        f'{os.getenv("API_URL")}/messages',
        headers=headers,
        json={
            'chatId': chat_id,
            'stream': False,
            'content': [{'type': 'text', 'value': message}]
        }
    )
    if response.status_code == 200:
        return response.json()['content'][0]['value']
    raise Exception(f"Failed to send message: {response.status_code}")

if __name__ == '__main__':
    token = get_access_token()
    chat_id = create_chat(token)
    result = send_message(token, chat_id, "Find me looks like this: [image_url]")
    print(result)
```

---

*Full Deploy AI API reference: https://core-api.dev.deploy.ai/ui*
