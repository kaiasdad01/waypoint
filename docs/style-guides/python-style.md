This comprehensive Python code style guide synthesizes the industry-standard **PEP 8** and the **Google Python Style Guide**. It is designed to maximize readability, maintainability, and consistency across projects.

---

# Comprehensive Python Code Style Guide

## 1. Code Layout & Formatting

Consistency in layout is the foundation of readable code.

* **Indentation:** Use **4 spaces** per indentation level. Never use tabs.
* **Maximum Line Length:**
* **PEP 8:** 79 characters for code; 72 for docstrings/comments.
* **Google:** 80 characters.
* *Recommendation:* Aim for **80 characters**; use 100+ only if the team agrees and it improves readability.


* **Line Breaking:** * Prefer breaking **before** binary operators (the "math" style).
* Use implicit line joining inside parentheses, brackets, and braces. Avoid backslashes (`\`) unless necessary (e.g., long `with` statements in older Python versions).


* **Blank Lines:**
* **Top-level:** 2 blank lines between functions and classes.
* **Inside classes:** 1 blank line between methods.
* **Inside functions:** Use sparingly to separate logical sections.


* **Trailing Commas:** Use a trailing comma in sequences of items when each item is on a new line. This makes diffs cleaner.

## 2. Whitespace & Statements

* **Avoid extraneous whitespace:**
* Immediately inside `()`, `[]`, or `{}`.
* Before a comma, semicolon, or colon.
* Immediately before the open parenthesis of a function call.


* **Operators:** Always surround assignment (`=`), comparisons (`==`, `<`), and booleans (`and`, `or`) with a single space.
* **Function Arguments:**
* `def func(a=1):` No spaces around `=` for default values.
* `def func(a: int = 1):` Use spaces around `=` **only** when combined with a type hint.


* **Compound Statements:** Generally, do not put multiple statements on the same line (e.g., `if x: y` is discouraged).

## 3. Imports

Imports should be at the top of the file, after the module docstring and before globals.

* **Order:**
1. Standard library imports.
2. Related third-party imports.
3. Local application/library-specific imports.


* *Note:* Separate each group with a single blank line.


* **Style:**
* **Absolute imports** are preferred over relative imports.
* **Google Preference:** Import modules and packages only (e.g., `import os` or `from subprocess import echo`). Do not import individual classes/functions unless they are from the `typing` module.
* **PEP 8 Preference:** Importing classes is acceptable (e.g., `from my_module import MyClass`).
* *Consensus:* If the class name is unique and clear, `from module import Class` is fine. If it's ambiguous, use `import module` and `module.Class`.


* **Wildcards:** Never use `from module import *`.

## 4. Naming Conventions

Naming reflects the usage, not the implementation.

| Entity | Convention | Example |
| --- | --- | --- |
| **Packages / Modules** | Short, lowercase, no underscores | `utilities`, `my_package` |
| **Classes** | PascalCase (CapWords) | `UserAccount` |
| **Functions / Methods** | snake_case | `calculate_total()` |
| **Variables / Arguments** | snake_case | `user_id` |
| **Constants** | UPPER_SNAKE_CASE | `MAX_RETRIES = 5` |
| **Internal Members** | Leading underscore | `_private_helper()` |
| **Protected / Mangled** | Double leading underscore | `__mangled_attr` |

* **Avoid:** Single-letter names like `l` (lowercase L), `O` (uppercase O), or `I` (uppercase i) as they are easily confused with numbers.

## 5. Programming Practices

* **Exceptions:**
* Use specific exceptions (e.g., `ValueError`) rather than a broad `except Exception:`.
* Minimize the code inside `try` blocks to avoid catching unexpected bugs.
* Use `finally` for cleanup (e.g., closing files).


* **Comprehensions:** Use for simple cases. If a list comprehension or generator expression spans multiple `for` clauses or is hard to read, use a standard loop.
* **Return Statements:** Be consistent. If a function can return `None`, use `return None` explicitly. If it reaches the end naturally, it returns `None` implicitly.
* **Global State:** Avoid mutable global state. Use module-level constants instead.
* **The Main Gate:** Use `if __name__ == '__main__':` for executable scripts.

## 6. Documentation & Comments

Code is read more often than written; document it for the next person.

* **Docstrings (PEP 257):**
* Use `"""Triple double quotes"""` for all docstrings.
* **Google Style Docstrings:** For functions, include sections for `Args:`, `Returns:`, and `Raises:`.


```python
def connect(user: str, timeout: int = 10) -> bool:
    """Connects to the server.

    Args:
        user: The username to authenticate.
        timeout: Seconds to wait before timing out.

    Returns:
        True if successful, False otherwise.

    Raises:
        ConnectionError: If the server is unreachable.
    """

```


* **Comments:**
* **Block Comments:** Indented to the same level as the code.
* **Inline Comments:** Separated by at least two spaces from the code. Use sparingly.
* **TODOs:** Use the format `# TODO(username): description of task` (Google style).



## 7. Type Annotations

Modern Python should be type-annotated to improve tooling and catch bugs.

* **Function Signatures:** Annotate arguments and return types: `def func(x: int) -> str:`.
* **Variables:** Annotate complex types if not obvious: `names: list[str] = []`.
* **Forward References:** Use `from __future__ import annotations` (Python 3.7+) to allow using a class as a type hint inside its own definition.

---

### Summary Checklist for a Code Review:

1. Is indentation 4 spaces?
2. Are imports sorted and grouped?
3. Are names `snake_case` (functions) or `PascalCase` (classes)?
4. Is the line length under 80 characters?
5. Are docstrings present and descriptive?
6. Are type hints used where appropriate?