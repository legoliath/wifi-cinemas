# 📡 WiFi Cinémas

> Professional mobile WiFi management for the film industry in Montreal.

WiFi Cinémas provides turnkey internet connectivity on film sets using Starlink + 5G failover + UniFi mesh WiFi. This monorepo contains the mobile app (React Native) and backend API (FastAPI) that operators and crew use to manage, monitor, and troubleshoot connectivity in real time.

## Architecture

```
┌───────────────────────────────────────────────────────┐
│                     FILM SET                           │
│  Starlink Mini ──▶ Peplink BR1 Pro 5G ──▶ UniFi Mesh │
│  5G SIMs ────────▶        │                    │      │
│                           │              Film Crew     │
└───────────────────────────┼───────────────────────────┘
                     ┌──────▼──────┐
                     │  FastAPI    │
                     │  Backend    │
                     ├─────────────┤
                     │ PostgreSQL  │
                     │ Redis       │
                     └──────┬──────┘
                     ┌──────▼──────┐
                     │  Mobile App │
                     │ (iOS/Android)│
                     └─────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Mobile | React Native + Expo, TypeScript |
| UI | React Native Paper (Material Design 3) |
| State | Zustand |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL + Redis |
| Auth | Firebase Authentication |
| Real-time | WebSocket |
| Hardware APIs | UniFi Controller, Peplink InControl, Starlink gRPC |

## Quick Start

### Backend
```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker-compose up -d postgres redis
alembic upgrade head
uvicorn app.main:app --reload
```

### Mobile
```bash
cd mobile
npm install
npx expo start
```

## Docs
- [Architecture](docs/architecture.md)
- [API Specification](docs/api-spec.md)
- [Firebase Setup](docs/firebase-setup.md)
- [Hardware Integration](docs/hardware-integration.md)
- [Deployment](docs/deployment.md)

## License
MIT
