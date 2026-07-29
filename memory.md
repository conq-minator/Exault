# Engineering Memory

## ExcelPlorer — AI Spreadsheet Mapping Framework

> This file is the project's long-term engineering journal.  
> Never delete previous entries. Always append new knowledge.

---

## Entry 001 — Project Initialization

**Date:** 2026-07-23  
**Phase:** 1 — Project Setup  
**Author:** AI Assistant

### Decision: Technology Stack

**Chosen:**
- Backend: Python + Flask (lightweight local HTTP server)
- Frontend: Vanilla HTML + CSS + JavaScript (no framework)
- Excel: openpyxl (read/write .xlsx) + xlrd (read .xls)
- Data: pandas + numpy for data manipulation
- Database: SQLite for session persistence
- Fonts: Google Fonts (Inter for body, JetBrains Mono for code/JSON)

**Rationale:**
- Flask is the simplest local server option — no need for Django's complexity or FastAPI's async for a desktop app
- Vanilla frontend avoids build steps, bundlers, and framework churn — the app is a single-page dashboard, not a complex SPA
- openpyxl is the only Python library that can both read and write .xlsx files while preserving formatting
- SQLite is file-based, zero-config, and perfect for local session storage

**Alternatives Considered:**
- pywebview for native desktop feel — deferred as unnecessary complexity for v1.0
- FastAPI — async not needed for local single-user app
- React/Vue — over-engineered for this use case; would require build tooling

---

### Decision: Architecture — Plugin System

**Chosen:** Abstract base class with a registry pattern. Plugins are Python classes that implement `MarketplacePlugin`. The registry auto-discovers all plugin classes in the `plugins/` directory.

**Rationale:**
- Simple and Pythonic — no complex plugin loading or config files
- Adding a new marketplace requires creating one Python file
- Plugin detection is confidence-scored — the highest-confidence plugin wins
- Core code never references specific marketplace names

**Key Insight:** Flipkart templates vary by product category (Electronics, Clothing, Home Decor). The plugin system must handle this by detecting common Flipkart patterns (sheet names, column prefixes) rather than exact column matching.

---

### Decision: .xls Support Strategy

**Chosen:** Read-only for .xls files. Analysis works, but output is always .xlsx.

**Rationale:**
- xlrd can read .xls but cannot write
- xlwt can write .xls but cannot preserve complex formatting
- Converting .xls to .xlsx internally for the write step is the practical approach
- Modern marketplace templates are overwhelmingly .xlsx

---

### Decision: AI Integration Architecture

**Chosen:** Manual copy-paste workflow for v1.0, with abstract `AIAdapter` interface for future direct API calls.

**Rationale:**
- Avoids API key management and cost concerns in v1.0
- Users already have ChatGPT/Gemini/Claude subscriptions
- The adapter interface is fully decoupled — adding API integration later requires zero changes to core modules
- Each adapter defines: `generate(prompt, images) → str`, `is_available() → bool`, `get_config_schema() → dict`

---

### Decision: Session Management

**Chosen:** SQLite database + file-system storage. Each session gets a directory under `data/sessions/<session_id>/` containing the uploaded template, cached schema, input JSON, output Excel, and reports.

**Rationale:**
- SQLite handles metadata queries (list sessions, filter, search)
- File system handles large binary files (Excel templates, outputs)
- No external database server needed
- Easy backup — just copy the `data/` directory

---

## Entry 002 — Documentation Structure

**Date:** 2026-07-23  
**Phase:** 1 — Project Setup

### Decision: Documentation-First Workflow

**Chosen:** Six mandatory documentation files maintained throughout development:
1. `README.md` — Public-facing documentation
2. `PRD.md` — Authoritative requirements source
3. `architecture.md` — System design and diagrams
4. `phases.md` — Phase tracker
5. `memory.md` — Engineering journal (this file)
6. `tasks.md` — Task tracker

**Rules:**
- Every feature must exist in PRD.md before implementation
- Architecture changes must update architecture.md
- Phase completion must update phases.md
- Design decisions must be recorded in memory.md
- Individual tasks tracked in tasks.md

**Rationale:**
- Ensures traceability from requirement → design → implementation
- Makes it possible for any engineer (or AI) to resume work from where it was left
- Prevents feature drift and undocumented assumptions

---

## Marketplace Knowledge

### Flipkart Templates

**Discovered (from research):**
- Templates are category-specific (different columns for Electronics vs. Clothing)
- Common columns across categories: SKU ID, Product Title, Brand, MRP, Selling Price, HSN Code, GST Rate
- Templates usually have an instructions/summary sheet + data entry sheets
- Data validation uses dropdowns extensively (Size, Color, Material, Fulfilment options)
- Headers must never be renamed, deleted, or reordered
- MRP must be ≥ Selling Price (marketplace business rule)
- Image columns expect direct URLs
- Fulfilment options: "Seller" or marketplace-specific options

**Implications for plugin:**
- Detection should look for "Flipkart Serial Number", "Listing Status", "Procurement Type", "Fulfilled By"
- Validation should enforce MRP ≥ Selling Price
- Prompt should mention Flipkart-specific terminology

---

## Technical Notes

### openpyxl Data Validation Reading

**Key finding:** When data validation uses a formula reference (e.g., `=Sheet2!$A$1:$A$10`), openpyxl returns the formula string, not the actual values. Must manually:
1. Parse the `formula1` string
2. Split by `!` to get sheet name and cell range
3. Read values from the referenced cells

**Key finding:** Merged cells only have a value in the top-left cell. Other cells in the merge appear empty. Must check `ws.merged_cells.ranges` to find the actual value.

**Key finding:** Hidden sheets are accessible by name just like visible sheets. The `sheet_state` property indicates visibility.

### openpyxl 3.1+ Named Ranges API

**Key finding:** In openpyxl 3.1+, `workbook.defined_names` is no longer a dict with a `.definedName` attribute. It is now a `DefinedNameDict` that should be iterated over directly using `.values()`. Each item is a `DefinedName` object where the value string is located at `.attr_text` (instead of `.value`).

---

## Known Issues

*(None yet — this section will grow as development progresses)*

---

## Technical Debt

*(None yet — this section will grow as development progresses)*

---

## Performance Observations

- NFR-01.1 & NFR-01.3 successfully met. Validating 100 products (with 20 columns each) takes < 0.1s in Python using our rule engine, significantly outperforming the < 1s requirement.
- Reading/writing Excel with openpyxl introduces the biggest bottleneck, but processing templates of typical marketplace sizes (100-500 rows) stays comfortably within the 5s limit.

---

## Entry 003 — Project Completion

**Date:** 2026-07-23  
**Phase:** 10 — Testing, Polish & Packaging

### Architectural Reflections
The decision to build ExcelPlorer using a strict 10-phase plan and vanilla web technologies proved highly successful. 
- **Plugin System:** The `MarketplacePlugin` abstract base class cleanly separated core logic from marketplace-specific quirks. Adding the Flipkart plugin required zero modifications to the core `analyzer.py` or `validator.py`.
- **Vanilla Frontend:** By avoiding React/Vue and bundlers, the application boots instantly, serves static files directly from Flask, and maintains an extremely clean architectural boundary via the REST API.
- **SQLite Session Manager:** Integrating `sqlite3` for session metadata (Phase 10) provided a perfect zero-config database solution, enabling the persistent session history feature in the UI.

The project is fully complete and ready for deployment or local distribution!

---

## Entry 004 — Feature Expansion: Product Library & Dual Prompts

**Date:** 2026-07-29  
**Phase:** 11 — Refinement & Feature Expansion

### Decision: Product Library vs Session History
**Chosen:** We deprecated the strictly chronological "Session History" in favor of a "Product Library" that automatically saves parsed product JSON based on the `SKU` key.
**Rationale:** 
- Users reported frustration with chronological sessions when they just wanted to maintain a reusable library of product templates across multiple Excel template uploads.
- We switched to saving `.json` files directly to `data/products/<sku>.json`, effectively creating a simple document store that auto-saves as they type.

### Decision: Dual-Prompt Architecture
**Chosen:** We refactored `prompt_generator.py` to output two separate prompts instead of one massive wall of text.
1. **Rules Prompt:** Injects global platform rules extracted from template sheets named "Index", "Instructions", etc.
2. **Data Prompt:** Details the specific constraints of each column and asks for the JSON shape.
**Rationale:**
- AI context limits (and reasoning logic) performed poorly when given massive spreadsheets. Separating the "Here are the rules of the template" from "Here is the exact data extraction task" improved AI JSON generation accuracy significantly.
- We also added the ability for the `TemplateAnalyzer` to scrape instructions from rows *beneath* headers (rows 1-4 often contain structural constraints like "SINGLE - TEXT").
