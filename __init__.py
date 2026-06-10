"""
ComfyUI Prompt Enhance API with Image

A custom node for ComfyUI that enhances prompts using OpenAI-compatible APIs
with optional image input for vision-enabled models.
"""

from .prompt_enhance_node import PromptEnhanceAPINode

NODE_CLASS_MAPPINGS = {
    "PromptEnhanceAPI": PromptEnhanceAPINode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptEnhanceAPI": "Prompt Enhance API (with Image)"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
