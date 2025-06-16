# Contributing to AfCyberSiem Platform

Thank you for your interest in contributing to the AfCyberSiem Platform! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### 🐛 Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title** describing the issue
- **Detailed description** of the problem
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, versions, configuration)
- **Log files** and error messages
- **Screenshots** if applicable

### 💡 Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- **Clear title** and description
- **Use case** and business value
- **Proposed solution** or approach
- **Alternative solutions** considered
- **Implementation complexity** assessment

### 🔧 Pull Requests

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

#### Pull Request Guidelines

- **Clear title** and description
- **Reference** related issues
- **Include tests** for new functionality
- **Update documentation** as needed
- **Follow coding standards**
- **Keep changes focused** and atomic

## 📋 Development Guidelines

### 🏗️ Code Standards

#### Python Code
- Follow **PEP 8** style guide
- Use **type hints** where appropriate
- Include **docstrings** for functions and classes
- Write **unit tests** for new code
- Use **meaningful variable names**

#### Infrastructure Code
- **Terraform**: Use consistent formatting (`terraform fmt`)
- **Ansible**: Follow YAML best practices
- **Docker**: Use multi-stage builds and minimal base images
- **Documentation**: Include inline comments

#### Documentation
- Use **Markdown** for documentation
- Include **code examples** where helpful
- Keep **README files** up to date
- Use **clear headings** and structure

### 🧪 Testing

#### Unit Tests
```bash
# Python tests
python -m pytest tests/

# Terraform validation
terraform validate

# Ansible syntax check
ansible-playbook --syntax-check playbooks/site.yml
```

#### Integration Tests
```bash
# Docker Compose testing
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Terraform plan
terraform plan -var-file="test.tfvars"
```

### 📝 Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(terraform): add multi-tenant VLAN configuration
fix(ansible): resolve Wazuh indexer startup issue
docs(readme): update installation instructions
```

## 🏗️ Development Environment

### Prerequisites
- **Git** 2.20+
- **Python** 3.8+
- **Terraform** 1.0+
- **Ansible** 4.0+
- **Docker** 20.0+
- **Node.js** 16+ (for web development)

### Setup
```bash
# Clone repository
git clone https://github.com/ativoj/AfCyberSiem-platform.git
cd AfCyberSiem-platform

# Install Python dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Validate setup
make validate
```

### 🔧 Development Tools

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
  
  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:
      - id: flake8
```

#### Makefile Commands
```makefile
# Common development tasks
.PHONY: help validate test build deploy clean

help:           ## Show this help
validate:       ## Validate all code
test:           ## Run all tests
build:          ## Build containers
deploy:         ## Deploy to test environment
clean:          ## Clean up resources
```

## 📚 Documentation

### 📖 Writing Documentation

- **Clear and concise** language
- **Step-by-step** instructions
- **Code examples** with explanations
- **Screenshots** for UI components
- **Cross-references** to related sections

### 🌐 Website Updates

The documentation website is in the `docs/` directory:

```bash
# Local development
cd docs/
python -m http.server 8080

# Build for production
npm run build
```

## 🚀 Release Process

### 📋 Release Checklist

1. **Update version** numbers
2. **Update CHANGELOG.md**
3. **Run full test suite**
4. **Update documentation**
5. **Create release branch**
6. **Tag release**
7. **Deploy to staging**
8. **Validate deployment**
9. **Merge to main**
10. **Deploy to production**

### 🏷️ Versioning

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Example: `v1.2.3`

### 📝 Changelog

Keep `CHANGELOG.md` updated with:

```markdown
## [1.2.3] - 2024-01-15

### Added
- New threat hunting dashboard
- ML anomaly detection module

### Changed
- Improved Grafana dashboard performance
- Updated Wazuh to version 4.7

### Fixed
- Fixed Elasticsearch memory leak
- Resolved Docker networking issues

### Security
- Updated dependencies with security patches
```

## 🏆 Recognition

### 🌟 Contributors

All contributors are recognized in:
- **README.md** contributors section
- **Release notes** acknowledgments
- **Annual contributor report**

### 🎖️ Contribution Types

We recognize various contribution types:
- **Code** contributions
- **Documentation** improvements
- **Bug reports** and testing
- **Community support**
- **Design** and UX improvements
- **Translation** and localization

## 📞 Getting Help

### 💬 Communication Channels

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General questions and ideas
- **Discord** - Real-time community chat
- **Email** - security@afcybersiem.com (security issues)

### 🆘 Support

For development questions:
1. **Search** existing issues and discussions
2. **Check** documentation and guides
3. **Ask** in GitHub Discussions
4. **Join** Discord community

## 📄 Code of Conduct

### 🤝 Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity
- Gender identity and expression
- Level of experience, nationality
- Personal appearance, race, religion
- Sexual identity and orientation

### 📋 Standards

**Positive behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other members

**Unacceptable behavior:**
- Trolling, insulting/derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct inappropriate in a professional setting

### 🚨 Enforcement

Report violations to security@afcybersiem.com. All reports will be reviewed and investigated promptly and fairly.

## 📜 License

By contributing to AfCyberSiem Platform, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to AfCyberSiem Platform! 🙏**

