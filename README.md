# NFG Analytics Orchestrator

AI-driven data analyst for the Networks–Fuels–Generation (NFG) energy sector.

## Overview

This project implements a generic, LLM-driven analytics system for the energy sector that can:

- Parse natural language queries about energy metrics
- Dynamically determine required data and equations using LLM
- Load and process data from CSV files
- Calculate results with unit safety
- Provide structured responses with citations
- Collect comprehensive metrics about LLM usage and performance
- Support multiple LLM models with dynamic parameter handling

## Architecture

- **Semantic Layer**: Intent parsing and variable mapping
- **NFG Math**: Dynamic equation registry and evaluation
- **I/O Layer**: Generic CSV data store (via data_io module)
- **Engine**: End-to-end pipeline orchestration
- **Utils**: Metrics collection and configuration utilities
- **API**: FastAPI endpoints with health monitoring
- **API**: FastAPI endpoints for query processing

## Key Features

- No hardcoded dependencies - all content determined by LLM at runtime
- Configuration-driven design with YAML files
- Unit-safe calculations using SymPy and pint
- Streaming responses for real-time updates
- Docker-ready deployment

## Installation

### Prerequisites

- Python 3.10+
- OpenAI API key

### Local Setup

```bash
# Clone the repository
git clone <repo-url>
cd nfg-orchestrator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy example environment file and configure
cp .env-example .env
# Edit .env with your OpenAI API key and other settings

# Or set environment variables directly
export OPENAI_API_KEY=your-api-key
export OPENAI_PROJECT_ID=your-project-id  # For project-based API keys
export OPENAI_MODEL=gpt-5-mini  # Supported: gpt-5-mini, gpt-4o, etc.
export DATA_FOLDER=./data
```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run directly with Docker
docker build -t nfg-orchestrator .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-api-key \
  -e OPENAI_PROJECT_ID=your-project-id \
  -e OPENAI_MODEL=gpt-5-mini \
  nfg-orchestrator
```

## Usage

### API Endpoints

- `POST /query`: Process an NFG analytics query
  ```json
  {
    "text": "LCOE for nuclear Belgium 2050",
    "stream": false
  }
  ```

- `GET /health`: Health check endpoint

### Example Queries

- "LCOE for nuclear Belgium 2050"
- "Average generation for nuclear Belgium 2050"
- "Fuel cost share for nuclear Belgium 2050"

## Data Format

Place CSV files in the `data` folder with columns matching the expected property names:

- Required columns: `property_name`, `value`, `child_name`, `date_string`
- Optional columns: `category_name`, `unit_name`

## Configuration

- `semantic/config.yaml`: Canonical mappings for metrics, technologies, etc.
- `nfg_math/equations.yaml`: Equation registry with formulas and requirements

## License

[Add license information]

## Contributing

[Add contribution guidelines]
