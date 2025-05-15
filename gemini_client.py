#!/usr/bin/env python3
"""Google Gemini client for the agent."""

import os
import json
import time
import random
import sys
import logging
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiDirectClient:
    """Use Google Gemini models via API."""

    def __init__(
        self,
        model_name="gemini-1.5-pro",
        max_retries=2,
        thinking_tokens=None,
        use_caching=False,
    ):
        """Initialize the Gemini client.

        Args:
            model_name: Name of the Gemini model to use (default: gemini-1.5-pro)
            max_retries: Maximum number of retries for API calls
            thinking_tokens: Not used for Gemini (included for compatibility)
            use_caching: Not used for Gemini (included for compatibility)
        """
        try:
            import google.generativeai as genai
        except ImportError:
            print("Error: google-generativeai package is not installed.")
            print("Please install it with: pip install google-generativeai>=0.3.0")
            sys.exit(1)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        # Configure the Gemini API
        genai.configure(api_key=api_key)

        self.model_name = model_name
        self.max_retries = max_retries
        self.debug = os.getenv("GEMINI_DEBUG", "0") == "1"
        self.genai = genai

        # Get the actual model
        try:
            self.model = genai.GenerativeModel(model_name)
            if self.debug:
                print(f"Successfully initialized Gemini model: {model_name}")

            # Check if function calling is available in this version by checking for methods
            self.supports_tools = hasattr(self.model, "generate_content_with_tools")
            if not self.supports_tools:
                logger.warning("This version of google-generativeai doesn't support tool calling. "
                               "Tool calls will be emulated through text. "
                               "Consider upgrading to the latest version.")

        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            raise

    def generate(
        self,
        messages,
        max_tokens: int,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        tools = [],
        tool_choice: dict[str, str] | None = None,
        thinking_tokens: int | None = None,
    ):
        """Generate responses using Gemini model."""
        # Import here to avoid circular imports
        from utils.llm_client import TextResult, ToolCall

        # Convert messages to Gemini format
        gemini_messages = []

        # Add system prompt if provided
        if system_prompt:
            system_content = {"role": "user", "parts": [{"text": f"SYSTEM: {system_prompt}"}]}
            gemini_messages.append(system_content)

        for idx, message_list in enumerate(messages):
            role = "user" if idx % 2 == 0 else "model"
            message_content = ""

            # Combine all content from this turn
            for message in message_list:
                # Use string type comparison to avoid circular imports
                if str(type(message).__name__) == "TextPrompt":
                    message_content += message.text
                elif str(type(message).__name__) == "TextResult":
                    message_content += message.text
                elif str(type(message).__name__) == "ToolCall":
                    # Format tool calls for Gemini
                    message_content += f"\nFunction Call: {message.tool_name}\n"
                    message_content += f"Function Arguments: {json.dumps(message.tool_input, indent=2)}\n"
                elif str(type(message).__name__) == "ToolFormattedResult":
                    # Format tool results for Gemini
                    message_content += f"\nFunction Result:\n{message.tool_output}\n"

            if message_content:
                gemini_messages.append({
                    "role": role,
                    "parts": [{"text": message_content}]
                })

        # Prepare tool information for textual instruction
        tool_instructions = ""
        if tools:
            tool_instructions = "\n\nYou have access to the following tools:\n"
            for tool in tools:
                tool_instructions += f"- {tool.name}: {tool.description}\n"
                tool_instructions += f"  Parameters: {json.dumps(tool.input_schema, indent=2)}\n\n"

            tool_instructions += "\nWhen you want to use a tool, respond with:\n"
            tool_instructions += "TOOL_CALL: <tool_name>\n"
            tool_instructions += "TOOL_PARAMETERS: <JSON parameters for the tool>\n"
            tool_instructions += "Make sure the parameters match exactly what the tool expects.\n"

        # Set up generation config
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "top_p": 1.0,
            "top_k": 32,
        }

        # Make API call with retries
        response = None
        for retry in range(self.max_retries):
            try:
                # Create a chat session
                chat = self.model.start_chat(history=[])

                # Send all messages to establish the conversation
                for message in gemini_messages[:-1]:  # All but the last message
                    if message["role"] == "user":
                        chat.send_message(message["parts"][0]["text"], stream=False)
                    elif message["role"] == "model":
                        # For model messages, we're just setting up history, no need to process response
                        pass

                # Send the last message and get the response
                last_message = gemini_messages[-1] if gemini_messages else {"role": "user", "parts": [{"text": "Hello"}]}

                # If we have tools, append the tool instructions to the last user message
                if tools and last_message["role"] == "user":
                    enhanced_message = last_message["parts"][0]["text"] + tool_instructions
                else:
                    enhanced_message = last_message["parts"][0]["text"]

                if last_message["role"] == "user":
                    response = chat.send_message(
                        enhanced_message,
                        generation_config=generation_config,
                        stream=False
                    )
                    break
                else:
                    # If the last message is from the model, we need to send a dummy message to get a response
                    response = chat.send_message(
                        "Please continue.",
                        generation_config=generation_config,
                        stream=False
                    )
                    break

            except Exception as e:
                if retry == self.max_retries - 1:
                    print(f"Failed Gemini request after {retry + 1} retries: {e}")
                    raise
                else:
                    print(f"Retrying Gemini request ({retry + 1}/{self.max_retries}): {e}")
                    time.sleep(2 * random.uniform(0.8, 1.2))  # Shorter wait times for Gemini

        # Convert response to expected format
        augment_messages = []

        if response:
            # Check for emulated tool calls in the response text
            response_text = response.text
            tool_call_match = False

            # Look for the tool call pattern in the response
            if "TOOL_CALL:" in response_text and "TOOL_PARAMETERS:" in response_text:
                tool_call_match = True
                lines = response_text.split("\n")
                tool_name = None
                tool_params_text = ""
                tool_params = {}
                collecting_params = False

                for line in lines:
                    if line.startswith("TOOL_CALL:"):
                        tool_name = line.replace("TOOL_CALL:", "").strip()
                    elif line.startswith("TOOL_PARAMETERS:"):
                        collecting_params = True
                        # Get everything after TOOL_PARAMETERS:
                        params_line = line.replace("TOOL_PARAMETERS:", "").strip()
                        if params_line:  # If there's content on the same line
                            tool_params_text = params_line
                    elif collecting_params and tool_params_text == "":
                        # We're collecting params and haven't found text yet
                        tool_params_text = line.strip()

                # Try to parse the parameters as JSON
                if tool_name and tool_params_text:
                    try:
                        tool_params = json.loads(tool_params_text)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try to find JSON in the text
                        # Look for opening brace to closing brace
                        import re
                        json_match = re.search(r'\{.*\}', tool_params_text, re.DOTALL)
                        if json_match:
                            try:
                                tool_params = json.loads(json_match.group(0))
                            except Exception:
                                # Still can't parse it, use a simple key-value format
                                tool_params = {"raw_input": tool_params_text}
                        else:
                            tool_params = {"raw_input": tool_params_text}

                if tool_name:
                    # Create a tool call
                    augment_messages.append(
                        ToolCall(
                            tool_call_id=f"gemini_tool_{random.randint(1000, 9999)}",
                            tool_name=tool_name,
                            tool_input=tool_params
                        )
                    )

                    if self.debug:
                        print(f"Detected emulated tool call: {tool_name} with input {tool_params}")

            # If no tool call was detected, return the text response
            if not tool_call_match:
                augment_messages.append(TextResult(text=response_text))
        else:
            # Fallback if we somehow get here without a response
            augment_messages.append(TextResult(text="I apologize, but I was unable to process your request."))

        # Create metadata
        message_metadata = {
            "raw_response": str(response),
            "input_tokens": -1,  # Gemini doesn't provide token counts in this API
            "output_tokens": -1,
        }

        return augment_messages, message_metadata


def get_gemini_client(model_name="gemini-1.5-pro", **kwargs):
    """Create a Gemini client."""
    return GeminiDirectClient(model_name=model_name, **kwargs)
