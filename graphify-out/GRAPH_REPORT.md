# Graph Report - stocktaking  (2026-10-27)

## Corpus Check
- Corpus is ~20,207 words - fits in a single context window. You may not need a graph.

## Summary
- 325 nodes · 681 edges · 20 communities (16 shown, 4 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Frontend Page Templates
- Common Code API
- Item CRUD
- Sensor Barcode Tracking
- Stocktake Records API
- Page Routes
- Items API
- Config and DB Setup
- Docker Compose Services
- Scan Page JS
- Stocktake Page JS
- Dev Certificate Script
- Shared Frontend Utils
- Items Page JS
- Common Codes Page JS
- Autocomplete Widget
- Status Page JS

## God Nodes (most connected - your core abstractions)
1. `Item` - 18 edges
2. `CLAUDE.md (project instructions)` - 17 edges
3. `SensorBarcode` - 14 edges
4. `Base` - 13 edges
5. `StocktakeRecord` - 12 edges
6. `CommonCode` - 11 edges
7. `AuditMixin` - 11 edges
8. `create_code()` - 9 edges
9. `scan_barcode()` - 9 edges
10. `get_status()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `scan.html (센서 재고 등록 page)` --conceptually_related_to--> `Camera decode gated by armed flag`  [INFERRED]
  app/templates/pages/scan.html → CLAUDE.md
- `CLAUDE.md (project instructions)` --references--> `Guidelines skill (SKILL.md)`  [EXTRACTED]
  CLAUDE.md → .claude/skills/guidelines/SKILL.md
- `toast.html (toast container partial)` --conceptually_related_to--> `Visible toast feedback on create/update/delete`  [INFERRED]
  app/templates/components/toast.html → guide/DEVELOPMENT_GUIDELINES.md
- `layout.html (base layout)` --references--> `asset_version query string cache busting`  [EXTRACTED]
  app/templates/layout.html → CLAUDE.md
- `common_codes.html (공통코드 등록 page)` --references--> `Mobile layout and table-scroll wrapper`  [EXTRACTED]
  app/templates/pages/common_codes.html → CLAUDE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **current_stock reconciliation** — claude_current_stock_formula, guide_schema_design_sensor_barcodes, guide_schema_design_stocktake_records, guide_plan_stocktake_form_breakdown, app_templates_pages_stocktakes, app_templates_pages_status [EXTRACTED 1.00]
- **Sensor scan flow (scan page, camera, HTTPS, reactivation)** — app_templates_pages_scan, claude_sensor_scan_add_remove_modes, claude_camera_armed_flag, claude_https_required_for_camera, guide_plan_sensor_barcode_reactivation [INFERRED 0.75]
- **Project documentation index** — claude, guide_handover, guide_plan, guide_schema_design, guide_development_guidelines, claude_skills_guidelines_skill [EXTRACTED 1.00]

## Communities (20 total, 4 thin omitted)

### Community 0 - "Frontend Page Templates"
Cohesion: 0.09
Nodes (20): nav.html (sidebar nav partial), toast.html (toast container partial), layout.html (base layout), common_codes.html (공통코드 등록 page), items.html (품목 등록 page), scan.html (센서 재고 등록 page), status.html (현황 page), stocktakes.html (재고 등록 page) (+12 more)

### Community 1 - "Common Code API"
Cohesion: 0.13
Nodes (22): create_code(), delete_code(), list_codes(), list_groups(), _serialize(), update_code(), code_exists_in_group(), create_code() (+14 more)

### Community 2 - "Item CRUD"
Cohesion: 0.13
Nodes (21): delete_item(), delete_stocktake(), barcode_prefix_exists(), count_items(), create_item(), deactivate_item(), find_item_by_scanned_barcode(), get_item() (+13 more)

### Community 3 - "Sensor Barcode Tracking"
Cohesion: 0.12
Nodes (14): delete_barcode(), list_barcodes(), remove_barcode(), scan_barcode(), get_db(), create_barcode(), deactivate_barcode(), get_barcode() (+6 more)

### Community 4 - "Stocktake Records API"
Cohesion: 0.19
Nodes (10): create_stocktake(), latest_quantity(), list_stocktakes(), status_view(), update_stocktake(), LatestQuantityOut, StatusRow, StocktakeCreate (+2 more)

### Community 5 - "Page Routes"
Cohesion: 0.17
Nodes (7): common_codes_page(), index(), items_page(), scan_page(), status_page(), stocktakes_page(), lifespan()

### Community 6 - "Items API"
Cohesion: 0.19
Nodes (9): count_items(), create_item(), get_item(), list_items(), update_item(), CommonCodeBrief, ItemCreate, ItemOut (+1 more)

### Community 7 - "Config and DB Setup"
Cohesion: 0.25
Nodes (3): Settings, Base, AuditMixin

### Community 8 - "Docker Compose Services"
Cohesion: 0.11
Nodes (18): MARIADB_DATABASE, MARIADB_PASSWORD, MARIADB_ROOT_PASSWORD, MARIADB_USER, interval, retries, test, timeout (+10 more)

### Community 9 - "Scan Page JS"
Cohesion: 0.16
Nodes (14): cameraCaptureBtn, cameraReaderEl, cameraSupported(), cameraToggleBtn, currentCount(), logBody, modeTabs, onCameraDecoded() (+6 more)

### Community 10 - "Stocktake Page JS"
Cohesion: 0.27
Nodes (11): clearSelectedItem(), deleteStocktake(), isSensorTracked(), loadStocktakes(), renderStocktakeEditRow(), renderStocktakeRow(), renderStocktakeTable(), saveStocktakeEdit() (+3 more)

### Community 12 - "Shared Frontend Utils"
Cohesion: 0.27
Nodes (6): apiRequest(), buildQuery(), commonCodeCache, itemSizeLabel(), loadCodeGroup(), sizeDetailText()

### Community 13 - "Items Page JS"
Cohesion: 0.38
Nodes (7): deleteItem(), loadItems(), renderItemEditRow(), renderItemRow(), renderItemTable(), saveItemEdit(), selectHtml()

### Community 14 - "Common Codes Page JS"
Cohesion: 0.47
Nodes (8): deleteCode(), loadCodes(), loadGroups(), renderEditRow(), renderRow(), renderTable(), renderTabs(), state

### Community 15 - "Autocomplete Widget"
Cohesion: 0.53
Nodes (4): attachAutocomplete(), close(), render(), select()

### Community 16 - "Status Page JS"
Cohesion: 0.47
Nodes (4): loadStatus(), renderStatusRow(), renderDetail(), renderStatusTable()

## Knowledge Gaps
- **5 isolated node(s):** `SERVER_GUIDE.md (server access checklist)`, `nav.html (sidebar nav partial)`, `requirements.txt (Python dependencies)`, `stocktake_records table (snapshot quantity)`, `Fixed CSS-variable color palette`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 96 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Item` connect `Item CRUD` to `Config and DB Setup`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Item` (e.g. with `barcode_prefix_exists()` and `count_items()`) actually correct?**
  _`Item` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SERVER_GUIDE.md (server access checklist)`, `nav.html (sidebar nav partial)`, `requirements.txt (Python dependencies)` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend Page Templates` be split into smaller, more focused modules?**
  _Cohesion score 0.09176788124156546 - nodes in this community are weakly interconnected._
- **Why does `SensorBarcode` connect `Sensor Barcode Tracking` to `Item CRUD`, `Config and DB Setup`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `SensorBarcode` (e.g. with `deactivate_barcode()` and `get_barcode()`) actually correct?**
  _`SensorBarcode` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `Common Code API` be split into smaller, more focused modules?**
  _Cohesion score 0.12612612612612611 - nodes in this community are weakly interconnected._