# Contributing to AgentSkills

Thanks for your interest in contributing! 🎉

## Development Setup

```bash
# Clone the repo
git clone https://github.com/akshayaggarwal99/agentskills.git
cd agentskills

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
pip install -e .

# Verify installation
skill --help
```

## Project Structure

```
agentskills/
├── models.py      # Skill dataclass
├── providers.py   # SkillProvider abstraction
├── registry.py    # Multi-provider registry
└── cli.py         # CLI commands
```

## Adding a New Command

1. Add your command in `cli.py`:
```python
@app.command()
def my_command(arg: str):
    """Description shown in --help."""
    console.print(f"Hello {arg}!")
```

2. Test it:
```bash
pip install -e .
skill my-command world
```

## Adding a New Skill Provider

Implement the `SkillProvider` abstract class:

```python
from agentskills.providers import SkillProvider

class MyProvider(SkillProvider):
    @property
    def name(self) -> str:
        return "My Provider"
    
    @property
    def source_id(self) -> str:
        return "my-source"
    
    def fetch_skills(self, force_refresh=False) -> list[Skill]:
        # Fetch and return skills
        pass
    
    def install_skill(self, skill, target_dir) -> Path:
        # Copy skill to target_dir
        pass
```

## Code Style

- Use [ruff](https://github.com/astral-sh/ruff) for linting
- Keep functions focused and small
- Add docstrings to public functions

## Pull Request Process

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test locally: `pip install -e . && skill --help`
5. Submit a PR with a clear description

## Questions?

Open an issue or start a discussion!
