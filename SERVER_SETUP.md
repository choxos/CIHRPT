# 🚀 CIHRPT Server Setup Guide

This guide explains how to easily start the CIHRPT development server with configurable ports and settings.

## 🎯 Quick Start

### Option 1: Super Easy (Recommended)
```bash
python start_server.py
```
This interactive script will:
- Create a `.env` file if it doesn't exist
- Show your current configuration
- Let you start the server or change settings

### Option 2: Direct Command
```bash
python manage.py runserver_env
```

### Option 3: Traditional Django Way
```bash
python manage.py runserver 8000
```

## ⚙️ Configuration

### Environment Variables (.env file)

Create a `.env` file in your project root:

```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,cihrpt.xeradb.com

# Server Configuration - Change these as needed!
PORT=8000
HOST=127.0.0.1

# Alternative ports you might want:
# PORT=8001  # For development instance 2
# PORT=8002  # For testing
# PORT=8080  # Common alternative
# PORT=3000  # If you prefer Node.js style
```

### Command Line Options

```bash
# Use custom port for this session only
python manage.py runserver_env --port 8001

# Use custom host
python manage.py runserver_env --host 0.0.0.0 --port 8080

# Show current configuration
python manage.py runserver_env --show-config
```

## 🔧 Common Use Cases

### Multiple Development Instances
```bash
# Terminal 1 - Main development
PORT=8000 python manage.py runserver_env

# Terminal 2 - Testing
PORT=8001 python manage.py runserver_env

# Terminal 3 - Experimental features
PORT=8002 python manage.py runserver_env
```

### Quick Port Changes
```bash
# Edit .env file
echo "PORT=8080" >> .env

# Or use command line override
python manage.py runserver_env --port 8080
```

### External Access (for testing on other devices)
```bash
# In .env file:
HOST=0.0.0.0
PORT=8000

# Or command line:
python manage.py runserver_env --host 0.0.0.0
```

## 💡 Pro Tips

1. **Never commit your `.env` file** - it's in `.gitignore` for security
2. **Use different ports for different purposes**:
   - `8000` - Main development
   - `8001` - Testing features
   - `8002` - Performance testing
   - `8080` - Demo/presentation
3. **Use the interactive script** (`python start_server.py`) when you're unsure
4. **Check configuration first** with `--show-config` flag

## 🛠️ Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000

# Kill Django servers on that port
pkill -f "runserver.*8000"

# Or use a different port
python manage.py runserver_env --port 8001
```

### Can't Connect to Server
1. Check if `HOST=127.0.0.1` (localhost only) or `HOST=0.0.0.0` (all interfaces)
2. Verify the port in your browser URL
3. Check firewall settings if accessing from other devices

### Environment Variables Not Loading
1. Ensure `.env` file exists in project root
2. Install `python-decouple`: `pip install python-decouple`
3. Check for typos in `.env` file (no spaces around `=`)

## 🎨 Benefits of This Setup

✅ **No more port confusion** - Set it once in `.env`  
✅ **Multiple dev instances** - Easy port management  
✅ **Team consistency** - Everyone uses same config format  
✅ **Production ready** - Same pattern works for deployment  
✅ **Secure** - Sensitive config stays out of git  

## 📁 File Structure
```
CIHRPT/
├── .env                 # Your local configuration (not in git)
├── start_server.py      # Interactive server starter
├── manage.py           # Django management
└── tracker/
    └── management/
        └── commands/
            └── runserver_env.py  # Custom server command
``` 