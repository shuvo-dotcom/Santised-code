# NFG Energy Analytics Docker Deployment

This directory contains the Docker deployment setup for the NFG Energy Analytics system with a chat-based frontend.

## Project Structure

```
deployment/
├── docker-compose.yml         # Main Docker Compose configuration
├── .env                       # Environment variables (create this file)
├── backend/                   # Backend API service
│   ├── Dockerfile             # Backend container configuration
│   ├── requirements.txt       # Python dependencies
│   └── api/                   # FastAPI application
│       └── main.py            # Main API endpoints
└── frontend/                  # React frontend application
    ├── Dockerfile             # Frontend container configuration
    ├── nginx.conf             # NGINX configuration for the frontend
    ├── public/                # Static assets
    └── src/                   # React source code
        ├── components/        # React components
        └── services/          # API services
```

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your system
- OpenAI API key for the LLM functionality

### Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo  # or your preferred model
DATA_FOLDER=./data
LOG_LEVEL=INFO
```

### Running the Application

1. Start the entire system:

```bash
docker-compose up -d
```

2. Access the application:
   - Frontend: http://localhost:4000
   - Backend API: http://localhost:9000
   - API Documentation: http://localhost:9000/docs

3. Stop the system:

```bash
docker-compose down
```

## Development

For development purposes, you can run each service separately:

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Features

- Modern chat interface for NFG energy analytics
- RESTful API endpoints for energy calculations
- WebSocket support for real-time chat
- Session management to maintain conversation context
- Visualization of energy metrics and analysis
