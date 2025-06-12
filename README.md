# Skip Demo - RAG-Powered Podcast Search

A full-stack application that enables semantic search across podcast transcripts using RAG (Retrieval-Augmented Generation) with ChromaDB and OpenAI.

## 🏗 Architecture

- **Frontend**: Next.js (deployed on Vercel)
- **Backend**: FastAPI with ChromaDB (deployed on Render)
- **Database**: ChromaDB with persistent storage
- **AI**: OpenAI GPT-3.5-turbo + Sentence Transformers embeddings

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd skip-demo
   ```

2. **Configure environment**:
   ```bash
   # Create backend/.env file
   echo "OPENAI_API_KEY=your_openai_api_key_here" > backend/.env
   ```

3. **Run everything**:
   ```bash
   ./local-run.sh
   ```

   This script will:
   - Create Python virtual environment
   - Install all dependencies
   - Initialize local ChromaDB
   - Ingest podcast data
   - Start backend (http://localhost:8000)
   - Start frontend (http://localhost:3000)

## 📁 Project Structure

```
skip-demo/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── ingest.py            # Data ingestion script
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Container configuration
│   ├── data/
│   │   ├── transcripts/     # Podcast transcript files
│   │   └── metadata.json    # Episode metadata
│   └── chroma_db/          # Local database (auto-created)
├── frontend/
│   ├── src/app/            # Next.js app directory
│   ├── components/         # React components
│   └── package.json        # Node.js dependencies
├── local-run.sh            # Local development script
├── render.yaml             # Render deployment config
└── README.md               # This file
```

## 🔧 Local Development

### Manual Setup (Alternative to local-run.sh)

**Backend**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 ingest.py  # Initialize database
uvicorn main:app --reload --port 8000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

### Adding New Podcast Episodes

1. **Add transcript file**: `backend/data/transcripts/episode_XXX.txt`
2. **Update metadata**: Add entry to `backend/data/metadata.json`:
   ```json
   {
     "episode_XXX": {
       "title": "Episode Title",
       "description": "Episode description",
       "url": "https://episode-url.com"
     }
   }
   ```
3. **Re-run ingestion**: `python3 ingest.py`

### Local Database Management

- **Database location**: `backend/chroma_db/`
- **Reset database**: Delete `chroma_db` folder, run `python3 ingest.py`
- **Check status**: Visit `http://localhost:8000/db-status`

## 🌐 Production Deployment

### Render (Backend)

1. **Connect repository** to Render
2. **Configure environment variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key
3. **Deploy**: Render auto-detects `render.yaml` configuration

The `render.yaml` handles:
- Docker build process
- Persistent disk mounting (`/data`)
- Pre-deploy data ingestion
- Health checks

### Vercel (Frontend)

1. **Connect repository** to Vercel
2. **Set build settings**:
   - Framework: Next.js
   - Root directory: `frontend`
3. **Configure environment variables** (if needed)
4. **Deploy**: Auto-deploys on push to main

### Production Data Management

**Automatic ingestion**: Every Render deployment runs `python3 ingest.py`

**Adding new episodes in production**:
1. Add files to `backend/data/transcripts/` and update `backend/data/metadata.json`
2. Push to Git
3. Render auto-redeploys and re-ingests data

**Manual data management**: Use API endpoints or Render shell access

## 📊 API Documentation

### Health Endpoints

- `GET /health` - Basic health check
- `GET /health/ready` - Database readiness check

### Core Endpoints

- `POST /query` - Semantic search with AI response
  ```json
  {
    "question": "What career advice was mentioned?"
  }
  ```

### Debug Endpoints

- `GET /db-status` - Database statistics
- `GET /db-check` - Collection information  
- `GET /debug` - Full debugging information
- `POST /test-query` - Raw search without AI processing

### API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger documentation.

## 🔍 How It Works

### Data Ingestion Process

1. **Load transcripts** from `data/transcripts/*.txt`
2. **Chunk content** into overlapping segments (1000 words, 100 word overlap)
3. **Generate embeddings** using Sentence Transformers (`all-MiniLM-L6-v2`)
4. **Store in ChromaDB** with metadata (episode info, chunk index, etc.)

### Query Process

1. **Receive user question** via API
2. **Search ChromaDB** using semantic similarity
3. **Retrieve relevant chunks** (top 2 matches)
4. **Generate AI response** using OpenAI GPT-3.5-turbo with context
5. **Return answer** with source citations

### Embedding Model
- **Model**: `all-MiniLM-L6-v2` (384-dimensional embeddings)
- **Advantages**: Fast, lightweight, good performance
- **Language**: English optimized

## 🛠 Troubleshooting

### Common Issues

**"No documents found"**:
- Check if ingestion completed successfully
- Verify transcript files exist in `data/transcripts/`
- Check logs for ingestion errors

**Port conflicts**:
- Backend (8000): `lsof -ti:8000 | xargs kill -9`
- Frontend (3000): `lsof -ti:3000 | xargs kill -9`
- Or use the cleanup in `local-run.sh`

**Database corruption**:
- Delete `backend/chroma_db/` folder
- Run `python3 ingest.py` to rebuild

**OpenAI API errors**:
- Verify `OPENAI_API_KEY` is set correctly
- Check API quota and billing
- Monitor rate limits

### Debug Commands

```bash
# Check database status
curl http://localhost:8000/db-status

# Test search functionality  
curl -X POST http://localhost:8000/test-query \
  -H "Content-Type: application/json" \
  -d '{"question": "career advice"}'

# Check logs
docker logs <container-id>  # Production
tail -f backend/logs/*.log  # Local (if logging enabled)
```

### Performance Monitoring

**Local development**:
- Monitor memory usage during ingestion
- Check startup time for embedding model loading
- Profile query response times

**Production**:
- Use Render metrics dashboard
- Monitor database size growth
- Set up uptime monitoring for health endpoints

## 🔐 Security Notes

- **API Keys**: Never commit `.env` files or expose API keys
- **CORS**: Configure allowed origins in production
- **Rate Limiting**: Consider implementing for public deployments
- **Authentication**: Add user auth for production use cases

## 📈 Scaling Considerations

### Current Limits
- **Storage**: 1GB Render disk (suitable for ~500 episodes)
- **Memory**: ChromaDB loads entirely in memory
- **Concurrent Users**: Limited by FastAPI async capabilities

### Scaling Options
- **Database**: Migrate to cloud vector databases (Pinecone, Weaviate)
- **Compute**: Upgrade Render plan or use multiple instances
- **Storage**: Increase disk size or implement data archiving
- **Caching**: Add Redis for frequent queries

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test locally with `./local-run.sh`
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

### Development Guidelines
- Test all changes locally before pushing
- Update documentation for new features
- Follow existing code style and patterns
- Add appropriate error handling

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

- **Issues**: Open a GitHub issue for bugs or feature requests
- **Documentation**: Check the `/docs` folder for additional guides
- **API**: Visit `/docs` endpoint for interactive API documentation

---

**Built with ❤️ using FastAPI, ChromaDB, and OpenAI**