"""AI service for LLM integration."""
from typing import Optional, List, Dict, Any, AsyncGenerator, Callable, Awaitable
import json
import uuid
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from app.core.config import get_settings
from app.graphql.types.enums import EventPriority


settings = get_settings()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
    ) -> Any:
        """Generate chat completion."""
        pass

    @abstractmethod
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
    ) -> Any:
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[str, None]:
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue


class AnthropicProvider(LLMProvider):
    """Anthropic provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
    ) -> Any:
        import httpx

        # Convert messages to Anthropic format
        system_message = ""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "stream": stream,
            "max_tokens": max_tokens or 4096,
        }

        if system_message:
            payload["system"] = system_message

        if tools:
            # Convert tools to Anthropic format
            payload["tools"] = self._convert_tools(tools)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """Convert OpenAI tool format to Anthropic format."""
        anthropic_tools = []
        for tool in tools:
            if tool["type"] == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
        return anthropic_tools

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[str, None]:
        import httpx

        system_message = ""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "stream": True,
            "max_tokens": max_tokens or 4096,
        }

        if system_message:
            payload["system"] = system_message

        if tools:
            payload["tools"] = self._convert_tools(tools)

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            chunk = json.loads(data)
                            if chunk.get("type") == "content_block_delta":
                                delta = chunk.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        except json.JSONDecodeError:
                            continue


class AIService:
    """AI service for managing LLM interactions."""

    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available LLM providers."""
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "test-key-for-development":
            self.providers["openai"] = OpenAIProvider(settings.OPENAI_API_KEY)

        if settings.ANTHROPIC_API_KEY:
            self.providers["anthropic"] = AnthropicProvider(settings.ANTHROPIC_API_KEY)

        # Always add mock provider as fallback
        if "mock" not in self.providers:
            self.providers["mock"] = MockProvider()

    def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """Get LLM provider by name."""
        return self.providers.get(provider_name)

    def get_default_provider(self) -> Optional[LLMProvider]:
        """Get default provider."""
        # Try configured provider first, then mock
        provider = self.get_provider(settings.DEFAULT_AI_PROVIDER)
        if provider:
            return provider
        return self.get_provider("mock")

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Generate AI response."""
        provider_name = provider or settings.DEFAULT_AI_PROVIDER
        model_name = model or settings.DEFAULT_AI_MODEL

        llm_provider = self.get_provider(provider_name)
        if not llm_provider:
            raise ValueError(f"Provider {provider_name} not configured")

        return await llm_provider.chat_completion(
            messages=messages,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )

    async def stream_response(
        self,
        messages: List[Dict[str, Any]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream AI response."""
        provider_name = provider or settings.DEFAULT_AI_PROVIDER
        model_name = model or settings.DEFAULT_AI_MODEL

        llm_provider = self.get_provider(provider_name)
        if not llm_provider:
            raise ValueError(f"Provider {provider_name} not configured")

        async for chunk in llm_provider.stream_chat_completion(
            messages=messages,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        ):
            yield chunk

    async def generate_response_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tool_functions: Dict[str, Callable[..., Awaitable[Any]]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Generate AI response with tool calling loop."""
        provider_name = provider or settings.DEFAULT_AI_PROVIDER
        model_name = model or settings.DEFAULT_AI_MODEL

        llm_provider = self.get_provider(provider_name)
        if not llm_provider:
            raise ValueError(f"Provider {provider_name} not configured")

        current_messages = messages.copy()

        # Loop to handle multiple tool calls
        max_iterations = 5
        for _ in range(max_iterations):
            response = await llm_provider.chat_completion(
                messages=current_messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )

            choices = response.get("choices", [])
            if not choices:
                break

            message = choices[0].get("message", {})
            tool_calls = message.get("tool_calls", [])

            # Add assistant message to conversation
            current_messages.append(message)

            if not tool_calls:
                # No more tool calls, return final response
                return response

            # Execute tool calls
            for tool_call in tool_calls:
                function_name = tool_call.get("function", {}).get("name")
                function_args = tool_call.get("function", {}).get("arguments", "{}")

                try:
                    args = json.loads(function_args)
                except json.JSONDecodeError:
                    args = {}

                if function_name in tool_functions:
                    try:
                        result = await tool_functions[function_name](**args)
                        tool_result = json.dumps(result) if not isinstance(result, str) else result
                    except Exception as e:
                        tool_result = json.dumps({"error": str(e)})
                else:
                    tool_result = json.dumps({"error": f"Unknown function: {function_name}"})

                # Add tool result to conversation
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "name": function_name,
                    "content": tool_result,
                })

        # If we've exhausted iterations, return the last response
        return response


class MockProvider(LLMProvider):
    """Mock provider for development/testing without real API keys."""

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
    ) -> Any:
        # Check if there are tool results in the conversation (indicating we already called tools)
        has_tool_results = any(msg.get("role") == "tool" for msg in messages)

        if has_tool_results:
            # We already have tool results, return a response based on them
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "I found your events for this week. You have several scheduled events. Would you like me to help you organize them or create new ones?",
                    }
                }]
            }

        # Check if the last USER message mentions events/calendar (ignore tool messages)
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg
                break

        content = last_user_msg.get("content", "").lower() if last_user_msg else ""

        # Simulate tool calling for calendar queries
        if any(keyword in content for keyword in ["event", "calendar", "week", "schedule", "meeting"]):
            if tools:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "get_calendar_events",
                                    "arguments": json.dumps({
                                        "start_date": datetime.now().isoformat(),
                                        "end_date": (datetime.now() + timedelta(days=7)).isoformat(),
                                        "timezone": "UTC"
                                    })
                                }
                            }]
                        }
                    }]
                }

        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "I'm a mock AI assistant. I can help you plan events and manage your calendar. In production, I'd use OpenAI or Anthropic to provide real responses with tool calling."
                }
            }]
        }

    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[str, None]:
        yield "I'm a mock AI assistant for development. "
        yield "I can help with calendar events and planning. "
        yield "Configure OPENAI_API_KEY or ANTHROPIC_API_KEY for real responses."

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Generate AI response."""
        provider_name = provider or settings.DEFAULT_AI_PROVIDER
        model_name = model or settings.DEFAULT_AI_MODEL

        llm_provider = self.get_provider(provider_name)
        if not llm_provider:
            raise ValueError(f"Provider {provider_name} not configured")

        return await llm_provider.chat_completion(
            messages=messages,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )

    async def stream_response(
        self,
        messages: List[Dict[str, Any]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream AI response."""
        provider_name = provider or settings.DEFAULT_AI_PROVIDER
        model_name = model or settings.DEFAULT_AI_MODEL

        llm_provider = self.get_provider(provider_name)
        if not llm_provider:
            raise ValueError(f"Provider {provider_name} not configured")

        async for chunk in llm_provider.stream_chat_completion(
            messages=messages,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        ):
            yield chunk

    async def generate_response_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tool_functions: Dict[str, Callable[..., Awaitable[Any]]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Generate AI response with tool calling loop."""
        provider_name = provider or settings.DEFAULT_AI_PROVIDER
        model_name = model or settings.DEFAULT_AI_MODEL

        llm_provider = self.get_provider(provider_name)
        if not llm_provider:
            raise ValueError(f"Provider {provider_name} not configured")

        current_messages = messages.copy()

        # Loop to handle multiple tool calls
        max_iterations = 5
        for _ in range(max_iterations):
            response = await llm_provider.chat_completion(
                messages=current_messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )

            choices = response.get("choices", [])
            if not choices:
                break

            message = choices[0].get("message", {})
            tool_calls = message.get("tool_calls", [])

            # Add assistant message to conversation
            current_messages.append(message)

            if not tool_calls:
                # No more tool calls, return final response
                return response

            # Execute tool calls
            for tool_call in tool_calls:
                function_name = tool_call.get("function", {}).get("name")
                function_args = tool_call.get("function", {}).get("arguments", "{}")

                try:
                    args = json.loads(function_args)
                except json.JSONDecodeError:
                    args = {}

                if function_name in tool_functions:
                    try:
                        result = await tool_functions[function_name](**args)
                        tool_result = json.dumps(result) if not isinstance(result, str) else result
                    except Exception as e:
                        tool_result = json.dumps({"error": str(e)})
                else:
                    tool_result = json.dumps({"error": f"Unknown function: {function_name}"})

                # Add tool result to conversation
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "name": function_name,
                    "content": tool_result,
                })

        # If we've exhausted iterations, return the last response
        return response


# AI Tools for planner
PLANNER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Get calendar events for a date range",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date-time"},
                    "end_date": {"type": "string", "format": "date-time"},
                    "timezone": {"type": "string"},
                },
                "required": ["start_date", "end_date", "timezone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_events",
            "description": "Search events by query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "start_date": {"type": "string", "format": "date-time"},
                    "end_date": {"type": "string", "format": "date-time"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_proposed_events",
            "description": "Create proposed events for user confirmation",
            "parameters": {
                "type": "object",
                "properties": {
                    "events": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "suggested_start_time": {"type": "string", "format": "date-time"},
                                "suggested_end_time": {"type": "string", "format": "date-time"},
                                "category_id": {"type": "string", "format": "uuid"},
                                "priority": {"type": "string", "enum": ["normal", "high", "critical"]},
                                "preparation_notes": {"type": "string"},
                                "reminders": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "minutes_before": {"type": "integer"},
                                            "notification_type": {"type": "string", "enum": ["in_app", "email", "push"]},
                                        },
                                        "required": ["minutes_before"],
                                    },
                                },
                            },
                            "required": ["title", "suggested_start_time", "suggested_end_time"],
                        },
                    },
                },
                "required": ["events"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_categories",
            "description": "Get user's event categories",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search personal memory for relevant context",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "memory_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["goal", "preference", "commitment", "fact", "summary"]},
                    },
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_conflicts",
            "description": "Detect scheduling conflicts for proposed events",
            "parameters": {
                "type": "object",
                "properties": {
                    "events": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "start_time": {"type": "string", "format": "date-time"},
                                "end_time": {"type": "string", "format": "date-time"},
                            },
                            "required": ["start_time", "end_time"],
                        },
                    },
                },
                "required": ["events"],
            },
        },
    },
]


class PlannerToolExecutor:
    """Executes planner tools with database access."""

    def __init__(self, user_id: uuid.UUID, db_session_factory):
        self.user_id = user_id
        self.db_session_factory = db_session_factory

    async def get_calendar_events(self, start_date: str, end_date: str, timezone: str) -> dict:
        """Get calendar events for a date range."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async with self.db_session_factory() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.user_id == self.user_id,
                    Event.deleted_at.is_(None),
                    Event.status == EventStatus.SCHEDULED,
                    Event.start_time < end_date,
                    Event.end_time > start_date,
                )
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
                .order_by(Event.start_time)
            )
            events = result.scalars().all()

            return {
                "events": [
                    {
                        "id": str(e.id),
                        "title": e.title,
                        "description": e.description,
                        "location": e.location,
                        "start_time": e.start_time.isoformat(),
                        "end_time": e.end_time.isoformat(),
                        "all_day": e.all_day,
                        "timezone": e.timezone,
                        "priority": e.priority.value,
                        "status": e.status.value,
                        "is_recurring": e.is_recurring,
                        "category": {
                            "id": str(e.category.id),
                            "name": e.category.name,
                            "color": e.category.color,
                        } if e.category else None,
                    }
                    for e in events
                ]
            }

    async def search_events(self, query: str, start_date: str = None, end_date: str = None) -> dict:
        """Search events by query."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select

        async with self.db_session_factory() as db:
            stmt = select(Event).where(
                Event.user_id == self.user_id,
                Event.deleted_at.is_(None),
                Event.status == EventStatus.SCHEDULED,
            )

            if start_date:
                stmt = stmt.where(Event.end_time >= start_date)
            if end_date:
                stmt = stmt.where(Event.start_time <= end_date)

            search = f"%{query}%"
            stmt = stmt.where(
                Event.title.ilike(search) |
                Event.description.ilike(search) |
                Event.location.ilike(search)
            )

            result = await db.execute(stmt.order_by(Event.start_time).limit(20))
            events = result.scalars().all()

            return {
                "events": [
                    {
                        "id": str(e.id),
                        "title": e.title,
                        "description": e.description,
                        "location": e.location,
                        "start_time": e.start_time.isoformat(),
                        "end_time": e.end_time.isoformat(),
                    }
                    for e in events
                ]
            }

    async def get_categories(self) -> dict:
        """Get user's event categories."""
        from app.models.category import Category
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async with self.db_session_factory() as db:
            result = await db.execute(
                select(Category)
                .where(
                    Category.user_id == self.user_id,
                    Category.deleted_at.is_(None),
                )
                .options(selectinload(Category.children))
                .order_by(Category.sort_order, Category.name)
            )
            categories = result.scalars().all()

            def cat_to_dict(cat):
                return {
                    "id": str(cat.id),
                    "name": cat.name,
                    "description": cat.description,
                    "color": cat.color,
                    "icon": cat.icon,
                    "is_system": cat.is_system,
                    "children": [cat_to_dict(c) for c in cat.children] if cat.children else [],
                }

            return {"categories": [cat_to_dict(c) for c in categories if c.parent_id is None]}

    async def search_memory(self, query: str, memory_types: list = None, limit: int = 10) -> dict:
        """Search personal memory for relevant context."""
        from app.models.memory import UserMemory, MemoryType
        from sqlalchemy import select

        async with self.db_session_factory() as db:
            stmt = select(UserMemory).where(
                UserMemory.user_id == self.user_id,
                UserMemory.deleted_at.is_(None),
                UserMemory.is_active == True,
            )

            search_term = f"%{query}%"
            stmt = stmt.where(
                UserMemory.title.ilike(search_term) |
                UserMemory.content.ilike(search_term)
            )

            if memory_types:
                stmt = stmt.where(UserMemory.memory_type.in_(memory_types))

            stmt = stmt.limit(limit)
            result = await db.execute(stmt)
            memories = result.scalars().all()

            return {
                "memories": [
                    {
                        "id": str(m.id),
                        "type": m.memory_type.value,
                        "title": m.title,
                        "content": m.content,
                        "confidence": m.confidence,
                    }
                    for m in memories
                ]
            }

    async def detect_conflicts(self, events: list) -> dict:
        """Detect scheduling conflicts for proposed events."""
        conflicts = []
        for i, e1 in enumerate(events):
            for e2 in events[i+1:]:
                start1 = datetime.fromisoformat(e1["start_time"].replace("Z", "+00:00"))
                end1 = datetime.fromisoformat(e1["end_time"].replace("Z", "+00:00"))
                start2 = datetime.fromisoformat(e2["start_time"].replace("Z", "+00:00"))
                end2 = datetime.fromisoformat(e2["end_time"].replace("Z", "+00:00"))

                if start1 < end2 and start2 < end1:
                    conflicts.append({
                        "event1": e1,
                        "event2": e2,
                    })

        return {"conflicts": conflicts}

    async def create_proposed_events(self, events: list, conversation_id: str) -> dict:
        """Create proposed events for user confirmation."""
        from app.graphql.types.event import ProposedEvent

        proposed = []
        for event_input in events:
            proposed_event = ProposedEvent(
                id=uuid.uuid4(),
                title=event_input["title"],
                description=event_input.get("description", ""),
                suggested_start_time=event_input["suggested_start_time"],
                suggested_end_time=event_input["suggested_end_time"],
                category=event_input.get("category_id"),
                priority=event_input.get("priority", "normal"),
                preparation_notes=event_input.get("preparation_notes", ""),
                reminders=event_input.get("reminders", []),
            )
            proposed.append(proposed_event)

        return {"proposed_events": [
            {
                "id": str(p.id),
                "title": p.title,
                "description": p.description,
                "suggested_start_time": p.suggested_start_time.isoformat(),
                "suggested_end_time": p.suggested_end_time.isoformat(),
                "category_id": p.category,
                "priority": p.priority,
                "preparation_notes": p.preparation_notes,
                "reminders": p.reminders,
            }
            for p in proposed
        ]}


SYSTEM_PROMPT_PLANNER = """You are an intelligent personal life planner AI. Your role is to help users organize their lives, plan events, set goals, and manage their time effectively.

You have access to the user's calendar, events, categories, and personal memory. Use these tools to provide personalized, context-aware assistance.

Key principles:
1. Always ask for confirmation before creating/modifying/deleting actual calendar events
2. Propose structured plans that the user can review and approve
3. Consider the user's existing commitments, preferences, and goals
4. Be proactive in suggesting relevant events and reminders
5. Help break down complex goals into manageable tasks
6. Detect and warn about scheduling conflicts

When proposing events:
- Provide clear titles, descriptions, and suggested times
- Assign appropriate categories and priorities
- Include preparation notes when helpful
- Suggest reasonable reminder times

When helping with planning:
- Consider the user's timezone
- Respect existing commitments
- Suggest realistic timeframes
- Break large tasks into smaller steps

Your responses should be helpful, organized, and actionable."""


async def get_planner_response(
    user_message: str,
    conversation_history: List[Dict[str, Any]],
    user_context: Dict[str, Any],
    ai_service: "AIService",
    user_id: uuid.UUID,
    db_session_factory,
) -> str:
    """Get AI planner response with tool calling."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_PLANNER},
    ]

    # Add context about user
    if user_context:
        context_msg = f"User context: {json.dumps(user_context, default=str)}"
        messages.append({"role": "system", "content": context_msg})

    # Add conversation history
    messages.extend(conversation_history)

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    # Create tool executor
    executor = PlannerToolExecutor(user_id, db_session_factory)

    # Map tool names to executor methods
    tool_functions = {
        "get_calendar_events": executor.get_calendar_events,
        "search_events": executor.search_events,
        "get_categories": executor.get_categories,
        "search_memory": executor.search_memory,
        "detect_conflicts": executor.detect_conflicts,
        "create_proposed_events": lambda **kwargs: executor.create_proposed_events(**kwargs, conversation_id=user_context.get("conversation_id", "")),
    }

    # Get response with tools (use mock provider for development)
    response = await ai_service.generate_response_with_tools(
        messages=messages,
        tool_functions=tool_functions,
        tools=PLANNER_TOOLS,
        temperature=0.7,
        provider="mock",
    )

    choices = response.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        return message.get("content", "")

    return "I'm having trouble generating a response. Please try again."