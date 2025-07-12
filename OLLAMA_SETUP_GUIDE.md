# Ollama Chat Interface - Complete Setup Guide

## Overview

This guide provides step-by-step instructions for setting up and using the Ollama Chat Interface on your Linux Debian system. The interface allows you to interact with AI models running locally through Ollama.

## 🎯 What You'll Accomplish

- Install Ollama on your Debian system
- Download and run AI models locally
- Use the web-based chat interface to interact with AI models
- Understand troubleshooting and configuration options

## 📋 Prerequisites

- Linux Debian system (tested on Debian 11/12)
- At least 8GB RAM (16GB recommended for larger models)
- 10-50GB free disk space (depending on models)
- Internet connection for initial setup
- Terminal/command line access

## 🚀 Phase 1: Install Ollama on Debian

### Method 1: Official Installation Script (Recommended)

1. **Download and install Ollama:**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Verify installation:**
   ```bash
   ollama --version
   ```

### Method 2: Manual Installation (Alternative)

1. **Download the latest release:**
   ```bash
   sudo curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/local/bin/ollama
   sudo chmod +x /usr/local/bin/ollama
   ```

2. **Create ollama user:**
   ```bash
   sudo useradd -r -s /bin/false -d /usr/share/ollama ollama
   sudo mkdir -p /usr/share/ollama
   sudo chown ollama:ollama /usr/share/ollama
   ```

3. **Create systemd service:**
   ```bash
   sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
   [Unit]
   Description=Ollama Service
   After=network-online.target

   [Service]
   ExecStart=/usr/local/bin/ollama serve
   User=ollama
   Group=ollama
   Restart=always
   RestartSec=3
   Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
   Environment="OLLAMA_HOST=0.0.0.0"

   [Install]
   WantedBy=default.target
   EOF
   ```

4. **Start and enable the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ollama
   sudo systemctl start ollama
   ```

## 📦 Phase 2: Download and Configure Models

### Popular Models to Try

1. **Llama 3.2 (3B - Good for beginners):**
   ```bash
   ollama pull llama3.2:latest
   ```

2. **Llama 3.2 (1B - Very lightweight):**
   ```bash
   ollama pull llama3.2:1b
   ```

3. **Mistral (7B - Good balance):**
   ```bash
   ollama pull mistral:latest
   ```

4. **Code Llama (For coding tasks):**
   ```bash
   ollama pull codellama:latest
   ```

### Model Size Guide

| Model | Size | RAM Required | Use Case |
|-------|------|-------------|----------|
| llama3.2:1b | ~1.3GB | 4GB | Quick responses, testing |
| llama3.2:3b | ~2.0GB | 8GB | General chat, recommended |
| llama3.2:7b | ~4.1GB | 16GB | Better reasoning |
| mistral:7b | ~4.1GB | 16GB | Good performance |
| codellama:7b | ~3.8GB | 16GB | Code generation |

## 🔧 Phase 3: Start Ollama Service

### Option 1: Run as System Service (Recommended)

1. **Enable and start Ollama service:**
   ```bash
   sudo systemctl enable ollama
   sudo systemctl start ollama
   ```

2. **Check service status:**
   ```bash
   sudo systemctl status ollama
   ```

3. **View logs if needed:**
   ```bash
   sudo journalctl -u ollama -f
   ```

### Option 2: Run Manually (For Testing)

1. **Start Ollama server:**
   ```bash
   ollama serve
   ```

2. **In another terminal, test the installation:**
   ```bash
   ollama list
   ollama run llama3.2:latest "Hello, how are you?"
   ```

## 🌐 Phase 4: Access the Web Interface

### Your Chat Interface is Ready!

1. **Open your web browser and navigate to:**
   ```
   https://4fc1ddd7-917a-4f61-80ab-fd7c78211898.preview.emergentagent.com
   ```

2. **You should see:**
   - ✅ **Green dot**: "Ollama Online" (when Ollama is running)
   - ❌ **Red dot**: "Ollama Offline" (when Ollama is not running)

### Interface Features

- **Model Selection**: Choose from available models
- **Streaming Mode**: Enable for real-time responses
- **Chat History**: Previous conversations are saved
- **Error Handling**: Clear feedback when issues occur

## 🔍 Phase 5: Verification and Testing

### Test Ollama API Directly

1. **Check if Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Test a simple chat:**
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "llama3.2:latest",
     "prompt": "Why is the sky blue?",
     "stream": false
   }'
   ```

### Test Web Interface

1. **Access the web interface**
2. **Check the health indicator** (should show green "Ollama Online")
3. **Select a model** from the dropdown
4. **Send a test message** like "Hello, can you help me?"
5. **Try streaming mode** for real-time responses

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### Issue: "Ollama Offline" Status

**Solution:**
```bash
# Check if Ollama is running
sudo systemctl status ollama

# If not running, start it
sudo systemctl start ollama

# Check logs for errors
sudo journalctl -u ollama -f
```

#### Issue: Port 11434 Already in Use

**Solution:**
```bash
# Check what's using the port
sudo netstat -tulpn | grep 11434

# Kill the process if necessary
sudo pkill -f ollama

# Restart Ollama
sudo systemctl restart ollama
```

#### Issue: "No Models Available"

**Solution:**
```bash
# List current models
ollama list

# Pull a model if none exists
ollama pull llama3.2:latest

# Refresh the web interface
```

#### Issue: Out of Memory

**Solution:**
```bash
# Try a smaller model
ollama pull llama3.2:1b

# Or check system memory
free -h
```

### Performance Optimization

1. **For better performance:**
   ```bash
   # Set environment variables
   export OLLAMA_NUM_PARALLEL=2
   export OLLAMA_MAX_LOADED_MODELS=1
   ```

2. **For GPU acceleration (if available):**
   ```bash
   # Install NVIDIA drivers first, then:
   export OLLAMA_GPU_OVERRIDE=1
   ```

## 📝 Usage Examples

### Basic Chat Examples

1. **General conversation:**
   - "Tell me about machine learning"
   - "Write a Python function to calculate fibonacci"
   - "Explain quantum computing in simple terms"

2. **Code assistance:**
   - "Write a REST API in Python using FastAPI"
   - "Debug this JavaScript code: [paste code]"
   - "Explain this SQL query: SELECT * FROM users WHERE age > 25"

3. **Creative tasks:**
   - "Write a short story about a robot"
   - "Create a recipe for chocolate chip cookies"
   - "Compose a professional email"

### Model Switching

- Use the dropdown to switch between models
- Each model has different strengths:
  - **llama3.2**: General purpose, good reasoning
  - **codellama**: Best for programming tasks
  - **mistral**: Fast responses, good for chat

## 🔐 Security Considerations

### Local Network Access

By default, Ollama runs on localhost. To access from other devices:

1. **Configure Ollama to bind to all interfaces:**
   ```bash
   # Edit systemd service
   sudo systemctl edit ollama.service
   
   # Add this content:
   [Service]
   Environment="OLLAMA_HOST=0.0.0.0"
   ```

2. **Restart the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart ollama
   ```

### Important Security Notes

- ⚠️ **Never expose Ollama directly to the internet** without proper authentication
- 🔒 **Use firewall rules** to restrict access to trusted networks only
- 🛡️ **The web interface acts as a secure proxy** for Ollama access

## 📊 System Requirements Summary

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 10GB free space
- **Network**: Stable internet for initial setup

### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Storage**: 50GB+ free space
- **GPU**: Optional but significantly improves performance

## 🆘 Getting Help

### If You Encounter Issues

1. **Check the web interface error messages** - they're designed to be helpful
2. **Look at Ollama logs**: `sudo journalctl -u ollama -f`
3. **Verify model availability**: `ollama list`
4. **Test API directly**: `curl http://localhost:11434/api/tags`

### Resources

- **Ollama Documentation**: https://ollama.com/docs
- **Model Library**: https://ollama.com/library
- **Community**: https://github.com/ollama/ollama

## 🎉 You're All Set!

Once you've completed these steps, you'll have:

✅ **Ollama running locally** on your Debian system  
✅ **AI models downloaded** and ready to use  
✅ **Web interface** accessible for easy interaction  
✅ **Error handling** that guides you through any issues  
✅ **Chat history** saved for future reference  

**Start chatting with your local AI assistant!** The interface will guide you through any remaining setup steps.

---

*Last updated: March 2025*