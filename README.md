# Tato Claude Plugins

A curated marketplace of productivity plugins for [Claude Code](https://claude.com/code).

## Available Plugins

| Plugin | Version | Category | Description |
|--------|---------|----------|-------------|
| [PRD Builder](./plugins/prd-builder/) | 1.0.0 | Productivity | Complete PRD generation and refinement system with 13 specialized skills |

## Installation

### Prerequisites

- Claude Code CLI installed (`claude` command available)
- Git

### Install a Plugin

#### Option 1: Add Marketplace (Recommended)

1. Add this marketplace to your known marketplaces:

```bash
# Add to ~/.claude/plugins/known_marketplaces.json
{
  "tato-plugins": {
    "source": {
      "source": "github",
      "repo": "tato/tato-claude-plugins"
    }
  }
}
```

2. Install plugins via Claude Code:

```bash
/plugin install prd-builder@tato-plugins
```

#### Option 2: Direct Installation

Clone the repository and install locally:

```bash
git clone https://github.com/tato/tato-claude-plugins.git
cd tato-claude-plugins
/plugin install ./plugins/prd-builder
```

### Verify Installation

After installing a plugin, verify it's working:

```bash
# Check that skills are available
/help | grep prd-

# Test a skill
/prd-status
```

## Quick Start: PRD Builder

Generate your first Product Requirements Document in 5 commands:

```bash
# 1. Install the plugin
/plugin install prd-builder@tato-plugins

# 2. Start a discovery session (gather context)
/prd-discover user-authentication

# 3. Generate the PRD from context
/prd-draft prd/user-authentication/prd-context-user-authentication.md

# 4. Analyze the quality
/prd-analyze prd/user-authentication/prd.md

# 5. Iteratively improve it
/prd-refine prd/user-authentication/prd.md
```

See the [PRD Builder documentation](./plugins/prd-builder/README.md) for comprehensive guides and advanced usage.

## Plugin Catalog

### PRD Builder

**Complete PRD generation and refinement system**

- **13 Skills**: Discovery, drafting, analysis, refinement, export, task generation, diagramming, UI prototyping, and navigation
- **5 Templates**: Full PRD (22 sections), 1-Pager (7 sections), Shape Up Pitch (6 sections), AI Product PRD (27 sections), Feature Document (11 sections)
- **Quality-driven**: 54-point rubric with automated scoring and improvement suggestions
- **Production-ready**: Comprehensive documentation, proven workflows, extensive examples

**Key Features**:
- Structured discovery sessions to gather context before writing
- Auto-detected PRD type with template-based generation
- Interactive refinement with targeted questions and gap identification
- Executive summaries for stakeholder distribution
- Task breakdown for engineering handoff
- Mermaid diagram generation (state machines, user flows, data models)
- Interactive UI prototype generation with frontend-design skill integration

[View PRD Builder Documentation →](./plugins/prd-builder/README.md)

## Development

### Adding a New Plugin

To add your own plugin to this marketplace:

1. Create plugin directory: `plugins/<plugin-name>/`
2. Add plugin metadata: `plugins/<plugin-name>/.claude-plugin/plugin.json`
3. Create plugin components (skills, commands, agents, etc.)
4. Update marketplace catalog: `.claude-plugin/marketplace.json`
5. Add plugin documentation: `plugins/<plugin-name>/README.md`
6. Update this README with plugin listing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines. *(Coming soon)*

### Testing Locally

Before publishing, test plugins locally:

```bash
# Install from local directory
/plugin install ./plugins/<plugin-name>

# Verify installation
/help | grep <plugin-skills>

# Test functionality
# Run plugin skills and verify they work as expected
```

## Updates

To update an installed plugin:

```bash
/plugin update prd-builder@tato-plugins
```

To update all plugins:

```bash
/plugin update-all
```

## Support

### Documentation

Each plugin has its own comprehensive documentation:
- [PRD Builder Documentation](./plugins/prd-builder/README.md)

### Issues

Report issues or request features:
- [GitHub Issues](https://github.com/tato/tato-claude-plugins/issues)

### Contributing

Contributions are welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines. *(Coming soon)*

## Roadmap

**Planned Plugins**:
- **Feature Roadmapper**: Strategic feature planning and prioritization
- **API Designer**: OpenAPI/REST API specification generator
- **Tech Stack Advisor**: Technology selection and architecture guidance
- **UI Component Library**: Reusable UI component generation

Want to suggest a plugin? [Open an issue](https://github.com/tato/tato-claude-plugins/issues/new)!

## License

This marketplace and all plugins are licensed under the [MIT License](./LICENSE).

Individual plugins may have additional licensing terms - see each plugin's directory for details.

## About

Created and maintained by [tato](https://github.com/tato).

Built for the [Claude Code](https://claude.com/code) community.

---

**Version**: 1.0.0
**Last Updated**: February 2026
