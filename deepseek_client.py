"""DeepSeek LLM client implementation.

This file contains the implementation of the DeepSeek LLM client for use with the agent.
"""

import json
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, cast
import logging

# Import existing client classes and types
from utils.llm_client import (
    LLMClient,
    AnthropicRedactedThinkingBlock,
    AnthropicThinkingBlock,
    ToolCall,
    ToolFormattedResult,
    AssistantContentBlock,
    GeneralContentBlock,
    TextPrompt,
    TextResult,
    ToolParam,
    recursively_remove_invoke_tag,
    LLMMessages,
)

# DeepSeek imports - ensure these are installed
try:
    from openai import OpenAI as DeepSeekAPI
    from openai import RateLimitError, APIConnectionError, InternalServerError
except ImportError:
    print("The openai package is required. Please install it with 'pip install openai'")
    raise

logger = logging.getLogger(__name__)

class DeepSeekClient(LLMClient):
    """Use DeepSeek models via OpenAI-compatible API."""

    def __init__(
        self,
        model_name="deepseek-chat",
        max_retries=3,
        use_caching=False,
        thinking_tokens=0,
        api_base="https://api.deepseek.com/v1",
    ):
        """Initialize the DeepSeek client.

        Args:
            model_name: Model name to use (default "deepseek-chat")
            max_retries: Maximum number of retries (default 3)
            use_caching: Whether to use caching (default False)
            thinking_tokens: Number of thinking tokens (default 0)
            api_base: DeepSeek API base URL (default "https://api.deepseek.com/v1")
        """
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY environment variable is not set")

        # Initialize OpenAI client with DeepSeek base URL
        self.client = DeepSeekAPI(
            api_key=self.api_key,
            base_url=api_base,
            max_retries=1,
            timeout=60 * 5
        )

        self.model_name = model_name
        self.max_retries = max_retries
        self.use_caching = use_caching
        self.thinking_tokens = thinking_tokens

        logger.info(f"Initialized DeepSeekClient with model {model_name}")

    def generate(
        self,
        messages: LLMMessages,
        max_tokens: int = 8192,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        tools: list[ToolParam] = [],
        tool_choice: dict[str, str] | None = None,
        thinking_tokens: int | None = None,
    ) -> Tuple[list[AssistantContentBlock], dict[str, Any]]:
        """Generate responses.

        Args:
            messages: A list of messages.
            max_tokens: The maximum number of tokens to generate (default 8192).
            system_prompt: A system prompt.
            temperature: The temperature.
            tools: A list of tools.
            tool_choice: A tool choice.
            thinking_tokens: Number of thinking tokens to use.

        Returns:
            A tuple of (model_response, metadata).
        """
        # Convert messages to DeepSeek/OpenAI format
        openai_messages = []

        # Add system prompt if provided
        if system_prompt is not None:
            openai_messages.append({"role": "system", "content": system_prompt})

        # Track tool calls to ensure we have the right number of tool messages
        pending_tool_calls = {}  # {tool_call_id: tool_name}

        # Convert message lists to OpenAI format
        for idx, message_list in enumerate(messages):
            role = "user" if idx % 2 == 0 else "assistant"

            # Process user or assistant messages
            processed_messages = self._process_message_list(message_list, role, pending_tool_calls)
            openai_messages.extend(processed_messages)

        # Convert tools to OpenAI format
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            })

        # Convert tool_choice to OpenAI format
        if tool_choice is None:
            tool_choice_param = None
        elif tool_choice["type"] == "any":
            tool_choice_param = "auto"  # OpenAI doesn't have direct equivalent
        elif tool_choice["type"] == "auto":
            tool_choice_param = "auto"
        elif tool_choice["type"] == "tool":
            tool_choice_param = {
                "type": "function",
                "function": {"name": tool_choice["name"]}
            }
        else:
            tool_choice_param = None

        # Dump the final message sequence for debugging
        message_dump = json.dumps(openai_messages, indent=2, default=str)
        logger.debug(f"Final message sequence: {message_dump}")

        # Perform API call with retries
        response = None

        for retry in range(self.max_retries):
            try:
                # Log what we're sending to the API for debugging
                logger.debug(f"Sending to DeepSeek API: model={self.model_name}, messages={openai_messages}")

                kwargs = {
                    "model": self.model_name,
                    "messages": openai_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                # Only add tools if we have them
                if openai_tools:
                    kwargs["tools"] = openai_tools

                if tool_choice_param:
                    kwargs["tool_choice"] = tool_choice_param

                # Make the API call
                response = self.client.chat.completions.create(**kwargs)
                break

            except (APIConnectionError, InternalServerError, RateLimitError) as e:
                if retry == self.max_retries - 1:
                    logger.error(f"Failed DeepSeek request after {retry + 1} retries: {e}")
                    raise e
                else:
                    logger.warning(f"DeepSeek API error: {e}. Retrying ({retry + 1}/{self.max_retries})...")
                    # Sleep 4-6 seconds with jitter to avoid thundering herd
                    time.sleep(5 * random.uniform(0.8, 1.2))

        # Handle response
        if response is None:
            raise RuntimeError("Failed to get response from DeepSeek API")

        # Convert response to our format
        augment_messages = []

        # Extract message content and/or function calls
        message = response.choices[0].message

        if message.content:
            augment_messages.append(TextResult(text=message.content))

        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                try:
                    # Function calls come back as JSON strings, parse them
                    tool_input = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse tool arguments: {tool_call.function.arguments}")
                    tool_input = {"error": "Failed to parse arguments"}

                augment_messages.append(
                    ToolCall(
                        tool_call_id=tool_call.id,
                        tool_name=tool_call.function.name,
                        tool_input=tool_input,
                    )
                )

        # Create metadata
        metadata = {
            "raw_response": response,
            "input_tokens": response.usage.prompt_tokens if hasattr(response.usage, "prompt_tokens") else 0,
            "output_tokens": response.usage.completion_tokens if hasattr(response.usage, "completion_tokens") else 0,
        }

        return augment_messages, metadata

    def _process_message_list(self, message_list, role, pending_tool_calls):
        """Process a list of messages for a single turn.

        Args:
            message_list: List of GeneralContentBlock objects
            role: The role ("user" or "assistant")
            pending_tool_calls: Dict of {tool_call_id: tool_name} to track pending calls

        Returns:
            List of messages in OpenAI format
        """
        openai_messages = []

        # Handle multiple messages in a list
        text_parts = []
        tool_calls_in_turn = []
        tool_results_in_turn = []

        for message in message_list:
            if isinstance(message, TextPrompt) or isinstance(message, TextResult):
                # Text from the user or assistant
                if isinstance(message, TextPrompt):
                    text_parts.append(message.text)
                else:
                    text_parts.append(message.text)

            elif isinstance(message, ToolCall):
                # Track this tool call
                tool_calls_in_turn.append({
                    "id": message.tool_call_id,
                    "name": message.tool_name,
                    "arguments": message.tool_input,
                })
                # Add to pending calls
                pending_tool_calls[message.tool_call_id] = message.tool_name

            elif isinstance(message, ToolFormattedResult):
                # Tool results will be added as separate messages
                tool_results_in_turn.append({
                    "id": message.tool_call_id,
                    "name": pending_tool_calls.get(message.tool_call_id, "unknown_tool"),
                    "output": message.tool_output,
                })
                # Remove from pending calls
                if message.tool_call_id in pending_tool_calls:
                    del pending_tool_calls[message.tool_call_id]

        # Add accumulated text
        if text_parts:
            openai_messages.append({
                "role": role,
                "content": "\n".join(text_parts)
            })

        # Add tool calls (as assistant messages)
        if tool_calls_in_turn and role == "assistant":
            # Add assistant message with tool calls
            tool_calls_formatted = []
            for tc in tool_calls_in_turn:
                tool_calls_formatted.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"])
                    }
                })

            openai_messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls_formatted
            })

        # Add tool results (as tool messages)
        for tr in tool_results_in_turn:
            # Add tool message with result
            openai_messages.append({
                "role": "tool",
                "tool_call_id": tr["id"],
                "content": tr["output"]
            })

        return openai_messages


def get_deepseek_client(**kwargs) -> LLMClient:
    """Get a DeepSeek client with the specified parameters."""
    return DeepSeekClient(**kwargs)
