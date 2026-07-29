# Product Requirements Document (PRD)

## ExcelPlorer — AI Spreadsheet Mapping Framework

**Version:** 1.0.0  
**Last Updated:** 2026-07-23  
**Status:** Active Development

---

## 1. Vision

ExcelPlorer is a generic, extensible framework that enables e-commerce sellers to convert AI-generated product descriptions and attributes into marketplace-ready bulk-upload Excel files. It eliminates manual data entry by leveraging existing AI vision models through an optimized prompt-copy-paste workflow.

---

## 2. Problem Statement

E-commerce sellers face a tedious, error-prone process when listing products on marketplaces:

1. Marketplaces provide complex Excel templates with hundreds of columns, strict validation rules, dropdowns, and required fields
2. Sellers must manually inspect each column, understand its constraints, and fill values correctly
3. AI models (ChatGPT, Gemini, Claude) can analyze product images and generate product data, but their output doesn't match the exact template format
4. There is no tool that bridges AI output to marketplace Excel templates while preserving formatting and enforcing validation

**ExcelPlorer solves this by automating the entire pipeline from template analysis to validated Excel output.**

---

## 3. Goals

| ID | Goal | Priority |
|----|------|----------|
| G-01 | Analyze any marketplace Excel template automatically | Critical |
| G-02 | Generate optimized AI prompts from template analysis | Critical |
| G-03 | Validate AI-returned JSON against template schema | Critical |
| G-04 | Write validated data into Excel preserving all formatting | Critical |
| G-05 | Support marketplace-specific plugins | High |
| G-06 | Provide detailed validation reports | High |
| G-07 | Auto-correct common AI mistakes | High |
| G-08 | Allow manual editing before export | Medium |
| G-09 | Maintain product library (JSON persistence) locally | Medium |
| G-10 | Be immediately runnable after dependency installation | Critical |

---

## 4. Non-Goals

| ID | Non-Goal | Rationale |
|----|----------|-----------|
| NG-01 | Direct AI API calls in v1.0 | Users copy-paste prompts manually; API integration is future scope |
| NG-02 | Cloud storage or sync | Desktop-first, privacy-focused, local-only |
| NG-03 | Marketplace API integration | We don't upload to marketplaces; we produce the Excel file |
| NG-04 | Image hosting or processing | AI models handle images; we handle structured data |
| NG-05 | Multi-user / authentication | Single-user local application |
| NG-06 | Mobile-first design | Desktop-first; responsive but optimized for large screens |

---

## 5. Target Users

### Primary: E-commerce Sellers
- List products on Flipkart, Amazon, Meesho, Shopify, WooCommerce
- Non-technical; comfortable with Excel and AI chatbots
- Need fast, accurate bulk listing without manual template filling
- Handle 10-500 products per session

### Secondary: E-commerce Service Providers
- Listing agencies managing multiple seller accounts
- Need to process templates across multiple marketplaces
- Higher volume (100-1000+ products per session)

---

## 6. Functional Requirements

### FR-01: File Upload
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01.1 | Accept `.xlsx` files via drag-and-drop or file picker | Critical |
| FR-01.2 | Accept `.xls` files (legacy format) | High |
| FR-01.3 | Display animated upload progress state | Medium |
| FR-01.4 | Show file metadata after upload (name, size, sheets, rows, columns) | Critical |
| FR-01.5 | Detect marketplace if template matches a known plugin | High |
| FR-01.6 | Reject invalid file types with clear error message | Critical |
| FR-01.7 | Support files up to 50MB | High |

### FR-02: Workbook Analysis
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-02.1 | Detect header row automatically | Critical |
| FR-02.2 | Extract all column names from all sheets | Critical |
| FR-02.3 | Detect merged cells and their ranges | High |
| FR-02.4 | Read data validation rules (dropdown lists) | Critical |
| FR-02.5 | Resolve validation formulas referencing other sheets/named ranges | High |
| FR-02.6 | Identify required vs. optional columns | Critical |
| FR-02.7 | Sample existing data values (first 5 non-empty per column) | High |
| FR-02.8 | Detect column data types from samples | High |
| FR-02.9 | Detect maximum field lengths (from validation or samples) | Medium |
| FR-02.10 | Identify hidden sheets | High |
| FR-02.11 | Identify hidden columns | High |
| FR-02.12 | Extract formulas | Medium |
| FR-02.13 | Extract named ranges | Medium |
| FR-02.14 | Extract cell comments/notes | Low |
| FR-02.15 | Generate internal WorkbookSchema from analysis | Critical |
| FR-02.16 | Never hardcode field names — everything from analysis | Critical |

### FR-03: Prompt Generation
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-03.1 | Generate dual prompts (Rules + Data) dynamically from WorkbookSchema | Critical |
| FR-03.2 | Include all detected column names with required/optional status | Critical |
| FR-03.3 | Include allowed values for dropdown columns | Critical |
| FR-03.4 | Include data type and max length constraints | High |
| FR-03.5 | Include example JSON structure matching schema in Data Prompt | Critical |
| FR-03.6 | Instruct AI to return ONLY JSON (no markdown, no code blocks) | Critical |
| FR-03.7 | Instruct AI to use EXACT field names | Critical |
| FR-03.8 | Instruct AI to leave unknown values empty | Critical |
| FR-03.9 | Support multiple products in a single response | High |
| FR-03.10 | Support variant/parent-child structures | Medium |
| FR-03.11 | Allow marketplace plugins and template Index sheets to inject additional rules into the Rules Prompt | High |
| FR-03.12 | Display character count, word count, estimated token count | Medium |

### FR-04: JSON Import
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-04.1 | Large paste area for JSON input | Critical |
| FR-04.2 | Instant JSON syntax validation on paste | Critical |
| FR-04.3 | Display parse errors with line/position | High |
| FR-04.4 | Pretty-print option | Medium |
| FR-04.5 | Collapse/expand for large JSON | Medium |

### FR-05: Validation Engine
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-05.1 | Validate missing required fields | Critical |
| FR-05.2 | Validate data types (string, number, date) | Critical |
| FR-05.3 | Detect duplicate SKUs / unique identifiers | High |
| FR-05.4 | Detect unknown/extra keys not in schema | High |
| FR-05.5 | Validate against dropdown allowed values | Critical |
| FR-05.6 | Validate field length limits | High |
| FR-05.7 | Detect empty mandatory values | Critical |
| FR-05.8 | Detect illegal characters | Medium |
| FR-05.9 | Validate parent-child variant relationships | Medium |
| FR-05.10 | Validate numeric ranges / dimensions | Medium |
| FR-05.11 | Support marketplace-specific validation rules via plugins | High |
| FR-05.12 | Categorize issues by severity (ERROR, WARNING, INFO) | Critical |

### FR-06: Auto-Correction
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-06.1 | Trim whitespace from all string values | Critical |
| FR-06.2 | Normalize case to match allowed dropdown values | High |
| FR-06.3 | Boolean normalization (TRUE→Yes, FALSE→No based on template) | High |
| FR-06.4 | Numeric type conversion (string→int/float where schema expects number) | High |
| FR-06.5 | Fuzzy match against allowed values for typo correction | High |
| FR-06.6 | Unit normalization | Medium |
| FR-06.7 | Log all corrections made | Critical |
| FR-06.8 | Never guess unknown information | Critical |

### FR-07: Excel Writer
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-07.1 | Write data into correct rows of original template | Critical |
| FR-07.2 | Match columns by name (not index) | Critical |
| FR-07.3 | Preserve all cell formatting (fonts, colors, borders, number formats) | Critical |
| FR-07.4 | Preserve data validation / dropdown rules | Critical |
| FR-07.5 | Preserve hidden sheets | Critical |
| FR-07.6 | Preserve named ranges | High |
| FR-07.7 | Preserve formulas in non-data cells | High |
| FR-07.8 | Handle multiple sheets | High |
| FR-07.9 | Handle multiple products (multiple rows) | Critical |
| FR-07.10 | Only modify data rows — never modify headers or structure | Critical |

### FR-08: Validation Report
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-08.1 | Count: products processed, successful, warnings, failed | Critical |
| FR-08.2 | List missing required fields per product | Critical |
| FR-08.3 | List unknown fields encountered | High |
| FR-08.4 | List duplicate values found | High |
| FR-08.5 | List invalid values | High |
| FR-08.6 | List cells/rows skipped | Medium |
| FR-08.7 | List auto-corrections performed | Critical |
| FR-08.8 | Summary statistics | Critical |
| FR-08.9 | Export as TXT | High |
| FR-08.10 | Export as HTML | High |
| FR-08.11 | Export as JSON | High |

### FR-09: Preview
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-09.1 | Table preview of data before writing Excel | Critical |
| FR-09.2 | Highlight missing cells (red) | Critical |
| FR-09.3 | Highlight changed/auto-corrected cells (yellow) | High |
| FR-09.4 | Highlight errors (red border) | Critical |
| FR-09.5 | Highlight warnings (orange) | High |
| FR-09.6 | Allow manual cell editing | High |
| FR-09.7 | Save edits back to session | High |

### FR-10: Export
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-10.1 | Export completed Excel file | Critical |
| FR-10.2 | Export validation report (TXT/HTML/JSON) | High |
| FR-10.3 | Export generated prompt | Medium |
| FR-10.4 | Export imported JSON | Medium |
| FR-10.5 | Export session log | Low |

### FR-11: Product Library
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-11.1 | Persist generated product JSONs locally (SQLite or FileStore) | High |
| FR-11.2 | Key saved products by SKU ID for easy lookup and reuse | High |
| FR-11.3 | Auto-save edits made to product JSONs | High |
| FR-11.4 | Delete stored products | Medium |
| FR-11.5 | No cloud storage | Critical |

### FR-12: Plugin System
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-12.1 | Abstract base class for marketplace plugins | Critical |
| FR-12.2 | Auto-detection of marketplace from template | High |
| FR-12.3 | Plugin discovery and registry | High |
| FR-12.4 | Flipkart plugin (fully implemented) | High |
| FR-12.5 | Amazon plugin (stub) | Low |
| FR-12.6 | Meesho plugin (stub) | Low |
| FR-12.7 | Plugin-specific validation rules | High |
| FR-12.8 | Plugin-specific prompt additions | High |
| FR-12.9 | Plugin-specific auto-corrections | Medium |

---

## 7. Non-Functional Requirements

### NFR-01: Performance
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01.1 | Excel processing (100 products) | < 5 seconds |
| NFR-01.2 | Workbook analysis | < 3 seconds |
| NFR-01.3 | JSON validation (100 products) | < 1 second |
| NFR-01.4 | UI responsiveness | < 100ms for interactions |

### NFR-02: Code Quality
| ID | Requirement |
|----|-------------|
| NFR-02.1 | Type hints on all Python functions |
| NFR-02.2 | Docstrings on all public methods |
| NFR-02.3 | Structured logging throughout |
| NFR-02.4 | Modular file structure (no God files) |
| NFR-02.5 | Comprehensive error handling |
| NFR-02.6 | Configuration via config file (no hardcoded paths) |
| NFR-02.7 | Reusable classes and functions |

### NFR-03: Maintainability
| ID | Requirement |
|----|-------------|
| NFR-03.1 | Clear folder structure with single responsibility per file |
| NFR-03.2 | Plugin system for marketplace extensibility |
| NFR-03.3 | AI adapter interface for future API integration |
| NFR-03.4 | Documentation synchronized with implementation |

---

## 8. Supported Platforms

| Platform | Status |
|----------|--------|
| Windows 10/11 | Primary target |
| macOS | Supported (untested) |
| Linux | Supported (untested) |
| Chrome/Edge/Firefox | Frontend target browsers |

---

## 9. UI Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| UI-01 | Dark mode theme | Critical |
| UI-02 | Glassmorphism / material style | High |
| UI-03 | Rounded corners | High |
| UI-04 | 8-tab navigation | Critical |
| UI-05 | Responsive layout (desktop-first) | High |
| UI-06 | Drag-and-drop upload with animation | Critical |
| UI-07 | One-click copy for prompts | Critical |
| UI-08 | Toast notifications for feedback | High |
| UI-09 | Micro-animations on interactions | Medium |
| UI-10 | Session history sidebar | Medium |
| UI-11 | Google Fonts (Inter, JetBrains Mono) | Medium |

---

## 10. Marketplace Compatibility

The system must not be hardcoded to any marketplace. The following are target marketplaces for plugin support:

| Marketplace | Plugin Status | Priority |
|-------------|---------------|----------|
| Flipkart | Full implementation | High |
| Amazon | Stub | Low |
| Meesho | Stub | Low |
| Shopify | Future | — |
| WooCommerce | Future | — |

---

## 11. Security Considerations

| ID | Consideration |
|----|---------------|
| SEC-01 | All data stays local — no network transmission of user data |
| SEC-02 | File upload validation — reject non-Excel files |
| SEC-03 | JSON input sanitization |
| SEC-04 | No debug mode in production |
| SEC-05 | No arbitrary code execution from uploaded files |

---

## 12. Future Scope

| ID | Feature | Notes |
|----|---------|-------|
| FS-01 | Direct AI API integration (OpenAI, Gemini, Claude, Ollama) | Adapter interface already in place |
| FS-02 | Batch processing (multiple templates in queue) | |
| FS-03 | Template library (save analyzed schemas for reuse) | |
| FS-04 | Image URL validation | Check if image URLs are accessible |
| FS-05 | PyInstaller packaging (.exe distribution) | |
| FS-06 | Additional marketplace plugins | |
| FS-07 | Collaborative editing (multi-user) | |

---

## 13. Feature Checklist

> This checklist tracks implementation status. Update as features are completed.

- [ ] **FR-01** File Upload (drag-and-drop, .xlsx, .xls, metadata display)
- [ ] **FR-02** Workbook Analysis (headers, dropdowns, validations, hidden elements)
- [ ] **FR-03** Prompt Generation (dynamic, schema-driven, multi-product)
- [ ] **FR-04** JSON Import (paste, validate, pretty-print)
- [ ] **FR-05** Validation Engine (required fields, types, dropdowns, duplicates)
- [ ] **FR-06** Auto-Correction (whitespace, casing, booleans, fuzzy match)
- [ ] **FR-07** Excel Writer (format-preserving, column-matched)
- [ ] **FR-08** Validation Report (TXT, HTML, JSON export)
- [ ] **FR-09** Preview (editable table, cell highlighting)
- [ ] **FR-10** Export (Excel, reports, prompt, JSON, session log)
- [ ] **FR-11** Session History (SQLite, list, reopen, delete)
- [ ] **FR-12** Plugin System (base, registry, Flipkart, stubs)
- [ ] **UI** Full dark-mode glassmorphism UI with 8 tabs
- [ ] **NFR** Performance targets met
- [ ] **NFR** Code quality standards met
- [ ] **Tests** Unit tests for analyzer, validator, auto-corrector
