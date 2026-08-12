# Contributing to Living Objects

Thank you for your interest in this research project.

## Philosophy

This is a **research project**, not a product. Our goal is to discover whether intelligent persistent software objects represent a genuinely useful next step in software architecture.

**Do not protect this idea.** If research proves it is just agents, accept that. If someone already built it, document it. If it fails at scale, understand why. If the best discovery is something different, follow the evidence.

## How to Contribute

### 1. Find Prior Art

The most valuable contribution is finding something that already solves this problem.

- Search academic papers, GitHub, technical blogs, conference proceedings
- If you find something, add it to `research/prior_art.md`
- Include: name, creators, date, URL, architecture, what it solves, what it does not solve, overlap, differences, threat level

### 2. Attack the Hypothesis

Try to prove the thesis wrong. This is not hostile — it is the scientific method.

- Read `research/hypotheses.md`
- Design an experiment that could falsify a hypothesis
- Run it and report results (positive or negative)
- Add results to `research/research_log.md`

### 3. Build Prototypes

- Proposals for new prototypes are welcome
- Each prototype must have a falsifiable hypothesis
- Prototypes live in `prototypes/`
- Each prototype needs: README, code, tests, results

### 4. Fix Bugs

- Prototype 1 (continuity test) should always pass
- If you find a bug, fix it and add a test

### 5. Improve Documentation

- Research documents should be clear, rigorous, and honest
- Architecture documents should be precise
- Code should be well-commented

## Code Standards

- Python 3.10+
- Type hints where possible
- Docstrings for all public methods
- Tests for all primitives
- No external API keys in code (use mock engines for tests)
- Event sourcing for all state changes
- Capability-based security model

## Research Standards

- Cite sources
- Do not claim novelty without evidence
- Record negative results
- Version everything
- Benchmark before optimizing

## Pull Request Process

1. Fork the repo
2. Create a branch: `research/your-topic` or `prototype/your-name`
3. Make your changes
4. Add tests
5. Update relevant research documents
6. Submit PR with clear description of what you did and why

## Questions?

Open an issue with the `question` label.

## Code of Conduct

- Be rigorous, not rude
- Critique ideas, not people
- Negative results are as valuable as positive ones
- Share credit generously
