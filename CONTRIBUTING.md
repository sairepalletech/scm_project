# Contributing to SCM Platform

Thank you for your interest in contributing to SCM Platform! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Documentation](#documentation)
- [Testing](#testing)
- [Community](#community)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow:

- **Be respectful**: Treat everyone with respect and consideration
- **Be collaborative**: Work together towards common goals
- **Be inclusive**: Welcome and support people of all backgrounds
- **Be constructive**: Provide helpful feedback and criticism
- **Be patient**: Remember that people have different skill levels and learning curves

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title**: Summarize the issue in one line
- **Description**: Detailed description of the problem
- **Steps to reproduce**: Step-by-step instructions
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, SCM version
- **Logs**: Relevant log output or error messages

**Template**:
```markdown
**Bug Description**
A clear description of the bug.

**To Reproduce**
1. Run command '...'
2. Observe error '...'

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: Ubuntu 20.04
- Python: 3.8
- SCM Version: 1.0.0

**Logs**
```
[paste logs here]
```
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear title**: Describe the enhancement
- **Provide rationale**: Explain why this enhancement would be useful
- **Describe alternatives**: What alternatives have you considered
- **Additional context**: Any other relevant information

### Contributing Code

#### Areas for Contribution

**Phase 1 (Current - Q1)**:
- Core API implementation (REST + gRPC)
- Orchestrator and scheduler
- Plugin SDK development (Go, Python, Node.js)
- Plugin implementations (GitHub, GitLab, AWS, etc.)
- Documentation improvements
- Testing and quality assurance

**Future Phases**:
- UI/UX improvements
- Performance optimizations
- Security enhancements
- New integrations
- Deployment tooling

#### First-Time Contributors

Look for issues labeled `good-first-issue` or `help-wanted`. These are great starting points for new contributors.

### Contributing Documentation

Documentation is crucial for adoption. You can contribute by:

- Fixing typos and grammar
- Improving clarity and organization
- Adding examples and tutorials
- Creating diagrams and visuals
- Writing plugin guides
- Translating documentation

## Development Setup

### Prerequisites

- Python 3.6 or higher
- Git
- pip (Python package manager)
- Virtual environment tool (venv or virtualenv)

### Local Development

1. **Fork the repository**

   Click the "Fork" button on GitHub

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR-USERNAME/scm_project.git
   cd scm_project
   ```

3. **Add upstream remote**

   ```bash
   git remote add upstream https://github.com/sairepalletech/scm_project.git
   ```

4. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

6. **Create a branch**

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_scm.py -v

# Run with coverage
pytest tests/ --cov=scm_config --cov-report=html
```

### Code Style

We use Python coding standards:

```bash
# Format code (if using black)
black scm_config/

# Lint code (if using pylint)
pylint scm_config/

# Type checking (if using mypy)
mypy scm_config/
```

## Pull Request Process

### Before Submitting

1. **Update documentation**: If you change functionality, update relevant docs
2. **Add tests**: Ensure your code is tested
3. **Run tests**: Make sure all tests pass
4. **Update CHANGELOG**: Add entry describing your changes (if applicable)
5. **Rebase on upstream**: Ensure your branch is up-to-date

   ```bash
   git fetch upstream
   git rebase upstream/master
   ```

### Submitting a Pull Request

1. **Push your branch**

   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**

   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template

3. **PR Title Format**

   Use conventional commits format:
   ```
   feat: Add GitHub plugin connector
   fix: Resolve authentication timeout issue
   docs: Update plugin development guide
   test: Add integration tests for workflow DSL
   refactor: Simplify orchestrator scheduling logic
   ```

4. **PR Description Template**

   ```markdown
   ## Description
   Brief description of what this PR does.

   ## Motivation
   Why is this change needed?

   ## Changes
   - Change 1
   - Change 2

   ## Testing
   How has this been tested?

   ## Screenshots (if applicable)
   Add screenshots for UI changes.

   ## Checklist
   - [ ] Tests pass locally
   - [ ] Documentation updated
   - [ ] CHANGELOG updated (if applicable)
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   ```

### Review Process

1. **Automated checks**: CI/CD runs tests and linters
2. **Code review**: Maintainers review your code
3. **Address feedback**: Make requested changes
4. **Approval**: Once approved, your PR will be merged

### After Your PR is Merged

1. **Delete your branch**

   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your fork**

   ```bash
   git checkout master
   git pull upstream master
   git push origin master
   ```

## Coding Standards

### Python Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions small and focused
- Avoid deep nesting (max 3 levels)
- Use type hints where appropriate

### Example

```python
"""Module for GitHub integration."""
from typing import Dict, List, Optional


class GitHubConnector:
    """Connector for GitHub API operations."""

    def __init__(self, token: str):
        """
        Initialize the GitHub connector.

        Args:
            token: GitHub personal access token
        """
        self.token = token

    def create_repository(
        self,
        name: str,
        visibility: str = "private",
        description: Optional[str] = None
    ) -> Dict:
        """
        Create a new GitHub repository.

        Args:
            name: Repository name
            visibility: Repository visibility (public/private)
            description: Optional repository description

        Returns:
            Dictionary with repository details

        Raises:
            GitHubAPIError: If API request fails
        """
        # Implementation
        pass
```

### Commit Messages

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example**:
```
feat(plugins): Add GitHub connector plugin

Implement GitHub connector with support for:
- Repository CRUD operations
- Branch protection rules
- Pull request management

Closes #123
```

## Documentation

### Documentation Structure

```
docs/
├── architecture/       # Architecture documents
├── plugins/           # Plugin development guides
├── api/              # API specifications
├── deployment/       # Deployment guides
└── security/         # Security documentation
```

### Writing Documentation

- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Link to related documentation
- Keep it up-to-date with code changes

### Markdown Style

- Use ATX-style headers (`#` for h1, `##` for h2, etc.)
- Add blank lines around headers
- Use fenced code blocks with language identifiers
- Use relative links for internal references

## Testing

### Test Types

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **Conformance Tests**: Test plugin compliance

### Writing Tests

```python
import pytest
from scm_config import some_module


def test_feature_works():
    """Test that feature works as expected."""
    result = some_module.do_something()
    assert result == expected_value


def test_feature_handles_error():
    """Test that feature handles errors gracefully."""
    with pytest.raises(ExpectedError):
        some_module.do_something_invalid()


@pytest.mark.parametrize("input,expected", [
    ("input1", "output1"),
    ("input2", "output2"),
])
def test_feature_with_parameters(input, expected):
    """Test feature with different parameters."""
    assert some_module.process(input) == expected
```

### Test Coverage

Aim for:
- **Unit tests**: 80%+ coverage
- **Critical paths**: 100% coverage
- **New features**: Must include tests

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Requests**: Code contributions

### Getting Help

If you need help:

1. Check existing documentation
2. Search closed issues for similar problems
3. Ask in GitHub Discussions
4. Open a new issue if needed

### Recognition

Contributors are recognized in:
- Release notes
- CONTRIBUTORS.md file
- Annual contributor highlights

## License

By contributing to SCM Platform, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you have questions about contributing, please open an issue or start a discussion on GitHub.

---

Thank you for contributing to SCM Platform! 🎉
