# Contributing to AI Gesture Mouse

Thank you for your interest in contributing to **AI Gesture Mouse**! We welcome bug reports, feature enhancements, documentation improvements, and feedback.

## Development Setup

1. **Fork and Clone the Repository**:
   ```bash
   git clone https://github.com/Rajapakshaminindu/AI-Gesture-Mouse.git
   cd AI-Gesture-Mouse
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Tests**:
   ```bash
   python -m pytest tests/
   ```

## Pull Request Guidelines

- Ensure code adheres to PEP8 guidelines (`flake8`).
- Add unit tests for new gesture recognition logic or mathematical filters.
- Use clear, descriptive conventional commit messages (e.g. `feat:`, `fix:`, `docs:`, `test:`).
- Document any new gestures in `docs/GESTURE_GUIDE.md`.
