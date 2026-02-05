# Scripts

Collection of automation scripts for daily workflows.

## organize_with_ai.sh

AI-powered file organizer using local Ollama models.

### Features

- Scans directories and analyzes file structure
- Generates organization suggestions using LLM
- Interactive approval for each move
- Never deletes files
- Creates executable script of approved moves

### Requirements

- [Ollama](https://ollama.ai/) installed and running
- Model: `qwen2.5:14b-instruct-q5_K_M` (configurable in script)

### Usage

```bash
./organize_with_ai.sh /path/to/directory [max_files] [depth]
```

| Param | Default | Description |
|-------|---------|-------------|
| `max_files` | 0 (no limit) | Maximum files to analyze |
| `depth` | 0 (no limit) | Directory depth levels |

**Examples:**
```bash
./organize_with_ai.sh ~/Descargas           # All files, all depth
./organize_with_ai.sh ~/Documentos 500      # Max 500 files
./organize_with_ai.sh ~/projects 0 3        # All files, max 3 levels
```

### Workflow

```
┌─────────────────┐
│  1. Scan Dir    │ → Collects files (configurable limits)
└────────┬────────┘
         ▼
┌─────────────────┐
│  2. AI Analysis │ → Ollama generates suggestions (background)
└────────┬────────┘
         ▼
┌─────────────────┐
│  3. Overview    │ → Shows current state + suggested structure
└────────┬────────┘
         ▼
┌─────────────────┐
│  4. Review      │ → Approve/reject each move [s/n/q]
└────────┬────────┘
         ▼
┌─────────────────┐
│  5. Execute     │ → Run approved moves (optional)
└─────────────────┘
```

### Output Files

All reports saved to `~/.organize_reports/`:

| File | Description |
|------|-------------|
| `report_TIMESTAMP.md` | Full AI analysis |
| `suggestions_TIMESTAMP.csv` | Extracted move suggestions |
| `approved_TIMESTAMP.sh` | Script with approved moves |

### Safety

- **No deletions**: Only suggests moves
- **No auto-execute**: Every move requires approval
- **Reversible**: Approved script can be reviewed before running
- **Logged**: All suggestions and decisions saved

### Configuration

Edit the script header to change:

```bash
MODEL="qwen2.5:14b-instruct-q5_K_M"  # Ollama model
```

## Author

**Alberto Jiménez** - [GitHub](https://github.com/albertjimrod)
