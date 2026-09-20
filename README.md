# ExcelPlorer

**AI Spreadsheet Mapping Framework** — A desktop-first web application that converts AI-generated product information into marketplace bulk-upload Excel files.

ExcelPlorer bridges the gap between AI vision models (ChatGPT, Gemini, Claude) and marketplace seller dashboards. Upload a marketplace Excel template, get an optimized prompt, paste it into any AI with your product images, paste the AI's JSON response back, and receive a perfectly formatted Excel file ready for bulk upload.

---

## Screenshots

> Screenshots will be added as each phase is completed.

| Upload | Analysis | Prompt | Preview |
|--------|----------|--------|---------|
| *Coming soon* | *Coming soon* | *Coming soon* | *Coming soon* |

---

## Features

### Core Workflow
- **Drag-and-drop upload** — Accept `.xlsx` and `.xls` marketplace templates
- **Automatic workbook analysis** — Inspect headers, dropdowns, validations, merged cells, hidden sheets, formulas, named ranges, and more
- **Dual-prompt generation** — Generates a Rules prompt (template constraints) and a Data prompt (extraction shape)
- **Product Library** — Auto-saves generated product JSONs (identified by SKU) for future editing and reuse
- **JSON import & validation** — Paste AI-returned JSON with instant syntax and schema validation
- **Auto-correction engine** — Automatically fix common mistakes (typos, casing, booleans, whitespace)
- **Formatting-preserving Excel writer** — Write data into the original template preserving all formatting, styles, and validation
- **Detailed validation reports** — Export as TXT, HTML, or JSON

### Architecture
- **Generic framework** — Not hardcoded to any marketplace
- **Plugin system** — Marketplace-specific plugins (Flipkart first, Amazon/Meesho/Shopify stubs)
- **Future-ready AI layer** — Adapter interfaces for OpenAI, Gemini, Claude, Ollama integration
- **Product Library Persistence** — Local SQLite-based product auto-saving (keyed by SKU)
- **Modular codebase** — Clean separation of concerns with type hints, docstrings, and logging

### UI
- Modern dark theme with glassmorphism
- 7-tab interface (Upload → Analysis → Prompt → JSON → Validation → Preview → Export)
- Responsive layout
- Micro-animations and visual feedback
- Editable preview table with cell-level status highlighting

---

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Edge, Firefox)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd excelplorer

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

The application will start a local server and automatically open your browser to `http://localhost:5000`.

---

## Usage

### Step-by-Step Workflow

1. **Upload** — Drag and drop (or click to browse) your marketplace Excel template (`.xlsx` or `.xls`)
2. **Review Analysis** — Inspect detected sheets, columns, required fields, dropdown values, and validation rules
3. **Copy Prompts** — Copy the auto-generated **Rules Prompt** and **Data Prompt** from the AI Prompt tab
4. **Paste into AI** — Open your preferred AI, upload product images, paste the Rules Prompt, then the Data Prompt
5. **Copy AI Response** — The AI returns structured JSON — copy it
6. **Paste JSON** — Paste the JSON into ExcelPlorer's JSON Input tab (products are auto-saved to your library)
7. **Review Validation** — Fix any errors or warnings; auto-corrections are applied automatically
8. **Preview** — Review the data table; edit cells manually if needed
9. **Export** — Download the completed Excel file, validation report, and session logs

### Configuration

Edit `config.py` to customize:
- Server port (default: `5000`)
- Upload file size limit (default: `50MB`)
- Data directory paths
- Logging level

---

## Folder Structure

```
excelplorer/
├── README.md                          # This file
├── PRD.md                             # Product Requirements Document
├── architecture.md                    # Architecture documentation
├── phases.md                          # Phase tracker
├── memory.md                          # Engineering journal
├── tasks.md                           # Task tracker
├── requirements.txt                   # Python dependencies
├── config.py                          # Application configuration
├── run.py                             # Entry point
│
├── backend/
│   ├── __init__.py
│   ├── app.py                         # Flask app factory
│   ├── api/                           # REST API route blueprints
│   │   ├── upload.py
│   │   ├── analysis.py
│   │   ├── prompt.py
│   │   ├── validate.py
│   │   ├── preview.py
│   │   ├── export.py
│   │   ├── report.py
│   │   └── products.py
│   ├── core/                          # Core business logic
│   │   ├── analyzer.py                # Workbook analysis engine
│   │   ├── schema.py                  # Internal schema models
│   │   ├── prompt_generator.py        # AI prompt generation
│   │   ├── validator.py               # Data validation engine
│   │   ├── auto_corrector.py          # Auto-correction engine
│   │   ├── excel_writer.py            # Excel writing engine
│   │   ├── report_generator.py        # Report generator
│   │   └── session_manager.py         # Legacy session management
│   ├── plugins/                       # Marketplace plugins
│   │   ├── base.py                    # Abstract plugin base
│   │   ├── registry.py                # Plugin discovery
│   │   ├── flipkart.py               # Flipkart plugin
│   │   ├── amazon.py                  # Amazon stub
│   │   └── meesho.py                  # Meesho stub
│   ├── ai/                            # Future AI integration
│   │   ├── base.py                    # Abstract AI adapter
│   │   ├── openai_adapter.py          # OpenAI stub
│   │   ├── gemini_adapter.py          # Gemini stub
│   │   └── ollama_adapter.py          # Ollama stub
│   └── utils/                         # Shared utilities
│       ├── excel_utils.py
│       ├── json_utils.py
│       └── logging_config.py
│
├── frontend/
│   ├── index.html                     # Main SPA page
│   ├── css/
│   │   ├── main.css                   # Design system & core styles
│   │   ├── components.css             # Reusable component styles
│   │   └── animations.css             # Micro-animations
│   └── js/
│       ├── app.js                     # Main application controller
│       ├── api.js                     # Backend API client
│       ├── upload.js                  # Upload tab
│       ├── analysis.js                # Analysis tab
│       ├── prompt.js                  # Prompt tab
│       ├── json-input.js              # JSON input tab
│       ├── validator.js               # Validation tab
│       ├── preview.js                 # Preview tab
│       ├── export.js                  # Export tab
│       ├── report.js                  # Report tab
│       └── utils.js                   # Shared utilities
│
├── data/
│   ├── products/                      # Auto-saved JSON products
│   ├── sessions/                      # Session storage
│   └── exports/                       # Export output
│
├── docs/
│   ├── architecture.md                # Detailed architecture
│   └── plugin_guide.md               # Plugin development guide
│
└── tests/
    ├── test_analyzer.py
    ├── test_validator.py
    └── test_auto_corrector.py
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | ≥3.0 | Local HTTP server and REST API |
| flask-cors | ≥4.0 | Cross-origin resource sharing |
| openpyxl | ≥3.1 | Read/write .xlsx files |
| pandas | ≥2.0 | Data manipulation |
| numpy | ≥1.24 | Numerical operations |
| xlrd | ≥2.0 | Legacy .xls reading |
| python-dateutil | ≥2.8 | Date parsing |

---


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Follow the documentation-first workflow:
   - Update `PRD.md` with new requirements
   - Update `architecture.md` if architecture changes
   - Add tasks to `tasks.md`
   - Implement the feature
   - Update `phases.md` and `memory.md`
4. Write tests for new functionality
5. Submit a pull request

### Code Standards
- Python: Type hints on all functions, docstrings on all public methods
- JavaScript: JSDoc comments on all functions
- CSS: Use CSS custom properties for theming
- All files must have consistent formatting

---

## License

MIT License — See [LICENSE](LICENSE) for details.
