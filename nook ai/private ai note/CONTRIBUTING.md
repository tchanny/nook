# 🤝 Contributing to Nook Engine

Thank you for your interest in Nook Engine! We welcome contributions from the community.

## 🚀 How to Contribute

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/nook-engine.git
cd nook-engine

# Add upstream
git remote add upstream https://github.com/nook-ai/nook-engine.git
```

### 2. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e ".[dev]"
```

### 3. Create Branch

```bash
# Create branch for your changes
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 4. Development

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style
- Add tests for new features
- Update documentation when necessary

### 5. Testing

```bash
# Run tests
pytest

# Check code style
black nook_engine/
flake8 nook_engine/

# Check types
mypy nook_engine/
```

### 6. Commit and Pull Request

```bash
# Add changes
git add .

# Create commit
git commit -m "feat: add new feature description"

# Push changes
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## 📋 Commit Rules

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - new feature
- `fix:` - bug fix
- `docs:` - documentation changes
- `style:` - code formatting
- `refactor:` - refactoring
- `test:` - adding tests
- `chore:` - dependency updates, etc.

## 🐛 Bug Reports

When creating an issue:

1. Describe the problem
2. Specify Python version and OS
3. Provide minimal example to reproduce
4. Describe expected behavior

## 💡 Feature Requests

When creating a feature request:

1. Describe the proposed feature
2. Explain why it's needed
3. Suggest possible implementation

## 📞 Contact

- GitHub Issues: for bugs and suggestions
- GitHub Discussions: for general questions
- Email: contact@nook.ai

Thank you for your contribution! 🎉
