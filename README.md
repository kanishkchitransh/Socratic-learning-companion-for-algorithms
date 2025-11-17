# Socratic Learning Companion for Algorithms

An intelligent tutoring system that uses the Socratic method to teach algorithms and data structures theory. Focuses on mathematical reasoning, proofs, and complexity analysis using material from MIT 6.006 and Kleinberg-Tardos Algorithm Design textbook.

## 🎯 Features

- **Socratic Dialogue**: Guides students to discover concepts through questions, not direct explanations
- **Multi-Agent System**: Orchestrator, Curriculum Planner, Tutor, Problem Generator, and Assessor agents
- **Theory-Focused**: Emphasizes proofs, mathematical reasoning, and complexity analysis (no code execution)
- **Adaptive Learning**: Tracks progress, identifies misconceptions, and adjusts difficulty
- **Rich Math Support**: Renders LaTeX notation for mathematical expressions
- **Persistent Progress**: SQLite database tracks learning history and misconceptions

## 🏗️ Architecture

### Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Multi-Agent**: LangGraph for orchestration
- **LLM**: Google Gemini 2.5 Flash
- **Vector DB**: ChromaDB (local, persistent)
- **Database**: SQLite for student progress and conversations
- **PDF Processing**: PyMuPDF for text extraction
- **Frontend** (planned): Next.js + React + Tailwind CSS

### System Components

1. **Orchestrator Agent**: Routes messages to appropriate specialist agents
2. **Curriculum Planner Agent**: Recommends topics based on prerequisites and progress
3. **Tutor Agent**: Conducts Socratic dialogue (asks guiding questions)
4. **Problem Generator Agent**: Creates practice problems for theory/proofs/complexity
5. **Assessor Agent**: Evaluates understanding and identifies misconceptions

## 📁 Project Structure

```
.
├── data/
│   ├── raw_pdfs/
│   │   ├── kleinberg_tardos/      # Algorithm Design textbook PDFs
│   │   └── mit_6006_lectures/     # MIT 6.006 lecture notes
│   ├── processed/                  # Processed chunks (JSON)
│   └── embeddings/
│       └── chroma_db/             # ChromaDB persistent storage
├── src/
│   ├── agents/                    # LangGraph agents (Phase 2)
│   ├── api/                       # FastAPI endpoints (Phase 3)
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── db_manager.py          # SQLite operations
│   │   └── chroma_manager.py      # ChromaDB operations
│   ├── processing/
│   │   ├── base_processor.py      # Base PDF processor
│   │   ├── textbook_processor.py  # Fixed-size chunking
│   │   └── process_pdfs.py        # Main processing pipeline
│   └── utils/
│       ├── config.py               # Configuration management
│       └── logging_config.py       # Structured logging
├── tests/                          # Unit tests
├── requirements.txt
├── .env                            # Environment variables (create from .env.example)
└── README.md
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.11 or higher
- Google Gemini API key
- Kleinberg-Tardos Algorithm Design textbook PDFs

### Installation

1. **Clone the repository**
   ```bash
   cd Socratic-learning-companion-for-algorithms
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Google Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

5. **Add PDF files**

   Place your Kleinberg-Tardos textbook PDFs in:
   ```
   data/raw_pdfs/kleinberg_tardos/
   ```

### Database Initialization

Initialize the SQLite database and ChromaDB collections:

```bash
python -m src.init_database
```

This will:
- Create SQLite tables (students, topics, progress, conversations, etc.)
- Initialize curriculum with 8 topics from Kleinberg-Tardos
- Create ChromaDB collections (textbook_chunks, lecture_notes, prerequisite_concepts)

### PDF Processing

Process the textbook PDFs and generate embeddings:

```bash
python -m src.processing.process_pdfs
```

This will:
- Extract text from PDFs with structure preservation
- Create fixed-size chunks (512 tokens, 50 token overlap)
- Classify chunks (theorem, proof, definition, example, exercise)
- Preserve LaTeX math notation
- Generate embeddings using Gemini
- Store in ChromaDB
- Save processed chunks to `data/processed/` (JSON)
- Generate processing statistics and verification report

**Expected output:**
- `data/processed/*_chunks.json` - Processed chunks for each PDF
- `data/processed/processing_stats.json` - Processing statistics
- `data/processed/verification_report.json` - Quality verification results
- `data/embeddings/chroma_db/` - ChromaDB persistent storage

## 📊 Database Schema

### SQLite Tables

- **students**: User profiles, background, learning goals
- **topics**: Curriculum topics with difficulty and prerequisites
- **topic_prerequisites**: Prerequisite relationships
- **student_progress**: Mastered/struggling topics, understanding scores
- **conversations**: Full conversation history with agent metadata
- **misconceptions**: Tracked misconceptions with correction attempts
- **assessments**: Student responses and evaluations
- **sessions**: Learning session metadata

### ChromaDB Collections

- **textbook_chunks**: Fixed-size chunks from Kleinberg-Tardos
  - Metadata: chapter, section, chunk_type, has_math, concepts
- **lecture_notes**: Hierarchical chunks from MIT 6.006 (Phase 2)
- **prerequisite_concepts**: For curriculum planning (Phase 2)

## 🎓 Curriculum Topics

The system includes 8 topics from Kleinberg-Tardos with prerequisites:

1. **Introduction to Algorithms** (Difficulty: 1)
   - Stable matching, Gale-Shapley algorithm

2. **Algorithm Analysis** (Difficulty: 2)
   - Asymptotic notation, computational tractability
   - Prerequisite: Introduction to Algorithms

3. **Graphs** (Difficulty: 2)
   - Graph connectivity, BFS, DFS, trees
   - Prerequisite: Algorithm Analysis

4. **Greedy Algorithms** (Difficulty: 3)
   - Interval scheduling, Huffman codes, MST
   - Prerequisite: Graphs

5. **Divide and Conquer** (Difficulty: 3)
   - Mergesort, recurrence relations
   - Prerequisite: Algorithm Analysis

6. **Dynamic Programming** (Difficulty: 4)
   - Weighted interval scheduling, sequence alignment
   - Prerequisites: Greedy Algorithms (recommended), Divide and Conquer (recommended)

7. **Network Flow** (Difficulty: 4)
   - Max-flow min-cut, Ford-Fulkerson, bipartite matching
   - Prerequisites: Graphs (required), Greedy Algorithms (recommended)

8. **NP-Completeness** (Difficulty: 5)
   - P, NP, NP-complete problems, reductions
   - Prerequisites: Algorithm Analysis (required), Dynamic Programming (recommended)

## 🔧 Development Phases

### Phase 1: Foundation & PDF Processing ✅ COMPLETE
- ✅ Project structure setup
- ✅ SQLite schema and database manager
- ✅ ChromaDB setup and manager
- ✅ PDF processing pipeline (fixed-size chunking)
- ✅ Chunk classification (theorem/proof/definition)
- ✅ Embedding generation and storage
- ✅ Test suite: 51/51 tests passing (100%)

### Phase 2: Multi-Agent System ✅ COMPLETE
- ✅ LangGraph orchestration
- ✅ Agent state management (TypedDict)
- ✅ Implemented 5 specialized agents:
  - ✅ Orchestrator Agent (routes messages)
  - ✅ Curriculum Planner Agent (recommends topics)
  - ✅ Tutor Agent (Socratic method)
  - ✅ Problem Generator Agent (creates practice problems)
  - ✅ Assessor Agent (evaluates understanding)
- ✅ Agent prompt templates for Gemini 2.5 Flash
- ✅ Conditional routing based on state
- ✅ Test suite: 17/17 tests passing (100%)

### Phase 3: FastAPI Backend ✅ COMPLETE
- ✅ REST API endpoints (8 endpoints)
- ✅ WebSocket for real-time dialogue
- ✅ Error handling and validation
- ✅ Pydantic models for requests/responses
- ✅ CORS middleware
- ✅ OpenAPI documentation (auto-generated)
- ✅ Integration with multi-agent system
- ✅ Test suite: 19/21 tests passing (95%)*
  * 2 tests require Gemini API access (SSL restricted in test environment)

### Phase 4: Frontend ✅ COMPLETE
- ✅ Simple HTML/CSS/JavaScript interface
- ✅ Student registration form
- ✅ Session management
- ✅ Chat interface with Socratic dialogue
- ✅ Progress dashboard
- ✅ Curriculum graph visualization
- ✅ Responsive design
- ✅ Real-time status updates

### Phase 5: Integration & Testing (CURRENT)
- [ ] End-to-end testing
- [ ] Full integration test with running API
- [ ] Performance testing
- [ ] Documentation updates

## 🚀 Running the Application

### Quick Start

1. **Start the Backend Server**
   ```bash
   ./start_server.sh
   ```

   Or manually:
   ```bash
   python -m uvicorn src.api.main:app --reload --port 8000
   ```

2. **Open the Frontend**

   Open `frontend/index.html` in your web browser (Chrome/Firefox/Safari)

3. **API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Application Workflow

1. **Register as a Student** - Provide your details and learning goals
2. **Start a Session** - Choose a topic from the curriculum
3. **Engage in Socratic Dialogue** - The tutor will guide you through questions
4. **Track Progress** - View your understanding scores and mastered topics
5. **Explore Curriculum** - See all available topics and their prerequisites

### API Endpoints

- `POST /api/student/register` - Register new student
- `GET /api/student/{user_id}` - Get student information
- `POST /api/session/start` - Start learning session
- `POST /api/chat` - Send message (multi-agent processing)
- `GET /api/student/{user_id}/progress` - Get progress summary
- `GET /api/curriculum/graph` - Get full curriculum
- `GET /api/topic/{topic_id}` - Get topic details
- `WS /ws/chat/{user_id}/{session_id}` - WebSocket for real-time chat

## 📝 Advanced Usage

After completing initial setup:

1. **Verify ChromaDB**
   ```python
   from src.database.chroma_manager import get_chroma_manager

   chroma = get_chroma_manager()
   stats = chroma.get_collection_stats("textbook_chunks")
   print(f"Total chunks: {stats['count']}")
   ```

2. **Test Retrieval**
   ```python
   results = chroma.query(
       collection_name="textbook_chunks",
       query_text="What is dynamic programming?",
       n_results=3
   )
   print(results['documents'][0][0])  # Top result
   ```

3. **Check Processing Stats**
   ```bash
   cat data/processed/processing_stats.json
   ```

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

## 📄 Logging

Structured logging with JSON output:
- All agent actions logged with execution time
- Retrievals logged (query, sources, relevance scores)
- Assessments logged (scores, misconceptions)
- Errors logged with full context

Logs location: Console output (can be configured to file)

## 🤝 Contributing

This is a learning project. Contributions welcome!

## 📚 References

- Kleinberg, J., & Tardos, É. (2005). *Algorithm Design*. Addison-Wesley.
- MIT 6.006: Introduction to Algorithms (Fall 2011)

## 📄 License

MIT License

## 🔮 Future Enhancements

- Multi-modal support (diagrams, visualizations)
- Collaborative learning (student groups)
- Spaced repetition for long-term retention
- Export learning transcripts
- Integration with LeetCode/competitive programming
