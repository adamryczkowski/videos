# Code Review Action Plan

**Project:** videos
**Created:** 2025-12-30
**Based on:** [Code Review Findings](code-review-findings.md)

---

## Overview

This document outlines a structured plan for addressing the findings from the code review. The plan is organized into milestones, prioritized by severity and logical grouping of related changes.

---

## Milestone 1: Critical Bug Fix

**Priority:** Immediate
**Estimated Effort:** 15 minutes
**Dependencies:** None

### Objective
Fix the critical bug that prevents multi-threaded downloads from working.

### Tasks

| Task | Finding | File | Description |
|------|---------|------|-------------|
| 1.1 | F15 | [`videos/threads.py:38`](../videos/threads.py:38) | Change `*.json` to `*.link` in glob pattern |

### Implementation Details

**Task 1.1: Fix file extension mismatch**

```python
# Before (line 38):
links = [json_file for json_file in path.glob("*.json")]

# After:
links = [json_file for json_file in path.glob("*.link")]
```

### Verification
- Run `just test` to ensure tests pass
- Run `just validate` to ensure no regressions
- Manual test: Create a `.link` file and verify `download_all` command finds it

---

## Milestone 2: Version Synchronization

**Priority:** High
**Estimated Effort:** 30 minutes
**Dependencies:** None

### Objective
Establish a single source of truth for version numbers.

### Tasks

| Task | Finding | File | Description |
|------|---------|------|-------------|
| 2.1 | F1 | [`videos/_version.py`](../videos/_version.py) | Update to `1.6.0` |
| 2.2 | F1 | [`README.adoc:180`](../README.adoc:180) | Update version history |
| 2.3 | F1 | Multiple | Document versioning process in README |

### Implementation Details

**Task 2.1: Update `_version.py`**
```python
__version__ = "1.6.0"
```

**Task 2.2: Update README version history**
```asciidoc
== Version History

* 1.6.0: Current version - Bug fixes and documentation improvements
* 1.5.3: Multi-threading support improvements
```

**Task 2.3: Add versioning documentation**
Add a section to README explaining that `pyproject.toml` is the source of truth for version.

### Verification
- Grep for version strings: `rg "1\.[56]\." --type py --type toml`
- Run `just validate`

---

## Milestone 3: Documentation Improvements

**Priority:** High
**Estimated Effort:** 2-3 hours
**Dependencies:** None

### Objective
Add comprehensive docstrings and update README with accurate information.

### Tasks

| Task | Finding | File | Description |
|------|---------|------|-------------|
| 3.1 | F3 | [`videos/main.py`](../videos/main.py) | Add docstrings to `Main` class and methods |
| 3.2 | F3 | [`videos/video.py`](../videos/video.py) | Add docstrings to `Video` class and methods |
| 3.3 | F3 | [`videos/videos.py`](../videos/videos.py) | Add docstrings to `Videos` class and methods |
| 3.4 | F3 | [`videos/functions.py`](../videos/functions.py) | Add docstrings to all functions |
| 3.5 | F3 | [`videos/threads.py`](../videos/threads.py) | Add docstrings to `DownloadWorker` class |
| 3.6 | F4 | [`README.adoc:129-133`](../README.adoc:129) | Update dependencies section |
| 3.7 | F5 | [`README.adoc`](../README.adoc) | Document all configuration options |

### Implementation Details

**Task 3.1-3.5: Docstring Template**

Use Google-style docstrings:
```python
def function_name(param1: Type, param2: Type) -> ReturnType:
    """Short description of function.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ExceptionType: When this exception is raised.
    """
```

**Task 3.6: Update dependencies**
```asciidoc
== Dependencies

* Python 3.10+
* yt-dlp: Video downloading
* toml: Configuration file writing
* Deno 2.0+: Required for YouTube signature extraction (see spack.yaml)
* Firefox: Required for cookie-based authentication (configurable)
```

**Task 3.7: Configuration options documentation**
Add a comprehensive table of all configuration options with types, defaults, and descriptions.

### Verification
- Run `just validate` (pyright will check docstring types)
- Consider adding `interrogate` hook to enforce docstring coverage

---

## Milestone 4: Error Handling & Robustness

**Priority:** Medium
**Estimated Effort:** 2 hours
**Dependencies:** Milestone 1

### Objective
Improve error handling consistency and robustness.

### Tasks

| Task | Finding | File | Description |
|------|---------|------|-------------|
| 4.1 | F17 | [`videos/functions.py:14-23`](../videos/functions.py:14) | Add `DownloadError` handling |
| 4.2 | F16 | [`videos/video.py:97-99`](../videos/video.py:97) | Fix progress hook type handling |
| 4.3 | F19 | [`videos/threads.py:19-31`](../videos/threads.py:19) | Add file existence check and error logging |
| 4.4 | F21 | [`videos/videos.py:12-19`](../videos/videos.py:12) | Add configuration validation |

### Implementation Details

**Task 4.1: Add error handling to `download_all`**
```python
def download_all(conf_file: Path | str = "video_downloads.toml"):
    m = Main(conf_file)
    path = m.link_queue_dir
    for json_file in path.glob("*.link"):
        with open(json_file, "rb") as f:
            json_entry = json.load(f)
        vid = Video(json_entry)
        assert str(m.link_queue_dir / vid.json_filename) == str(json_file)
        try:
            vid.download(m.target_prefix)
        except yt_dlp.DownloadError:
            json_file.rename(json_file.with_suffix(".broken"))
        else:
            Path(json_file).unlink()
```

**Task 4.2: Fix progress hook**
```python
def download(self, dir: Path) -> Path | None:
    filename: str | dict = ""
    # ... existing code ...
    if isinstance(filename, dict) and "filename" in filename:
        return Path(filename["filename"])
    return None
```

**Task 4.3: Add robustness to worker**
```python
def run(self):
    while True:
        directory, link = self.queue.get()
        try:
            link_path = Path(link)
            if not link_path.exists():
                logger.warning("Link file no longer exists: %s", link)
                continue
            download_link(link_path, directory)
        except Exception as e:
            logger.error("Failed to download %s: %s", link, e)
        finally:
            self.queue.task_done()
```

**Task 4.4: Add configuration validation**
```python
def load_config(conf_file: Path | str) -> dict:
    with open(str(conf_file), "rb") as f:
        data = tomllib.load(f)

    # Validate required keys for channel config
    if "link" in data or "target_folder" in data:
        required_keys = ["link", "target_folder"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required configuration key: {key}")

    data.setdefault("max_height", 1080)
    data.setdefault("last_download_index", 0)
    return data
```

### Verification
- Run `just test`
- Run `just validate`
- Manual testing with edge cases

---

## Milestone 5: Code Quality Improvements

**Priority:** Medium
**Estimated Effort:** 2-3 hours
**Dependencies:** Milestones 1-4

### Objective
Improve code quality, consistency, and maintainability.

### Tasks

| Task | Finding | File | Description |
|------|---------|------|-------------|
| 5.1 | F7 | [`videos/threads.py:7`](../videos/threads.py:7) | Fix import to use direct source |
| 5.2 | F13 | Multiple | Replace print statements with logging |
| 5.3 | F14 | [`videos/video.py`](../videos/video.py), [`videos/threads.py`](../videos/threads.py) | Use constant for file extension |
| 5.4 | F11 | [`videos/video.py:14`](../videos/video.py:14) | Rename `LoadFromJSON` to `load_from_json` |
| 5.5 | F8 | [`videos/videos.py:1-5`](../videos/videos.py:1) | Add clarifying comments for imports |
| 5.6 | F18 | [`videos/videos.py:155`](../videos/videos.py:155) | Remove unused variable |
| 5.7 | F22 | Multiple | Remove commented-out code |

### Implementation Details

**Task 5.1: Fix import**
```python
# Before:
from .functions import Main

# After:
from .main import Main, download_link
```

**Task 5.2: Replace print with logging**
```python
import logging
logger = logging.getLogger(__name__)

# Replace:
print(f"Checking for new videos from {self._conf['target_folder']}...")
# With:
logger.info("Checking for new videos from %s...", self._conf['target_folder'])
```

**Task 5.3: Add file extension constant**
```python
# In videos/common.py or videos/__init__.py:
LINK_FILE_EXTENSION = ".link"

# Usage:
file = strhash[:20] + LINK_FILE_EXTENSION
links = [f for f in path.glob(f"*{LINK_FILE_EXTENSION}")]
```

**Task 5.4: Rename method**
```python
@staticmethod
def load_from_json(json_path: Path) -> "Video":
    """Load a Video instance from a JSON file."""
    with open(str(json_path), "rb") as f:
        json_entry = json.load(f)
    return Video(json_entry)
```

Note: This is a breaking change for any external code using `LoadFromJSON`.

### Verification
- Run `just validate`
- Run `just test`

---

## Milestone 6: Type Safety Improvements

**Priority:** Medium
**Estimated Effort:** 3-4 hours
**Dependencies:** Milestones 1-5

### Objective
Address type issues properly instead of suppressing warnings.

### Tasks

| Task | Finding | File | Description |
|------|---------|------|-------------|
| 6.1 | F10 | [`videos/videos.py`](../videos/videos.py) | Create TypedDict for yt-dlp responses |
| 6.2 | F10 | [`videos/video.py`](../videos/video.py) | Fix interface method signatures |
| 6.3 | F9 | [`videos/video.py`](../videos/video.py) | Remove unused `_parent` attribute |
| 6.4 | F10 | Multiple | Remove `pyright: ignore` comments where possible |

### Implementation Details

**Task 6.1: Create TypedDict for yt-dlp responses**
```python
from typing import TypedDict, NotRequired

class VideoEntry(TypedDict):
    id: str
    title: str
    url: str
    duration: float
    my_index: NotRequired[int]
    my_title: NotRequired[str]
    max_height: NotRequired[int]

class PlaylistInfo(TypedDict):
    entries: list[VideoEntry]
    channel: str
    channel_url: str
    webpage_url_domain: NotRequired[str]
```

**Task 6.2-6.4: Fix interface mismatches**
Review each `pyright: ignore` comment and either:
1. Fix the underlying type issue
2. Update the interface to match the implementation
3. Add proper type annotations

### Verification
- Run `just typecheck`
- Run `just validate`
- Aim for zero `pyright: ignore` comments

---

## Milestone 7: Test Coverage

**Priority:** High
**Estimated Effort:** 4-6 hours
**Dependencies:** Milestones 1-6

### Objective
Significantly improve test coverage with meaningful unit tests.

### Tasks

| Task | Finding | File | Description |
|------|---------|------|-------------|
| 7.1 | F23 | [`tests/`](../tests/) | Add unit tests for `Video` class |
| 7.2 | F23 | [`tests/`](../tests/) | Add unit tests for `Videos` class |
| 7.3 | F23 | [`tests/`](../tests/) | Add unit tests for configuration loading |
| 7.4 | F23 | [`tests/`](../tests/) | Add unit tests for error handling |
| 7.5 | F23 | [`pyproject.toml`](../pyproject.toml) | Add pytest-mock dependency |

### Implementation Details

**Task 7.5: Add pytest-mock**
```toml
[tool.poetry.group.test.dependencies]
pytest = "^8.3.0"
coverage = "^7.6.0"
pytest-mock = "^3.12.0"
```

**Task 7.1-7.4: Test structure**
```python
# tests/test_video.py
import pytest
from unittest.mock import Mock, patch
from videos import Video

class TestVideo:
    def test_load_from_json(self, tmp_path):
        """Test loading video from JSON file."""
        # Create test JSON file
        json_file = tmp_path / "test.link"
        json_file.write_text('{"id": "abc123", "title": "Test", ...}')

        video = Video.load_from_json(json_file)
        assert video.id == "abc123"

    def test_json_filename_truncation(self):
        """Test that JSON filename is truncated to 20 chars."""
        entry = {"id": "a" * 30, ...}
        video = Video(entry)
        assert len(video.json_filename) == 25  # 20 + ".link"

    @patch("videos.video.yt_dlp.YoutubeDL")
    def test_download_success(self, mock_ytdl, tmp_path):
        """Test successful download."""
        # ... mock yt-dlp and verify behavior
```

### Verification
- Run `just test`
- Check coverage report: aim for >80% coverage
- Run `just validate`

---

## Milestone 8: Configuration & Cleanup

**Priority:** Low
**Estimated Effort:** 1-2 hours
**Dependencies:** Milestones 1-7

### Objective
Make hardcoded values configurable and clean up dead code.

### Tasks

| Task | Finding | File | Description |
|------|---------|------|-------------|
| 8.1 | F12 | [`videos/video.py`](../videos/video.py) | Make browser configurable |
| 8.2 | F12 | [`videos/video.py`](../videos/video.py) | Make subtitle languages configurable |
| 8.3 | F12 | [`videos/threads.py`](../videos/threads.py) | Document default worker count |
| 8.4 | F6 | [`videos/common.py`](../videos/common.py) | Remove or populate with constants |
| 8.5 | F24 | [`videos/functions.py`](../videos/functions.py) | Rename or remove duplicate `download_all` |
| 8.6 | F20 | [`videos/threads.py`](../videos/threads.py) | Document daemon thread behavior |

### Implementation Details

**Task 8.1-8.2: Configuration options**
Add to channel TOML config:
```toml
browser = "firefox"  # or "chrome", "edge", etc.
subtitle_languages = ["pl", "en", "ru"]
```

**Task 8.4: Populate common.py**
```python
"""Common constants and utilities for the videos package."""

LINK_FILE_EXTENSION = ".link"
DEFAULT_MAX_HEIGHT = 1080
DEFAULT_WORKER_COUNT = 3
DEFAULT_SUBTITLE_LANGUAGES = ["pl", "en", "ru"]
DEFAULT_BROWSER = "firefox"
```

**Task 8.5: Rename duplicate function**
Rename `download_all` in `functions.py` to `download_all_sequential` or remove it entirely if unused.

### Verification
- Run `just validate`
- Update README with new configuration options

---

## Milestone 9: Optional Enhancements

**Priority:** Low
**Estimated Effort:** 1 hour
**Dependencies:** All previous milestones

### Objective
Optional improvements for better developer experience.

### Tasks

| Task | Finding | File | Description |
|------|---------|------|-------------|
| 9.1 | F27 | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) | Add docstring enforcement hook |
| 9.2 | F28 | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) | Consider Ruff rule consolidation |
| 9.3 | F2 | [`docs/`](../docs/) | Expand API documentation |

### Implementation Details

**Task 9.1: Add interrogate hook**
```yaml
- repo: https://github.com/econchick/interrogate
  rev: 1.7.0
  hooks:
    - id: interrogate
      args: [-vv, --fail-under=80, --ignore-init-method, --ignore-magic]
```

### Verification
- Run `just validate`

---

## Summary Timeline

| Milestone | Priority | Effort | Dependencies |
|-----------|----------|--------|--------------|
| M1: Critical Bug Fix | Immediate | 15 min | None |
| M2: Version Sync | High | 30 min | None |
| M3: Documentation | High | 2-3 hrs | None |
| M4: Error Handling | Medium | 2 hrs | M1 |
| M5: Code Quality | Medium | 2-3 hrs | M1-M4 |
| M6: Type Safety | Medium | 3-4 hrs | M1-M5 |
| M7: Test Coverage | High | 4-6 hrs | M1-M6 |
| M8: Configuration | Low | 1-2 hrs | M1-M7 |
| M9: Enhancements | Low | 1 hr | All |

**Total Estimated Effort:** 16-22 hours

---

## Tracking Progress

Use this checklist to track completion:

- [ ] **Milestone 1**: Critical Bug Fix
  - [ ] Task 1.1: Fix `.json` → `.link`
- [ ] **Milestone 2**: Version Synchronization
  - [ ] Task 2.1: Update `_version.py`
  - [ ] Task 2.2: Update README version history
  - [ ] Task 2.3: Document versioning process
- [ ] **Milestone 3**: Documentation Improvements
  - [ ] Task 3.1-3.5: Add docstrings
  - [ ] Task 3.6: Update dependencies
  - [ ] Task 3.7: Document configuration options
- [ ] **Milestone 4**: Error Handling & Robustness
  - [ ] Task 4.1-4.4: Implement error handling
- [ ] **Milestone 5**: Code Quality Improvements
  - [ ] Task 5.1-5.7: Code cleanup
- [ ] **Milestone 6**: Type Safety Improvements
  - [ ] Task 6.1-6.4: Fix type issues
- [ ] **Milestone 7**: Test Coverage
  - [ ] Task 7.1-7.5: Add unit tests
- [ ] **Milestone 8**: Configuration & Cleanup
  - [ ] Task 8.1-8.6: Configuration and cleanup
- [ ] **Milestone 9**: Optional Enhancements
  - [ ] Task 9.1-9.3: Optional improvements
