# Code Cleanup Plan - Status Guide Project

This document outlines a comprehensive plan for ensuring clean code across the codebase according to the Python Style Guide (`docs/style-guides/python-style.md`), without affecting any functionality.

## Overview

The codebase is generally well-structured, but there are several areas where we can improve adherence to PEP 8 and Google Python Style Guide standards. This plan is organized by priority and category.

---

## Phase 1: High Priority - Code Layout & Formatting

### 1.1 Line Length Violations
**Issue:** Several lines exceed 80 characters (style guide recommendation).

**Files Affected:**
- `src/status_optimizer/cli/output.py` (23 lines)
- `src/status_optimizer/cli/main.py` (3 lines)
- `src/status_optimizer/search/beam_search.py` (multiple lines)
- `src/status_optimizer/constraints/constraint.py` (1 line)

**Action Items:**
1. Break long lines using implicit line joining (parentheses, brackets, braces)
2. Prefer breaking before binary operators (math style)
3. For function calls with many arguments, put each argument on its own line
4. For long f-strings, break into multiple lines

**Examples:**
- Line 101 in `output.py`: Long f-string with multiple concatenations
- Line 197 in `output.py`: Long f-string in day header
- Line 50 in `beam_search.py`: Long logger.info call

### 1.2 Blank Line Consistency
**Issue:** Need to verify consistent blank line usage.

**Action Items:**
1. Ensure 2 blank lines between top-level functions and classes
2. Ensure 1 blank line between methods inside classes
3. Remove extraneous blank lines inside functions (keep only for logical separation)

**Files to Review:**
- All module files for top-level spacing
- All class files for method spacing

### 1.3 Trailing Commas
**Issue:** Add trailing commas in multi-line sequences for cleaner diffs.

**Action Items:**
1. Add trailing commas to function arguments when each is on a new line
2. Add trailing commas to list/dict items when each is on a new line

**Files to Review:**
- `src/status_optimizer/cli/main.py` (import statements, function calls)
- `src/status_optimizer/search/__init__.py` (__all__ list)

---

## Phase 2: Medium Priority - Imports & Organization

### 2.1 Import Ordering
**Issue:** Some files may have imports not properly grouped.

**Action Items:**
1. Verify all files follow: stdlib → third-party → local
2. Ensure single blank line between each group
3. Sort imports alphabetically within each group

**Files to Review:**
- `src/status_optimizer/cli/main.py` (verify grouping)
- `src/status_optimizer/search/search.py` (verify grouping)
- `src/status_optimizer/data/providers/excel_flight_feed.py` (verify grouping)

### 2.2 Import Style Consistency
**Issue:** Mix of `from module import Class` and `import module` styles.

**Action Items:**
1. Review imports for clarity - prefer `from module import Class` when class name is unique
2. Use `import module` when class name might be ambiguous
3. Ensure consistency across similar modules

**Files to Review:**
- All files with imports

---

## Phase 3: Medium Priority - Documentation

### 3.1 Docstring Completeness
**Issue:** Some functions/classes may be missing docstrings or have incomplete Google-style docstrings.

**Action Items:**
1. Add module docstrings to all `__init__.py` files (currently many are placeholders)
2. Ensure all public functions have Google-style docstrings with:
   - Brief description
   - Args: section (if parameters exist)
   - Returns: section (if function returns)
   - Raises: section (if exceptions raised)
3. Add class docstrings with brief description

**Files Needing Docstrings:**
- `src/status_optimizer/__init__.py` (currently placeholder)
- `src/status_optimizer/domain/__init__.py` (currently placeholder)
- `src/status_optimizer/data/__init__.py` (currently placeholder)
- `src/status_optimizer/data/feeds/__init__.py` (currently placeholder)
- `src/status_optimizer/data/providers/__init__.py` (currently placeholder)

**Files to Review for Docstring Quality:**
- All domain model classes (Flight, Itinerary, Segment)
- All constraint classes
- All search algorithm classes

### 3.2 Type Annotation Completeness
**Issue:** Some functions may be missing type hints.

**Action Items:**
1. Add type hints to all function signatures
2. Add type hints to complex variables where not obvious
3. Use `from __future__ import annotations` if needed for forward references

**Files to Review:**
- `src/status_optimizer/data/providers/normalizers.py` (check all functions)
- All test files (add type hints where appropriate)

---

## Phase 4: Low Priority - Code Quality Improvements

### 4.1 Exception Handling
**Issue:** Review for broad exception catching.

**Action Items:**
1. Replace `except Exception:` with specific exceptions where possible
2. Ensure `try` blocks are minimal (only wrap code that can raise)
3. Add `finally` blocks for cleanup where needed

**Files to Review:**
- `src/status_optimizer/cli/main.py` (line 330: `except Exception`)
- `src/status_optimizer/data/providers/excel_flight_feed.py` (line 83: `except Exception`)

### 4.2 Return Statement Consistency
**Issue:** Ensure explicit `return None` when function can return None.

**Action Items:**
1. Review functions that can return None
2. Add explicit `return None` for clarity where appropriate

**Files to Review:**
- `src/status_optimizer/data/providers/normalizers.py` (functions returning Optional)

### 4.3 Variable Naming
**Issue:** Check for single-letter variables or unclear names.

**Action Items:**
1. Review for single-letter variables (except in comprehensions/loops where appropriate)
2. Ensure all variables use snake_case
3. Ensure all constants use UPPER_SNAKE_CASE

**Files to Review:**
- All files for naming consistency

### 4.4 Whitespace in Expressions
**Issue:** Verify proper spacing around operators.

**Action Items:**
1. Ensure single space around `=`, `==`, `<`, `>`, `and`, `or`
2. No spaces around `=` in default parameter values (unless combined with type hint)
3. Spaces around `=` when combined with type hints: `def func(a: int = 1)`

**Files to Review:**
- All files for operator spacing

---

## Phase 5: Code Organization

### 5.1 Module Organization
**Issue:** Some modules may benefit from better organization.

**Action Items:**
1. Ensure constants are defined at module level in UPPER_CASE
2. Ensure `__all__` is defined in `__init__.py` files where appropriate
3. Review module-level code organization

**Files to Review:**
- All `__init__.py` files for `__all__` definitions
- Module files for constant definitions

### 5.2 Comment Quality
**Issue:** Review comments for clarity and formatting.

**Action Items:**
1. Ensure block comments are indented to code level
2. Ensure inline comments are separated by at least 2 spaces
3. Convert TODO comments to format: `# TODO(username): description`
4. Remove redundant comments that just restate code

**Files to Review:**
- All files for comment quality

---

## Implementation Strategy

### Step 1: Automated Checks
1. Run `black --check` to identify formatting issues
2. Run `flake8` or `pylint` to identify style violations
3. Run `mypy` to identify type annotation issues

### Step 2: Manual Review
1. Review each file systematically following the plan above
2. Make changes incrementally, file by file
3. Run tests after each major change to ensure no functionality is affected

### Step 3: Verification
1. Run full test suite after all changes
2. Verify no functionality has changed
3. Review diff to ensure only style changes were made

---

## Files Requiring Attention (Priority Order)

### High Priority
1. `src/status_optimizer/cli/output.py` - Line length violations
2. `src/status_optimizer/cli/main.py` - Line length, exception handling
3. `src/status_optimizer/search/beam_search.py` - Line length
4. `src/status_optimizer/search/search.py` - Line length, docstrings

### Medium Priority
5. `src/status_optimizer/data/providers/excel_flight_feed.py` - Exception handling, line length
6. `src/status_optimizer/constraints/__init__.py` - Docstrings, line length
7. All `__init__.py` files - Add proper module docstrings

### Low Priority
8. `src/status_optimizer/data/providers/normalizers.py` - Type hints, return statements
9. All test files - Type hints, docstrings
10. All domain model files - Verify docstring completeness

---

## Testing Strategy

After each phase:
1. Run unit tests: `pytest tests/unit/`
2. Run integration tests: `pytest tests/integration/`
3. Run full test suite: `pytest`
4. Verify CLI still works: Test with sample commands

---

## Notes

- **No functionality changes**: All changes are style-only
- **Incremental approach**: Make changes file by file, test after each
- **Preserve behavior**: Ensure all tests pass before and after changes
- **Documentation**: Update any inline comments that become outdated

---

## Estimated Effort

- **Phase 1 (High Priority)**: 2-3 hours
- **Phase 2 (Medium Priority)**: 1-2 hours
- **Phase 3 (Medium Priority)**: 2-3 hours
- **Phase 4 (Low Priority)**: 1-2 hours
- **Phase 5 (Code Organization)**: 1 hour

**Total Estimated Time**: 7-11 hours

---

## Success Criteria

✅ All lines under 80 characters (or justified exceptions documented)
✅ All imports properly ordered and grouped
✅ All public functions/classes have Google-style docstrings
✅ All functions have type annotations
✅ All tests pass
✅ No functionality changes
✅ Code is more readable and maintainable

