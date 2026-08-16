import json
import base64
import io
import configparser
from pathlib import Path
import numpy as np
from PIL import Image
import torch
import requests


class PromptEnhanceAPINode:
    """
    A ComfyUI custom node that enhances prompts using OpenAI-compatible or Ollama native API.
    Supports optional image input for vision-enabled models.
    """

    def __init__(self):
        """Initialize the node and load configuration."""
        self.config = self._load_config()

    @classmethod
    def INPUT_TYPES(cls):
        """Define the input types for the node."""
        return {
            "required": {
                "api_mode": (["openai", "ollama"], {
                    "default": "openai"
                }),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "You are a helpful assistant that enhances and rewrites prompts to be more detailed and effective."
                }),
                "user_prompt": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "model": ("STRING", {
                    "default": "gpt-4o"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "step": 1
                }),
            },
            "optional": {
                "image": ("IMAGE",),
                "keep_alive": ("STRING", {
                    "default": "0"  # Ollama only: "0" unloads immediately, or "5m", "1h", "-1" for indefinitely
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("enhanced_prompt",)
    FUNCTION = "enhance_prompt"
    CATEGORY = "text/processing"

    def _load_config(self):
        """Load configuration from config.ini file."""
        config = configparser.ConfigParser()

        # Look for config in the same directory as this file
        config_path = Path(__file__).parent / "config.ini"

        # Default configuration for both modes
        default_config = {
            "openai": {
                "api_key": "",
                "api_endpoint": "https://api.openai.com/v1/chat/completions",
                "temperature": "0.7",
                "max_tokens": "2000",
                "top_p": "1.0"
            },
            "ollama": {
                "api_endpoint": "http://localhost:11434/api/chat",
                "temperature": "0.7",
                "top_p": "1.0",
                "top_k": "40",
                "num_predict": "2000",
                "num_ctx": "4096",
                "keep_alive": "0"  # Set to 0 to unload immediately, or "5m", "1h", etc.
            }
        }

        if config_path.exists():
            config.read(config_path)
            # Update OpenAI config if present
            if config.has_section("openai"):
                default_config["openai"].update(dict(config.items("openai")))
            # Update Ollama config if present
            if config.has_section("ollama"):
                default_config["ollama"].update(dict(config.items("ollama")))

        return default_config

    def _image_to_base64(self, image_tensor):
        """
        Convert ComfyUI image tensor to base64 string.

        ComfyUI images are in the format [batch, height, width, channels] with values in range [0, 1]
        """
        # Convert from torch tensor to numpy if needed
        if isinstance(image_tensor, torch.Tensor):
            image_np = image_tensor.cpu().numpy()
        else:
            image_np = image_tensor

        # Take the first image if batch
        if len(image_np.shape) == 4:
            image_np = image_np[0]

        # Convert from [0, 1] float to [0, 255] uint8
        image_np = (image_np * 255).astype(np.uint8)

        # Convert to PIL Image
        pil_image = Image.fromarray(image_np)

        # Convert to base64
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return img_base64

    def enhance_prompt(self, api_mode, system_prompt, user_prompt, model, seed, image=None, keep_alive=None):
        """
        Enhance the prompt using OpenAI-compatible or Ollama native API.

        Args:
            api_mode: API mode to use ("openai" or "ollama")
            system_prompt: System message to set the context
            user_prompt: User's prompt to enhance
            model: Model name to use (e.g., "gpt-4o", "llama3.2-vision")
            seed: Random seed for caching control (changing seed forces re-execution)
            image: Optional image tensor from ComfyUI
            keep_alive: Ollama only. How long to keep the model loaded ("0", "5m",
                "1h", "-1"). Overrides the config.ini value when provided.

        Returns:
            Tuple containing the enhanced prompt string
        """
        if not user_prompt.strip() and image is None:
            raise ValueError("User prompt is empty and no image provided. Nothing to enhance.")

        if api_mode == "ollama":
            return self._call_ollama_api(system_prompt, user_prompt, model, seed, image, keep_alive)
        else:
            return self._call_openai_api(system_prompt, user_prompt, model, seed, image)

    def _call_openai_api(self, system_prompt, user_prompt, model, seed, image=None):
        """Call OpenAI-compatible API."""
        # Get API configuration
        config = self.config.get("openai", {})
        api_key = config.get("api_key")
        api_endpoint = config.get("api_endpoint")

        if not api_key:
            error_msg = "API key not configured. Please set it in config.ini under [openai] section"
            print(f"Error: {error_msg}")
            raise ValueError(error_msg)

        # Build the messages array
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # Add user message with optional image
        if image is not None:
            # Convert image to base64
            image_base64 = self._image_to_base64(image)

            # Vision-enabled message format
            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        else:
            # Text-only message
            user_message = {
                "role": "user",
                "content": user_prompt
            }

        messages.append(user_message)

        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": float(config.get("temperature", 0.7)),
            "max_tokens": int(config.get("max_tokens", 2000)),
            "top_p": float(config.get("top_p", 1.0)),
            "seed": seed
        }

        try:
            # Send request to API
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=payload,
                timeout=int(config.get("timeout", 60))
            )

            response.raise_for_status()

            # Parse response
            response_data = response.json()
            try:
                enhanced_text = response_data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as e:
                raise RuntimeError(f"OpenAI API returned unexpected response structure: {response_data}") from e

            print(f"[OpenAI] Prompt enhanced successfully using model: {model}")
            return (enhanced_text,)

        except requests.exceptions.RequestException as e:
            error_msg = f"OpenAI API request failed: {str(e)}"

            # If there's a response, try to get more details
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f"\nDetails: {error_details}"
                except (ValueError, json.JSONDecodeError):
                    error_msg += f"\nResponse: {e.response.text}"

            print(f"Error: {error_msg}")
            raise RuntimeError(error_msg) from e

        except Exception as e:
            error_msg = f"OpenAI unexpected error: {str(e)}"
            print(f"Error: {error_msg}")
            raise RuntimeError(error_msg) from e

    def _call_ollama_api(self, system_prompt, user_prompt, model, seed, image=None, keep_alive=None):
        """Call Ollama native API."""
        # Get API configuration
        config = self.config.get("ollama", {})
        api_endpoint = config.get("api_endpoint", "http://localhost:11434/api/chat")

        # Build the messages array for Ollama
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # Add user message with optional image
        user_message = {
            "role": "user",
            "content": user_prompt
        }

        # Ollama uses an images array at the message level
        if image is not None:
            image_base64 = self._image_to_base64(image)
            user_message["images"] = [image_base64]

        messages.append(user_message)

        # Prepare the Ollama API request
        headers = {
            "Content-Type": "application/json"
        }

        # Parse keep_alive - can be a string like "5m" or a number.
        # The node input (if provided) takes precedence over config.ini.
        if keep_alive is None or str(keep_alive).strip() == "":
            keep_alive = config.get("keep_alive", "0")
        # Try to convert to int if it's a number string, otherwise keep as string
        try:
            keep_alive = int(keep_alive)
        except (ValueError, TypeError):
            pass  # Keep as string for formats like "5m", "1h", etc.

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": float(config.get("temperature", 0.7)),
                "top_p": float(config.get("top_p", 1.0)),
                "top_k": int(config.get("top_k", 40)),
                "num_predict": int(config.get("num_predict", 2000)),
                "num_ctx": int(config.get("num_ctx", 4096)),
                "seed": seed,
            },
            "keep_alive": keep_alive
        }

        try:
            # Send request to Ollama API
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=payload,
                timeout=int(config.get("timeout", 300))  # Ollama can be slow; configurable via [ollama] timeout
            )

            response.raise_for_status()

            # Parse response
            response_data = response.json()
            try:
                enhanced_text = response_data["message"]["content"]
            except (KeyError, TypeError) as e:
                raise RuntimeError(f"Ollama API returned unexpected response structure: {response_data}") from e

            print(f"[Ollama] Prompt enhanced successfully using model: {model}")
            print(f"[Ollama] keep_alive: {keep_alive}, num_ctx: {config.get('num_ctx', 4096)}")
            return (enhanced_text,)

        except requests.exceptions.RequestException as e:
            error_msg = f"Ollama API request failed: {str(e)}"

            # If there's a response, try to get more details
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f"\nDetails: {error_details}"
                except (ValueError, json.JSONDecodeError):
                    error_msg += f"\nResponse: {e.response.text}"

            print(f"Error: {error_msg}")
            raise RuntimeError(error_msg) from e

        except Exception as e:
            error_msg = f"Ollama unexpected error: {str(e)}"
            print(f"Error: {error_msg}")
            raise RuntimeError(error_msg) from e
