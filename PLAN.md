# Ship Crew Optimizer - Development Roadmap

## Project Overview
A standalone desktop application to optimize ship crew assignments for a naval strategy game. Built with Python backend, HTML/jQuery/Tailwind CSS frontend, and PyWebView for native window delivery.

---

## Phase 1: Data Models & JSON I/O

### Objectives
- Define core data structures using Python `dataclasses`
- Implement serialization/deserialization for roster and ship configuration files
- Establish the mathematical foundation for stat calculations

### Deliverables
1. [`models.py`](models.py) - Complete data model definitions
2. [`solver.py`](solver.py) - Core optimization engine with stat calculation logic
3. [`test_solver.py`](test_solver.py) - Unit tests for math engine

### Acceptance Criteria
- [ ] All data models (`Stats`, `Captain`, `CrewMember`, `ShipUpgrades`, `BuildingBonuses`, `ConsumableBuff`, `VoyageTarget`) are defined with proper type hints
- [ ] Serialization methods (`to_dict()`, `from_dict()`) work correctly for all models
- [ ] Base stat calculation (1 Captain + 5 Crew + flat upgrades + flat consumables) produces correct sums
- [ ] Percentage multiplier application (`final_stat = floor(base_sum * (1 + sum_of_percent_multipliers))`) is accurate
- [ ] Combination generation using `itertools.combinations` covers all valid crew arrangements
- [ ] Voyage target filtering correctly identifies qualifying setups
- [ ] Result ranking by composite score works as expected
- [ ] All unit tests in `test_solver.py` pass (100% pass rate)

### Test Instructions
```bash
python -m pytest test_solver.py -v
```
Expected: All 15+ tests pass with correct assertions.

---

## Phase 2: Flask API Layer

### Objectives
- Create RESTful API endpoints for frontend communication
- Implement optimization request handling
- Add roster file import/export endpoints

### Deliverables
1. `api.py` - Flask API routes
2. `test_api.py` - API endpoint tests

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/optimize` | Submit voyage targets and receive optimized crew assignments |
| GET | `/api/roster` | Load current roster from `roster.json` |
| POST | `/api/roster` | Save updated roster to `roster.json` |
| GET | `/api/ship-config` | Load current ship configuration |
| POST | `/api/ship-config` | Save ship configuration |

### Acceptance Criteria
- [ ] All API endpoints return correct JSON responses
- [ ] Error handling for invalid inputs returns 400 status codes
- [ ] File I/O operations handle missing/malformed files gracefully
- [ ] API responds within 2 seconds for standard optimization requests
- [ ] All API tests pass

### Test Instructions
```bash
python -m pytest test_api.py -v
```

---

## Phase 3: PyWebView Integration

### Objectives
- Integrate Flask server with PyWebView for native desktop delivery
- Implement graceful startup and shutdown logic
- Configure window properties (size, title, resizable)

### Deliverables
1. [`app.py`](app.py) - Main application launcher

### Acceptance Criteria
- [ ] Flask server starts on `localhost:5000` in a background thread
- [ ] PyWebView window opens pointing to `http://127.0.0.1:5000`
- [ ] Window displays correct title: "Ship Crew Optimizer"
- [ ] Window size defaults to 1200x800 pixels
- [ ] Graceful shutdown occurs when window is closed (Flask server stops)
- [ ] No console window appears on Windows (if possible)
- [ ] Application launches successfully with `python app.py`

### Test Instructions
```bash
python app.py
```
Expected: Native window opens, displays frontend (placeholder during Phase 3), closes cleanly.

---

## Phase 4: Frontend UI & Roster Management

### Objectives
- Build modern desktop-style UI with Tailwind CSS
- Implement voyage target configuration forms
- Create crew selection and management interface
- Add result card display for optimization output

### Deliverables
1. [`templates/index.html`](templates/index.html) - Complete frontend

### UI Sections
1. **Voyage Configuration Panel**
   - Input fields for target stats (Morale, Combat, Seafaring)
   - Checkboxes for building bonuses
   - Checkboxes for consumable buffs
   - "Optimize" button

2. **Roster Management Panel**
   - Captain selection dropdown
   - Crew member list with checkboxes
   - Ship upgrades configuration
   - Save/Load roster buttons

3. **Results Panel**
   - Optimized crew assignment cards
   - Stat breakdown per result
   - Sort/rank indicators
   - Export configuration option

### Acceptance Criteria
- [ ] Tailwind CSS loads correctly via CDN
- [ ] All form inputs accept valid input and reject invalid input
- [ ] "Optimize" button triggers API call to `/api/optimize`
- [ ] Result cards display correctly with stat breakdowns
- [ ] Roster save/load functions work with `roster.json`
- [ ] UI is responsive and works at 1200x800 resolution
- [ ] No JavaScript console errors

### Test Instructions
Manual testing:
1. Launch application with `python app.py`
2. Configure voyage targets and click "Optimize"
3. Verify results match expected optimization output
4. Save and load roster - verify file integrity

---

## Phase 5: Integration Testing & Polish

### Objectives
- End-to-end testing of all components
- Performance optimization for large rosters
- Bug fixes and edge case handling
- Final documentation and packaging

### Deliverables
1. `test_integration.py` - Full integration test suite
2. `requirements.txt` - Final dependency list
3. `build.bat` - Windows packaging script (optional)

### Acceptance Criteria
- [ ] Full workflow: Load roster → Configure voyage → Optimize → Display results → Save config
- [ ] Application handles rosters with 50+ crew members efficiently
- [ ] Optimization completes within 5 seconds for standard inputs
- [ ] No memory leaks during repeated optimization calls
- [ ] All previous phase tests still pass
- [ ] `requirements.txt` lists all dependencies with version pins
- [ ] README.md updated with setup instructions

### Test Instructions
```bash
python -m pytest test_integration.py -v
python -m pytest test_solver.py -v
python -m pytest test_api.py -v
```

---

## Dependency Summary

| Package | Purpose | Phase |
|---------|---------|-------|
| flask | Backend API | Phase 2 |
| pywebview | Native window | Phase 3 |
| pytest | Testing | Phase 1 |
| dataclasses | Data models (stdlib) | Phase 1 |
| itertools | Combination generation (stdlib) | Phase 1 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| PyWebView installation issues on Windows | Provide fallback to browser-based testing |
| Large roster performance | Implement caching and combination pruning |
| Tailwind CDN availability | Include local fallback CSS |
| Flask threading conflicts | Use proper lock mechanisms for shared state |
