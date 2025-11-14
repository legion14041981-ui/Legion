# Legion Examples

This directory contains example scripts demonstrating various features and use cases of the Legion framework.

## 📋 Available Examples

### 1. basic_usage.py

**What it demonstrates:**
- Creating and configuring Legion agents
- Registering agents with LegionCore coordinator
- Using the logging system
- Agent lifecycle management (start/stop)
- Monitoring agent status
- Basic error handling

**How to run:**
```bash
cd examples
python basic_usage.py
```

**Expected output:**
- Logs showing agent creation
- Agent registration confirmation
- Status updates as agents start and stop
- Clean shutdown messages

**No dependencies required** - works with base Legion installation.

---

### 2. supabase_integration.py

**What it demonstrates:**
- Connecting to Supabase database
- Creating agents with database storage
- Managing tasks in the database
- Using TaskQueue with Supabase backend
- Working with Edge Functions (indirectly)
- Environment variable configuration
- Comprehensive error handling

**Prerequisites:**
1. Supabase account and project
2. Environment variables configured (see below)
3. Database tables created (see main README.md)

**Setup:**

Create a `.env` file in the project root:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

**How to run:**
```bash
cd examples
python supabase_integration.py
```

**Expected output:**
- Database connection confirmation
- Agent creation and registration logs
- Task creation confirmations
- Queue processing statistics
- Final status report

---

## 🔧 Environment Setup

### For basic_usage.py
No special setup required. Just install Legion:
```bash
pip install -r ../requirements.txt
```

### For supabase_integration.py
1. Install Legion with all dependencies
2. Set up Supabase project
3. Create `.env` file with credentials
4. Ensure database tables exist:
   - `agents` table
   - `tasks` table

See the main [README.md](../README.md) for detailed database schema.

---

## 📝 Creating Your Own Examples

When creating new examples:

1. **Add proper documentation** at the top of the file
2. **Include error handling** for robustness
3. **Use the logging system** for output
4. **Make it self-contained** where possible
5. **Add environment checks** for required dependencies

Example template:
```python
\"\"\"
Brief description of what this example demonstrates.
\"\"\"

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from legion import setup_logging

async def main():
    logger = setup_logging("ExampleName", "INFO")
    logger.info("Starting example...")
    
    # Your code here
    
    logger.info("Example completed!")

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
```

---

## 🚀 Next Steps

After trying these examples:

1. **Modify them** - Change agent configurations, add new capabilities
2. **Combine concepts** - Create agents that use both local and Supabase storage
3. **Build something new** - Use these as templates for your own projects
4. **Check the docs** - See the main README for API documentation

---

## ❓ Troubleshooting

### Import errors
Make sure you're running from the examples directory and Legion is installed:
```bash
pip install -e ..
```

### Supabase connection fails
- Check your `.env` file exists and has correct values
- Verify your Supabase project is active
- Ensure your API key has the right permissions

### Database errors
- Make sure tables are created (see main README)
- Check your Supabase project has the Edge Functions deployed
- Verify Row Level Security (RLS) settings if applicable

---

## 📚 Additional Resources

- [Main README](../README.md) - Full Legion documentation
- [Supabase Documentation](https://supabase.com/docs)
- [Python AsyncIO Guide](https://docs.python.org/3/library/asyncio.html)

---

**Have questions or found issues?** Open an issue on GitHub or contact the maintainers!
