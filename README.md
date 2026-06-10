# ComfyUI Prompt Enhance API with Image

A ComfyUI custom node that enhances and rewrites prompts using OpenAI-compatible APIs or native Ollama API. Supports optional image input for vision-enabled models like GPT-4 Vision and Llama 3.2 Vision.

## Features

- **Dual API Support**: Choose between OpenAI-compatible mode or native Ollama API mode
- **Prompt Enhancement**: Send prompts to an API for enhancement and rewriting
- **Optional Image Input**: Support for vision-enabled models that can analyze images
- **Flexible Configuration**: Configure API endpoint, model, and parameters via config file
- **System Prompts**: Customize the behavior with system prompts
- **OpenAI Compatible**: Works with OpenAI API, Azure OpenAI, local models (LM Studio), and other compatible endpoints
- **Ollama Native API**: Full access to Ollama-specific features including `keep_alive` control for immediate model unloading

## Installation

### Manual Installation

1. Navigate to your ComfyUI custom_nodes directory:
   ```bash
   cd /path/to/ComfyUI/custom_nodes
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/comfyui-prompt-enhance-api-with-image.git
   ```

3. Install dependencies

4. Restart ComfyUI

## Configuration

Create a `config.ini` file in the node directory (same folder as this README). You can configure both OpenAI-compatible and Ollama native API modes.

See [config.example.ini](config.example.ini) for a complete template.

### OpenAI-Compatible Mode

For OpenAI, Azure OpenAI, LM Studio, and other OpenAI-compatible endpoints:

```ini
[openai]
# Your API key (required for most services)
api_key = sk-your-api-key-here

# API endpoint
api_endpoint = https://api.openai.com/v1/chat/completions

# Model parameters (optional)
temperature = 0.7
max_tokens = 2000
top_p = 1.0
```

**Alternative OpenAI-Compatible Endpoints:**

- **Azure OpenAI**: `https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2024-02-01`
- **LM Studio**: `http://localhost:1234/v1/chat/completions`
- **Ollama (OpenAI-compatible)**: `http://localhost:11434/v1/chat/completions` (limited features)

### Ollama Native API Mode

For full Ollama features including `keep_alive` control:

```ini
[ollama]
# Ollama native API endpoint
api_endpoint = http://localhost:11434/api/chat

# Model parameters
temperature = 0.7
top_p = 1.0
top_k = 40
num_predict = 2000

# Context window size (higher uses more VRAM but allows longer inputs/outputs)
num_ctx = 4096

# keep_alive controls model memory management
# "0" = unload immediately (frees VRAM right away)
# "5m" = keep loaded for 5 minutes
# "-1" = keep loaded indefinitely
keep_alive = 0
```

**Important**: The native Ollama mode (`api_mode = "ollama"`) uses the `/api/chat` endpoint and provides full access to Ollama-specific parameters. Use this when you need to control `keep_alive` to manage VRAM usage.

## Usage

### Inputs

**Required:**
- **api_mode** (DROPDOWN): Choose the API mode
  - Options: "openai" (default) or "ollama"
  - **openai**: Uses OpenAI-compatible API format (works with OpenAI, Azure, LM Studio, etc.)
  - **ollama**: Uses native Ollama API with full access to Ollama-specific parameters like `keep_alive`

- **system_prompt** (STRING): The system message that sets the context for the AI
  - Default: "You are a helpful assistant that enhances and rewrites prompts to be more detailed and effective."
  - Multiline text input

- **user_prompt** (STRING): The prompt you want to enhance
  - Multiline text input

- **model** (STRING): The model name to use
  - Default: "gpt-4o"
  - OpenAI examples: "gpt-4o", "gpt-4-vision-preview", "gpt-3.5-turbo"
  - Ollama examples: "llama3.2-vision", "llama3.2", "mistral", "gemma2"

- **seed** (INT): Random seed for caching control
  - Default: 0
  - Range: 0 to 18446744073709551615
  - **Important**: ComfyUI caches node results based on inputs. When the seed value stays the same, ComfyUI uses the cached result without calling the API. Change the seed to force a new API call.

**Optional:**
- **image** (IMAGE): An optional image for vision-enabled models
  - Connect from any image-generating node
  - If provided, the model can analyze the image along with the text

### Output

- **enhanced_prompt** (STRING): The enhanced/rewritten prompt returned by the API

### Example Workflow

1. Add the "Prompt Enhance API (with Image)" node to your workflow
2. Select the API mode: "openai" or "ollama"
3. (Optional) Connect an image source to the image input
4. Enter your system prompt (or use the default)
5. Enter the prompt you want to enhance
6. Set the model name (e.g., "gpt-4o" for OpenAI, "llama3.2-vision" for Ollama)
7. Set the seed value (change it when you want a new API call)
8. Connect the output to wherever you need the enhanced prompt

### Understanding Seed and Caching

ComfyUI automatically caches node outputs based on their inputs. This means:

- **Same inputs = Cached result**: If you run the workflow again with identical inputs (including seed), no API call is made and the previous result is returned instantly. This saves API costs and time.
- **Different inputs = New execution**: Changing any input (prompt, model, image, or seed) triggers a new API call.

**Use the seed parameter to control when API calls happen:**

- **Keep seed the same**: Reuse the cached enhanced prompt without spending API credits
- **Increment seed**: Force a new API call to get a fresh enhancement (e.g., change from 0 to 1, then 2, etc.)
- **Random seed**: Connect a random number generator to get new results every run

**Tip**: You can connect a "Seed Generator" node or use ComfyUI's built-in random seed nodes to the seed input for automatic variation on each queue.

### Example Use Cases

#### Basic Prompt Enhancement
```
System Prompt: "You are a helpful assistant that enhances and rewrites prompts to be more detailed and effective."
User Prompt: "a beautiful landscape"
Output: "A breathtaking landscape featuring rolling hills under a golden sunset, with vibrant wildflowers in the foreground..."
```

#### Image-Based Prompt Enhancement
```
System Prompt: "Analyze the provided image and create a detailed prompt that describes it accurately."
User Prompt: "Describe this image in detail"
Image: [connected from an image node]
Output: "A serene mountain landscape with snow-capped peaks reflecting in a crystal-clear alpine lake..."
```

#### Style Transfer Prompts
```
System Prompt: "You are an expert at creating Stable Diffusion prompts. Rewrite the user's prompt with appropriate style tags and quality modifiers."
User Prompt: "portrait of a woman"
Output: "professional portrait of a young woman, detailed face, photorealistic, 8k uhd, high quality, cinematic lighting..."
```

#### Using Ollama with Immediate Model Unloading
```
API Mode: ollama
Model: llama3.2-vision
Config keep_alive: 0

This configuration ensures the Ollama model is unloaded from VRAM immediately after generating the response, freeing up memory for other tasks. This is especially useful when running multiple models or when VRAM is limited.
```

## Ollama Native API vs OpenAI-Compatible Mode

When using Ollama, you have two options:

| Feature | OpenAI-Compatible Mode | Ollama Native Mode |
|---------|------------------------|-------------------|
| Endpoint | `/v1/chat/completions` | `/api/chat` |
| api_mode setting | `openai` | `ollama` |
| keep_alive control | ❌ Not available | ✅ Full control (0, 5m, 1h, etc.) |
| Context window (num_ctx) | ❌ Not available | ✅ Configurable |
| Ollama-specific params | ❌ Not available | ✅ top_k, num_predict, etc. |
| Use when | You want compatibility | You need keep_alive or Ollama features |

**Recommendation**: Use `api_mode = "ollama"` when running Ollama locally to get full control over model lifecycle and memory management.

## Troubleshooting

### "API key not configured" Error
- Make sure you've created `config.ini` in the node directory
- Verify your API key is correctly set under `[openai]` section
- **Note**: Ollama mode doesn't require an API key

### Image Not Being Processed
- **OpenAI mode**: Ensure you're using a vision-enabled model (e.g., "gpt-4o", "gpt-4-vision-preview")
- **Ollama mode**: Use a vision-enabled model (e.g., "llama3.2-vision", "llava")
- Check that the image is properly connected to the image input

### Connection Errors
- Verify the `api_endpoint` is correct in your config
- Check your internet connection (for cloud APIs)
- For Ollama:
  - Ensure Ollama is running (`ollama serve` or system service)
  - Check if the model is installed (`ollama list`)
  - Try accessing http://localhost:11434 in your browser
- For LM Studio: Ensure the server is running and the API is enabled

### Ollama Model Not Unloading (VRAM stays full)
- Set `api_mode` to `"ollama"` (not `"openai"`)
- In `config.ini` under `[ollama]`, set `keep_alive = 0`
- Verify you're using the native endpoint: `http://localhost:11434/api/chat` (not `/v1/chat/completions`)
- Check the console output - it should show `[Ollama] keep_alive: 0, num_ctx: 4096`

### Rate Limiting
- OpenAI APIs have rate limits depending on your plan
- Consider adding delays between requests in your workflow
- Check the error message for specific rate limit details
- Ollama (local) has no rate limits

### Error Handling
- **Errors raise exceptions** and appear in ComfyUI's error console (not as text output)
- The failed node will be highlighted in red in the workflow
- Check the ComfyUI console/terminal for detailed error messages
- Errors prevent text from being passed to downstream nodes, stopping execution properly

## Requirements

- Python 3.8+
- ComfyUI
- requests
- Pillow
- numpy
- torch
