"""FastAPI control plane for Living Objects."""

from __future__ import annotations

import asyncio
import hmac
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from production.auth import JWTError, decode_jwt, encode_jwt
from production.config import Settings
from production.metrics import (
    ARCHIVE_ERRORS,
    CONTENT_TYPE_LATEST,
    CULTURE,
    FITNESS,
    GENERATIONS,
    NOVELTY,
    ORGANISMS,
    REQUESTS,
    generate_latest,
)
from production.store import OrganismRecord, RedisCache, StateStore, utc_now
from production.api.v2.routes import control_state, router as v2_router
from production.api.v3.routes import router as v3_router, state as v3_state
from production.api.v4.routes import router as v4_router, state as v4_state
from production.api.v5.routes import router as v5_router, state as v5_state
from production.api.v6.routes import router as v6_router, state as v6_state
from production.api.v9.routes import router as v9_router, state as v9_state
from production.middleware.cors import CORSConfig
from production.middleware.rate_limit import configure_rate_limiter, rate_limit_dependency


class OrganismCreate(BaseModel):
    species: str = Field(default="adaptive", min_length=1, max_length=64)
    generation: int = Field(default=0, ge=0)
    fitness: float = Field(default=0.0, ge=0.0, le=1.0)
    mutation_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrganismUpdate(BaseModel):
    status: Optional[str] = Field(default=None, min_length=1, max_length=32)
    fitness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metadata: Optional[dict[str, Any]] = None


class TokenRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class EvolutionStepRequest(BaseModel):
    generation: int = Field(default=0, ge=0)
    organism_count: int = Field(default=0, ge=0)
    average_fitness: float = Field(default=0.0, ge=0.0, le=1.0)
    cultural_complexity: float = Field(default=0.0, ge=0.0)
    novelty_delta: int = Field(default=0, ge=0)


class EventBroker:
    def __init__(self, max_events: int = 500) -> None:
        self.max_events = max_events
        self.history: list[dict[str, Any]] = []
        self.clients: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event: dict[str, Any]) -> None:
        async with self._lock:
            self.history.append(event)
            self.history = self.history[-self.max_events :]
            for client in list(self.clients):
                if client.full():
                    try:
                        client.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await client.put(event)

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=50)
        async with self._lock:
            self.clients.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            self.clients.discard(queue)


class Runtime:
    def __init__(self, settings: Settings) -> None:
        settings.ensure_local_state()
        self.settings = settings
        self.store = StateStore(settings.database_url)
        self.cache = RedisCache(settings.redis_url)
        self.broker = EventBroker(settings.event_buffer_size)
        self.generation = 0

    def close(self) -> None:
        self.store.close()

    def snapshot(self) -> dict[str, Any]:
        organisms = self.store.list_organisms(limit=10_000)
        count = len(organisms)
        average_fitness = sum(item.fitness for item in organisms) / count if count else 0.0
        snapshot = {
            "organism_count": count,
            "average_fitness": round(average_fitness, 6),
            "generation": self.generation,
            "memome_count": len(self.store.query_memes(limit=10_000)),
        }
        ORGANISMS.set(count)
        FITNESS.set(average_fitness)
        return snapshot


settings = Settings.from_env()
configure_rate_limiter(
    settings.redis_url,
    enabled=settings.environment.lower() in {"production", "prod", "staging"},
)
runtime = Runtime(settings)
bearer = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    runtime.close()


app = FastAPI(
    title="Living Objects Platform API",
    version="1.0.0",
    description="Authenticated control plane for scalable software-organism evolution.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORSConfig(settings.environment).validate_origins(settings.cors_origins)),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    try:
        return decode_jwt(credentials.credentials, settings.jwt_secret)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_operator(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    if user.get("role") != "operator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="operator role required")
    return user


app.include_router(v2_router, dependencies=[Depends(require_operator)])
app.include_router(v3_router, dependencies=[Depends(require_operator)])
app.include_router(v4_router, dependencies=[Depends(require_operator)])
app.include_router(v5_router, dependencies=[Depends(require_operator)])
app.include_router(v6_router, dependencies=[Depends(require_operator)])
app.include_router(v9_router, dependencies=[Depends(require_operator)])


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "environment": settings.environment, "redis": runtime.cache.enabled}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/auth/token", dependencies=[Depends(rate_limit_dependency("5/minute"))])
def issue_token(request: TokenRequest) -> dict[str, Any]:
    expected_user = hmac.compare_digest(request.username, settings.operator_username)
    expected_password = hmac.compare_digest(request.password, settings.operator_password)
    if not (expected_user and expected_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = encode_jwt({"sub": request.username, "role": "operator"}, settings.jwt_secret, settings.jwt_ttl_seconds)
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.jwt_ttl_seconds}


@app.get("/organisms")
def list_organisms(
    limit: int = Query(default=100, ge=1, le=10_000),
    offset: int = Query(default=0, ge=0),
    _: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    items = runtime.store.list_organisms(limit=limit, offset=offset)
    REQUESTS.labels("GET", "/organisms", "200").inc()
    return {"items": [item.__dict__ for item in items], "count": len(items), "offset": offset, "limit": limit}


@app.post("/organisms", status_code=status.HTTP_201_CREATED)
async def create_organism(payload: OrganismCreate, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    if len(runtime.store.list_organisms(limit=settings.organism_limit)) >= settings.organism_limit:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="organism capacity reached")
    record = OrganismRecord(
        organism_id=f"org-{__import__('uuid').uuid4().hex[:12]}",
        species=payload.species,
        generation=payload.generation,
        fitness=payload.fitness,
        mutation_rate=payload.mutation_rate,
        status="alive",
        created_at=utc_now(),
        metadata=payload.metadata,
    )
    runtime.store.upsert_organism(record)
    await runtime.broker.publish({"type": "organism.created", "data": record.__dict__})
    ORGANISMS.set(len(runtime.store.list_organisms(limit=10_000)))
    return record.__dict__


@app.get("/organisms/{organism_id}")
def get_organism(organism_id: str, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    record = runtime.store.get_organism(organism_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="organism not found")
    return record.__dict__


@app.patch("/organisms/{organism_id}")
async def update_organism(
    organism_id: str, payload: OrganismUpdate, _: dict[str, Any] = Depends(current_user)
) -> dict[str, Any]:
    current = runtime.store.get_organism(organism_id)
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="organism not found")
    updates = payload.model_dump(exclude_unset=True)
    updated = OrganismRecord(
        organism_id=current.organism_id,
        species=current.species,
        generation=current.generation,
        fitness=updates.get("fitness", current.fitness),
        mutation_rate=current.mutation_rate,
        status=updates.get("status", current.status),
        created_at=current.created_at,
        metadata=updates.get("metadata", current.metadata),
    )
    runtime.store.upsert_organism(updated)
    await runtime.broker.publish({"type": "organism.updated", "data": updated.__dict__})
    return updated.__dict__


@app.delete("/organisms/{organism_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organism(organism_id: str, _: dict[str, Any] = Depends(current_user)) -> None:
    if not runtime.store.delete_organism(organism_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="organism not found")


@app.get("/archive/strategies")
def query_archive(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=100, ge=1, le=10_000),
    _: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    try:
        items = runtime.store.query_memes(q, limit)
    except Exception as exc:
        ARCHIVE_ERRORS.inc()
        raise HTTPException(status_code=503, detail="archive unavailable") from exc
    return {"items": items, "count": len(items)}


@app.post("/evolution/step")
async def evolution_step(payload: EvolutionStepRequest, _: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    runtime.generation = max(runtime.generation, payload.generation)
    FITNESS.set(payload.average_fitness)
    CULTURE.set(payload.cultural_complexity)
    NOVELTY.inc(payload.novelty_delta)
    GENERATIONS.inc()
    event = runtime.store.record_event("generation.completed", runtime.generation, payload.model_dump())
    await runtime.broker.publish({"type": "generation.completed", "data": event})
    return {"accepted": True, "event": event}


@app.websocket("/ws/evolution")
async def evolution_stream(websocket: WebSocket, token: str = Query(default="")) -> None:
    try:
        decode_jwt(token, settings.jwt_secret)
    except JWTError:
        await websocket.close(code=1008, reason="valid token required")
        return
    await websocket.accept()
    queue = await runtime.broker.subscribe()
    try:
        for event in runtime.broker.history[-20:]:
            await websocket.send_json(event)
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        await runtime.broker.unsubscribe(queue)


@app.websocket("/ws/v2/evolution")
async def v2_evolution_stream(websocket: WebSocket, token: str = Query(default="")) -> None:
    """Stream v2 organism, culture, constitution, and red-team events."""
    try:
        decode_jwt(token, settings.jwt_secret)
    except JWTError:
        await websocket.close(code=1008, reason="valid token required")
        return
    await websocket.accept()
    cursor = 0
    try:
        while True:
            events = control_state.events
            if cursor < len(events):
                for event in events[cursor:]:
                    await websocket.send_json(event)
                cursor = len(events)
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return


_V3_WS_CONNECTIONS: dict[str, int] = {}


@app.websocket("/ws/v3/evolution")
async def v3_evolution_stream(websocket: WebSocket, token: str = Query(default="")) -> None:
    """Stream v3 frontier events, capped at ten concurrent connections per IP."""
    try:
        decode_jwt(token, settings.jwt_secret)
    except JWTError:
        await websocket.close(code=1008, reason="valid token required")
        return
    address = websocket.client.host if websocket.client else "unknown"
    if _V3_WS_CONNECTIONS.get(address, 0) >= 10:
        await websocket.close(code=1013, reason="connection limit reached")
        return
    _V3_WS_CONNECTIONS[address] = _V3_WS_CONNECTIONS.get(address, 0) + 1
    await websocket.accept()
    cursor = 0
    try:
        while True:
            events = v3_state.events
            if cursor < len(events):
                for event in events[cursor:]:
                    await websocket.send_json(event)
                cursor = len(events)
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return
    finally:
        remaining = _V3_WS_CONNECTIONS.get(address, 1) - 1
        if remaining <= 0:
            _V3_WS_CONNECTIONS.pop(address, None)
        else:
            _V3_WS_CONNECTIONS[address] = remaining


_V4_WS_CONNECTIONS: dict[str, int] = {}


@app.websocket("/ws/v4/evolution")
async def v4_evolution_stream(websocket: WebSocket, token: str = Query(default="")) -> None:
    """Stream BEAST v4 universe, computation, civilization, and substrate events."""
    try:
        decode_jwt(token, settings.jwt_secret)
    except JWTError:
        await websocket.close(code=1008, reason="valid token required")
        return
    address = websocket.client.host if websocket.client else "unknown"
    if _V4_WS_CONNECTIONS.get(address, 0) >= 10:
        await websocket.close(code=1013, reason="connection limit reached")
        return
    _V4_WS_CONNECTIONS[address] = _V4_WS_CONNECTIONS.get(address, 0) + 1
    await websocket.accept()
    cursor = 0
    try:
        while True:
            events = v4_state.events
            if cursor < len(events):
                for event in events[cursor:]:
                    await websocket.send_json(event)
                cursor = len(events)
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return
    finally:
        remaining = _V4_WS_CONNECTIONS.get(address, 1) - 1
        if remaining <= 0:
            _V4_WS_CONNECTIONS.pop(address, None)
        else:
            _V4_WS_CONNECTIONS[address] = remaining


_V5_WS_CONNECTIONS: dict[str, int] = {}


@app.websocket("/ws/v5/evolution")
async def v5_evolution_stream(websocket: WebSocket, token: str = Query(default="")) -> None:
    """Stream bounded v5 epoch, champion, and pollination events."""
    try:
        decode_jwt(token, settings.jwt_secret)
    except JWTError:
        await websocket.close(code=1008, reason="valid token required")
        return
    address = websocket.client.host if websocket.client else "unknown"
    if _V5_WS_CONNECTIONS.get(address, 0) >= 10:
        await websocket.close(code=1013, reason="connection limit reached")
        return
    _V5_WS_CONNECTIONS[address] = _V5_WS_CONNECTIONS.get(address, 0) + 1
    await websocket.accept()
    cursor = 0
    try:
        while True:
            events = v5_state.events
            if cursor < len(events):
                for event in events[cursor:]:
                    await websocket.send_json(event)
                cursor = len(events)
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return
    finally:
        remaining = _V5_WS_CONNECTIONS.get(address, 1) - 1
        if remaining <= 0:
            _V5_WS_CONNECTIONS.pop(address, None)
        else:
            _V5_WS_CONNECTIONS[address] = remaining


_V6_WS_CONNECTIONS: dict[str, int] = {}


@app.websocket("/ws/v6/evolution")
async def v6_evolution_stream(websocket: WebSocket, token: str = Query(default="")) -> None:
    """Stream bounded v6 interpreted-program evidence events."""
    try:
        decode_jwt(token, settings.jwt_secret)
    except JWTError:
        await websocket.close(code=1008, reason="valid token required")
        return
    address = websocket.client.host if websocket.client else "unknown"
    if _V6_WS_CONNECTIONS.get(address, 0) >= 10:
        await websocket.close(code=1013, reason="connection limit reached")
        return
    _V6_WS_CONNECTIONS[address] = _V6_WS_CONNECTIONS.get(address, 0) + 1
    await websocket.accept()
    queue = await v6_state.live_gp.subscribe()
    try:
        for event in v6_state.live_gp.history[-20:]:
            await websocket.send_json(event)
        while True:
            await websocket.send_json(await queue.get())
    except WebSocketDisconnect:
        return
    finally:
        await v6_state.live_gp.unsubscribe(queue)
        remaining = _V6_WS_CONNECTIONS.get(address, 1) - 1
        if remaining <= 0:
            _V6_WS_CONNECTIONS.pop(address, None)
        else:
            _V6_WS_CONNECTIONS[address] = remaining
