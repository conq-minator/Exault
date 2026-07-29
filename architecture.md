# Architecture Documentation

## ExcelPlorer — AI Spreadsheet Mapping Framework

**Version:** 1.0.0  
**Last Updated:** 2026-07-23

---

## 1. High-Level Architecture

```mermaid
graph TB
    subgraph User["User"]
        Browser["Web Browser"]
        AI["AI Model<br/>(ChatGPT / Gemini / Claude)"]
    end

    subgraph ExcelPlorer["ExcelPlorer (localhost:5000)"]
        subgraph FE["Frontend Layer"]
            HTML["index.html (SPA)"]
            CSS["CSS Design System"]
            JS["JavaScript Modules"]
        end

        subgraph API["API Layer (Flask)"]
            Routes["REST API Routes<br/>(Blueprints)"]
        end

        subgraph Core["Core Engine"]
            Analyzer["Workbook Analyzer"]
            Schema["Schema Models"]
            PromptGen["Prompt Generator"]
            Validator["Validation Engine"]
            AutoFix["Auto Corrector"]
            Writer["Excel Writer"]
            Reporter["Report Generator"]
            ProductMgr["Product Library Manager"]
        end

        subgraph Ext["Extension Layer"]
            PluginMgr["Plugin Registry"]
            Plugins["Marketplace Plugins"]
            AIAdapters["AI Adapters (Future)"]
        end

        subgraph Data["Data Layer"]
            SQLite["SQLite DB"]
            FileStore["File Storage"]
        end
    end

    Browser <-->|HTTP/REST| Routes
    Routes --> Analyzer
    Routes --> PromptGen
    Routes --> Validator
    Routes --> Writer
    Routes --> Reporter
    Routes --> ProductMgr
    Analyzer --> Schema
    PromptGen --> Schema
    Validator --> Schema
    Writer --> Schema
    Analyzer --> PluginMgr
    Validator --> PluginMgr
    PromptGen --> PluginMgr
    PluginMgr --> Plugins
    ProductMgr --> FileStore
    Writer --> FileStore

    Browser -.->|"1. Copy prompt"| AI
    AI -.->|"2. Paste JSON"| Browser
```

---

## 2. Folder Structure & Module Responsibilities

```
excelplorer/
├── run.py                    # Entry point — starts Flask, opens browser
├── config.py                 # All configuration constants
│
├── backend/
│   ├── app.py                # Flask app factory, blueprint registration
│   │
│   ├── api/                  # HTTP request/response handling ONLY
│   │   ├── upload.py         # POST /api/upload
│   │   ├── analysis.py       # GET /api/analysis/<id>
│   │   ├── prompt.py         # GET /api/prompt/<id>
│   │   ├── validate.py       # POST /api/validate/<id>
│   │   ├── preview.py        # GET/POST /api/preview/<id>
│   │   ├── export.py         # POST/GET /api/export/<id>
│   │   ├── report.py         # GET /api/report/<id>
│   │   └── products.py       # CRUD /api/products
│   │
│   ├── core/                 # ALL business logic lives here
│   │   ├── schema.py         # Dataclass models (WorkbookSchema, SheetSchema, etc.)
│   │   ├── analyzer.py       # Reads Excel, produces WorkbookSchema
│   │   ├── prompt_generator.py  # WorkbookSchema → prompt text
│   │   ├── validator.py      # JSON + WorkbookSchema → ValidationResult
│   │   ├── auto_corrector.py # JSON + WorkbookSchema → corrected JSON
│   │   ├── excel_writer.py   # JSON + template → filled Excel
│   │   ├── report_generator.py  # ValidationResult → report (TXT/HTML/JSON)
│   │   └── session_manager.py   # Legacy SQLite session manager (kept for older endpoints)
│   │
│   ├── plugins/              # Marketplace-specific extensions
│   │   ├── base.py           # Abstract MarketplacePlugin class
│   │   ├── registry.py       # Plugin discovery and selection
│   │   ├── flipkart.py       # Flipkart detection, rules, mappings
│   │   ├── amazon.py         # Stub
│   │   └── meesho.py         # Stub
│   │
│   ├── ai/                   # Future AI direct-call adapters
│   │   ├── base.py           # Abstract AIAdapter class
│   │   ├── openai_adapter.py
│   │   ├── gemini_adapter.py
│   │   └── ollama_adapter.py
│   │
│   └── utils/                # Stateless helpers
│       ├── excel_utils.py    # Excel cell/range helpers
│       ├── json_utils.py     # JSON parsing/formatting helpers
│       └── logging_config.py # Logging configuration
│
├── frontend/                 # Served as Flask static files
│   ├── index.html
│   ├── css/
│   │   ├── main.css          # Design tokens, layout, theme
│   │   ├── components.css    # Buttons, cards, tables, inputs
│   │   └── animations.css    # Keyframes, transitions
│   └── js/
│       ├── app.js            # State management, tab routing
│       ├── api.js            # fetch() wrapper for all endpoints
│       ├── upload.js         # Drag-drop, file validation, upload
│       ├── analysis.js       # Render analysis results
│       ├── prompt.js         # Prompt display, copy, stats
│       ├── json-input.js     # JSON paste, validate, format
│       ├── validator.js      # Render validation issues
│       ├── preview.js        # Editable data table
│       ├── export.js         # Download triggers
│       ├── report.js         # Report rendering
│       └── utils.js          # DOM helpers, formatters, toasts
│
├── data/
│   ├── products/             # Auto-saved JSON products (keyed by SKU)
│   ├── sessions/             # Uploaded templates + exports per session
│   │   └── <session_id>/     # Each session gets a directory
│   │       ├── template.xlsx # Uploaded file
│   │       ├── schema.json   # Cached analysis
│   │       ├── input.json    # User-pasted JSON
│   │       ├── output.xlsx   # Generated Excel
│   │       └── report.*      # Generated reports
│   └── excelplorer.db        # SQLite database
│
└── tests/
```

### Responsibility Boundaries

| Layer | Responsibility | Does NOT |
|-------|---------------|----------|
| **API** | Parse HTTP requests, call core, return HTTP responses | Contain business logic |
| **Core** | All business logic, data processing, validation | Know about HTTP or frontend |
| **Plugins** | Marketplace-specific rules, detection, mappings | Modify core behavior directly |
| **AI** | Interface definition for future AI API calls | Make actual API calls in v1.0 |
| **Utils** | Stateless helper functions | Hold state or business logic |
| **Frontend** | User interaction, display, API communication | Process data or validate deeply |

---

## 3. Frontend Architecture

### Single-Page Application (SPA)

The frontend is a vanilla HTML/CSS/JS SPA. No frameworks. No build step.

```mermaid
graph LR
    subgraph SPA["index.html"]
        TabNav["Tab Navigation Bar"]
        TabPanels["Tab Content Panels (8)"]
        Sidebar["History Sidebar"]
        Toasts["Toast Container"]
    end

    subgraph JSModules["JavaScript Modules"]
        AppJS["app.js<br/>State + Routing"]
        ApiJS["api.js<br/>HTTP Client"]
        UploadJS["upload.js"]
        AnalysisJS["analysis.js"]
        PromptJS["prompt.js"]
        JsonJS["json-input.js"]
        ValidatorJS["validator.js"]
        PreviewJS["preview.js"]
        ExportJS["export.js"]
        ReportJS["report.js"]
        HistoryJS["history.js"]
        UtilsJS["utils.js"]
    end

    AppJS --> ApiJS
    UploadJS --> ApiJS
    AnalysisJS --> ApiJS
    PromptJS --> ApiJS
    JsonJS --> ApiJS
    ValidatorJS --> ApiJS
    PreviewJS --> ApiJS
    ExportJS --> ApiJS
    ReportJS --> ApiJS
    HistoryJS --> ApiJS
```

### State Management

`app.js` maintains a simple global state object:

```javascript
const AppState = {
    currentTab: 'upload',
    sessionId: null,
    fileInfo: null,
    analysis: null,
    prompt: null,
    jsonData: null,
    validationResult: null,
    previewData: null,
    report: null,
    sessions: []
};
```

Tab modules read/write to `AppState` and call `api.js` for server communication.

---

## 4. Backend Architecture

### Flask App Factory Pattern

```python
# backend/app.py
def create_app(config=None):
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    # Register blueprints
    # Configure CORS
    # Set up logging
    # Initialize session manager
    return app
```

### Blueprint Organization

Each API module is a Flask Blueprint:

```mermaid
graph TB
    App["Flask App"] --> Upload["upload_bp<br/>/api/upload"]
    App --> Analysis["analysis_bp<br/>/api/analysis"]
    App --> Prompt["prompt_bp<br/>/api/prompt"]
    App --> Validate["validate_bp<br/>/api/validate"]
    App --> Preview["preview_bp<br/>/api/preview"]
    App --> Export["export_bp<br/>/api/export"]
    App --> Report["report_bp<br/>/api/report"]
    App --> Session["session_bp<br/>/api/sessions"]
```

---

## 5. Data Flow

### Complete Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as Flask API
    participant AN as Analyzer
    participant PG as Prompt Generator
    participant AI as External AI
    participant VA as Validator
    participant AC as Auto Corrector
    participant EW as Excel Writer
    participant RG as Report Generator

    U->>FE: Upload .xlsx template
    FE->>API: POST /api/upload
    API->>AN: analyze(file)
    AN-->>API: WorkbookSchema
    API-->>FE: analysis result

    FE->>API: GET /api/prompt/{id}
    API->>PG: generate(schema)
    PG-->>API: prompt text + stats
    API-->>FE: prompt

    U->>FE: Copy prompt
    U->>AI: Paste prompt + images
    AI-->>U: JSON response
    U->>FE: Paste JSON

    FE->>API: POST /api/validate/{id}
    API->>AC: correct(json, schema)
    AC-->>API: corrected JSON + corrections log
    API->>VA: validate(corrected_json, schema)
    VA-->>API: ValidationResult
    API-->>FE: validation + preview data

    U->>FE: Review & edit preview
    FE->>API: POST /api/preview/{id}/edit

    U->>FE: Click Export
    FE->>API: POST /api/export/{id}
    API->>EW: write(template, data, schema)
    EW-->>API: output.xlsx path
    API->>RG: generate(validation_result)
    RG-->>API: report
    API-->>FE: download links

    U->>FE: Download files
```

---

## 6. Excel Processing Pipeline

### Workbook Analysis

```mermaid
flowchart TD
    Input["Upload Excel File"] --> Format{"File Format?"}
    Format -->|.xlsx| OPXL["Open with openpyxl"]
    Format -->|.xls| XLRD["Open with xlrd<br/>(read-only)"]

    OPXL --> Sheets["Iterate All Sheets"]
    XLRD --> Convert["Convert to openpyxl-compatible schema"]
    Convert --> Sheets

    Sheets --> PerSheet["For Each Sheet"]
    PerSheet --> Headers["Detect Header Row"]
    PerSheet --> Merged["Map Merged Cells"]
    PerSheet --> Hidden["Check Hidden State"]

    Headers --> Columns["For Each Column"]
    Columns --> ColName["Extract Name"]
    Columns --> DV["Read Data Validation"]
    Columns --> Samples["Sample Data Values"]
    Columns --> Types["Infer Data Type"]
    Columns --> Required["Detect Required Status"]

    DV --> DVType{"Validation Type?"}
    DVType -->|"List (inline)"| InlineVals["Parse comma-separated values"]
    DVType -->|"List (formula)"| FormulaRef["Resolve sheet!range reference"]
    DVType -->|"Other"| OtherDV["Record rule type + params"]
    FormulaRef --> ReadCells["Read values from referenced cells"]

    ColName --> Schema["Build ColumnSchema"]
    InlineVals --> Schema
    ReadCells --> Schema
    OtherDV --> Schema
    Samples --> Schema
    Types --> Schema
    Required --> Schema

    Schema --> SheetSchema["Build SheetSchema"]
    SheetSchema --> WBSchema["Build WorkbookSchema"]
    WBSchema --> Plugin["Run Plugin Detection"]
    Plugin --> Output["Return AnalysisResult"]
```

### Excel Writing

```mermaid
flowchart TD
    Input["Validated JSON Data"] --> Open["Open ORIGINAL template with openpyxl"]
    Open --> FindHeader["Find header row in target sheet"]
    FindHeader --> MapCols["Map column names → column indices"]
    MapCols --> DataStart["Determine data start row<br/>(header + 1)"]

    DataStart --> Loop["For each product in JSON"]
    Loop --> Row["For each field in product"]
    Row --> Match{"Column name<br/>matches schema?"}
    Match -->|Yes| Write["Write value to cell"]
    Match -->|No| Skip["Skip (log warning)"]
    Write --> Preserve["Preserve cell style:<br/>font, fill, border,<br/>number_format, alignment"]

    Loop --> NextRow["Move to next row"]
    NextRow --> Loop

    Loop --> Save["Save workbook"]
    Save --> Output["Return output file path"]
```

---

## 7. Prompt Generation Pipeline

```mermaid
flowchart TD
    Schema["WorkbookSchema"] --> Plugin{"Marketplace<br/>plugin detected?"}
    Plugin -->|Yes| PluginPrompt["Get plugin prompt additions"]
    Plugin -->|No| Generic["Use generic instructions"]

    Schema --> Header["Build header section:<br/>Task description, output format rules"]
    Schema --> Fields["Build field listing:<br/>For each column: name, required/optional,<br/>type, allowed values, max length"]
    Schema --> Example["Build example JSON:<br/>Matching exact schema structure"]
    Schema --> Rules["Build strict rules:<br/>JSON only, exact keys, no markdown,<br/>empty for unknown, multiple products"]

    PluginPrompt --> Combine["Combine all sections"]
    Generic --> Combine
    Header --> Combine
    Fields --> Combine
    Example --> Combine
    Rules --> Combine

    Combine --> Stats["Calculate stats:<br/>char count, word count, token estimate"]
    Stats --> Output["Return prompt + stats"]
```

---

## 8. Validation Pipeline

```mermaid
flowchart TD
    Input["Raw JSON"] --> Parse{"Valid JSON?"}
    Parse -->|No| SyntaxErr["Return syntax error"]
    Parse -->|Yes| AutoCorrect["Run Auto Corrector"]

    AutoCorrect --> Trim["Trim whitespace"]
    AutoCorrect --> Case["Normalize case<br/>(fuzzy match dropdowns)"]
    AutoCorrect --> Bool["Normalize booleans"]
    AutoCorrect --> Numeric["Convert numeric strings"]
    AutoCorrect --> LogFixes["Log all corrections"]

    LogFixes --> Validate["Run Validator"]
    Validate --> ReqCheck["Check required fields"]
    Validate --> TypeCheck["Check data types"]
    Validate --> DropCheck["Check dropdown values"]
    Validate --> DupCheck["Check duplicates (SKU, ID)"]
    Validate --> ExtraCheck["Check unknown/extra keys"]
    Validate --> LenCheck["Check length limits"]
    Validate --> CharCheck["Check illegal characters"]
    Validate --> RelCheck["Check parent-child<br/>relationships"]

    Validate --> PluginCheck{"Plugin<br/>rules?"}
    PluginCheck -->|Yes| PluginVal["Run plugin-specific validation"]
    PluginCheck -->|No| Collect

    PluginVal --> Collect["Collect all issues"]
    ReqCheck --> Collect
    TypeCheck --> Collect
    DropCheck --> Collect
    DupCheck --> Collect
    ExtraCheck --> Collect
    LenCheck --> Collect
    CharCheck --> Collect
    RelCheck --> Collect

    Collect --> Classify["Classify: ERROR / WARNING / INFO"]
    Classify --> Result["Return ValidationResult"]
```

---

## 9. Plugin System

### Class Hierarchy

```mermaid
classDiagram
    class MarketplacePlugin {
        <<abstract>>
        +name: str
        +version: str
        +detect(schema: WorkbookSchema) float
        +get_validation_rules() List~ValidationRule~
        +get_prompt_additions() str
        +get_field_mappings() Dict
        +get_auto_corrections() Dict
    }

    class FlipkartPlugin {
        +name = "Flipkart"
        +detect(schema) float
        +get_validation_rules()
        +get_prompt_additions()
        +get_field_mappings()
        +get_auto_corrections()
    }

    class AmazonPlugin {
        +name = "Amazon"
        +detect(schema) float
    }

    class MeeshoPlugin {
        +name = "Meesho"
        +detect(schema) float
    }

    class PluginRegistry {
        -plugins: List~MarketplacePlugin~
        +discover_plugins()
        +detect_marketplace(schema) MarketplacePlugin?
        +get_plugin(name) MarketplacePlugin?
    }

    MarketplacePlugin <|-- FlipkartPlugin
    MarketplacePlugin <|-- AmazonPlugin
    MarketplacePlugin <|-- MeeshoPlugin
    PluginRegistry o-- MarketplacePlugin
```

### Plugin Detection Flow

When a workbook is analyzed, the `PluginRegistry` runs detection on all registered plugins:

1. Each plugin's `detect()` receives the `WorkbookSchema`
2. Each plugin returns a confidence score (0.0–1.0)
3. The plugin with the highest score above a threshold (0.5) wins
4. If no plugin matches, the system uses generic behavior

---

## 10. Session Management

### SQLite Schema

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filename TEXT NOT NULL,
    file_size INTEGER,
    marketplace TEXT,
    sheet_count INTEGER,
    status TEXT DEFAULT 'uploaded',  -- uploaded, analyzed, validated, exported
    schema_json TEXT,
    prompt_text TEXT,
    input_json TEXT,
    validation_json TEXT,
    corrections_json TEXT,
    export_path TEXT
);
```

### Session Lifecycle

```
uploaded → analyzed → prompt_generated → json_received → validated → exported
```

Each state transition updates `status` and `updated_at`.

---

## 11. Future AI Integration Architecture

```mermaid
classDiagram
    class AIAdapter {
        <<abstract>>
        +name: str
        +generate(prompt: str, images: List~bytes~) str
        +is_available() bool
        +get_config_schema() Dict
    }

    class OpenAIAdapter {
        +name = "OpenAI"
        +generate()
        +is_available()
    }

    class GeminiAdapter {
        +name = "Gemini"
        +generate()
        +is_available()
    }

    class OllamaAdapter {
        +name = "Ollama"
        +generate()
        +is_available()
    }

    AIAdapter <|-- OpenAIAdapter
    AIAdapter <|-- GeminiAdapter
    AIAdapter <|-- OllamaAdapter
```

The AI adapter layer is **fully decoupled** from the rest of the application. When implemented:

1. API gets a new endpoint: `POST /api/ai/generate`
2. Frontend gets an "AI Generate" button alongside the manual copy-paste flow
3. The adapter calls the AI API, gets JSON, and feeds it into the same validation pipeline
4. **Zero changes** to analyzer, validator, writer, or reporter

---

## 12. Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| **API Routes** | Try/except with JSON error responses, HTTP status codes |
| **Core Modules** | Raise typed exceptions (`AnalysisError`, `ValidationError`, `WriterError`) |
| **Frontend** | API client catches errors, shows toast notifications |
| **File I/O** | Always use context managers, validate file existence before operations |
| **Excel Operations** | Catch openpyxl-specific exceptions, never corrupt the template |

### Custom Exceptions

```python
class ExcelPlorerError(Exception): ...
class AnalysisError(ExcelPlorerError): ...
class ValidationError(ExcelPlorerError): ...
class WriterError(ExcelPlorerError): ...
class PluginError(ExcelPlorerError): ...
class SessionError(ExcelPlorerError): ...
```

---

## 13. Logging Strategy

- Use Python's `logging` module
- Log file: `data/excelplorer.log`
- Console output in development, file-only in production
- Log levels:
  - `DEBUG` — Detailed analysis steps, cell-level operations
  - `INFO` — Session lifecycle, file uploads, exports
  - `WARNING` — Auto-corrections, skipped fields, plugin detection misses
  - `ERROR` — Validation failures, file I/O errors
  - `CRITICAL` — Application startup failures
- Structured format: `[%(asctime)s] %(levelname)s %(name)s: %(message)s`
- Each module gets its own logger: `logging.getLogger(__name__)`

---

## 14. API Reference

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| POST | `/api/upload` | multipart/form-data (file) | `{session_id, file_info}` |
| GET | `/api/analysis/<id>` | — | `{sheets, columns, validations, ...}` |
| GET | `/api/prompt/<id>` | — | `{prompt, char_count, word_count, token_count}` |
| POST | `/api/validate/<id>` | `{json_data}` | `{valid, issues[], corrections[], preview}` |
| GET | `/api/preview/<id>` | — | `{headers, rows, cell_statuses}` |
| POST | `/api/preview/<id>/edit` | `{row, column, value}` | `{success}` |
| POST | `/api/export/<id>` | — | `{excel_path, report_path}` |
| GET | `/api/export/<id>/download/<type>` | — | File download |
| GET | `/api/report/<id>` | `?format=html\|txt\|json` | Report content |
| GET | `/api/sessions` | — | `[{id, filename, date, status}, ...]` |
| GET | `/api/sessions/<id>` | — | Full session details |
| DELETE | `/api/sessions/<id>` | — | `{success}` |
