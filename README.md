# AI-Powered Document Organization Tool

An intelligent document management system with AI-powered organization, tagging, and search capabilities.

## Features

- 🤖 AI-powered document analysis and categorization
- 📁 Smart folder organization
- 🏷️ Automatic tagging and metadata extraction
- 🔍 Semantic search across documents
- 📄 Support for PDF, DOCX, XLSX, PPTX, and images
- 🔒 Secure document storage
- 📊 Document insights and analytics

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

2. Copy the environment template:
```bash
cp .env.example .env
```

3. Edit `.env` and add your Anthropic API key:
```bash
ANTHROPIC_API_KEY=your_actual_api_key_here
```

4. Build and run with Docker Compose:
```bash
docker-compose up --build
```

5. Access the application at `http://localhost:8000`

## Deployment

### Using Docker Hub

1. Build the image:
```bash
docker build -t yourusername/doc-organizer:latest .
```

2. Push to Docker Hub:
```bash
docker push yourusername/doc-organizer:latest
```

3. Run on your server:
```bash
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  -v /path/to/data:/app/data \
  yourusername/doc-organizer:latest
```

### Using GitHub Container Registry (Automatic)

This repository includes GitHub Actions that automatically build and push Docker images to GitHub Container Registry on every push to `main`.

1. Ensure GitHub Actions is enabled for your repository
2. Push to the `main` branch
3. The Docker image will be available at: `ghcr.io/yourusername/your-repo-name:latest`

To pull and run:
```bash
docker pull ghcr.io/yourusername/your-repo-name:latest
docker run -d -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  ghcr.io/yourusername/your-repo-name:latest
```

### Environment Variables

See `.env.example` for all available configuration options.

Required:
- `ANTHROPIC_API_KEY`: Your Anthropic API key

Optional but recommended:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string for caching
- `SECRET_KEY`: Secret key for session management

## Architecture

```
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core business logic
│   ├── models/           # Database models
│   ├── services/         # AI and document processing
│   └── utils/            # Utility functions
├── data/                 # Persistent data (mounted volume)
├── tests/                # Test suite
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Multi-container setup
└── requirements.txt      # Python dependencies
```

## AI Features

### Document Analysis
- Automatic extraction of key information
- Entity recognition (dates, names, organizations)
- Topic classification

### Smart Organization
- AI-suggested folder structures
- Automatic categorization
- Duplicate detection

### Semantic Search
- Natural language queries
- Context-aware results
- Relationship mapping

## Development

### Running Tests
```bash
docker-compose exec app pytest
```

### Database Migrations
```bash
docker-compose exec app alembic upgrade head
```

### Logs
```bash
docker-compose logs -f app
```

## Security Notes

- Never commit `.env` files with real credentials
- Change `SECRET_KEY` in production
- Use environment-specific configurations
- Enable HTTPS in production
- Regularly update dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open a GitHub issue.
