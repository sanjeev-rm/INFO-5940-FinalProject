"""
Base Agent Class

Provides common functionality for all AI agents in the hotel training system.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config.settings import AppConfig

class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self, config: AppConfig, model_preference: str = "default"):
        """
        Initialize base agent

        Args:
            config: Application configuration
            model_preference: Preferred model type (e.g., "fast", "smart", "balanced")
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_preference = model_preference

        # Get model configuration based on preference
        self.model_config = self._get_model_config()

    def _get_model_config(self) -> Dict[str, Any]:
        """Get model configuration based on preference"""
        model_configs = {
            "fast": {
                "model": self.config.FAST_MODEL,
                "max_tokens": 1500,
                "temperature": 0.7
            },
            "balanced": {
                "model": self.config.BALANCED_MODEL,
                "max_tokens": 3000,
                "temperature": 0.8
            },
            "smart": {
                "model": self.config.SMART_MODEL,
                "max_tokens": 5000,
                "temperature": 0.9
            },
            "default": {
                "model": self.config.DEFAULT_MODEL,
                "max_tokens": 3000,
                "temperature": 0.8
            }
        }

        return model_configs.get(self.model_preference, model_configs["default"])

    def _make_llm_request(self, messages: List[Dict[str, str]],
                         system_prompt: Optional[str] = None) -> str:
        """
        Make request to LLM API using OpenAI client

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt

        Returns:
            str: LLM response text
        """
        try:
            # Prepare messages for API
            api_messages = []

            # Add system prompt if provided
            if system_prompt:
                api_messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # Add conversation messages
            api_messages.extend(messages)

            # Initialize OpenAI client with Cornell endpoint
            client = OpenAI(
                api_key=self.config.LLM_API_KEY,
                base_url=self.config.LLM_API_URL
            )

            # Make API request
            response = client.chat.completions.create(
                model=self.model_config["model"],
                messages=api_messages,
                max_tokens=self.model_config["max_tokens"],
                temperature=self.model_config["temperature"]
            )

            # Extract response text
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                raise ValueError("No response from LLM API")

        except Exception as e:
            self.logger.error(f"API request error: {e}")
            return "I apologize, but I'm having trouble connecting to the AI service. Please try again."

    def _format_conversation_history(self, messages: List[Dict]) -> str:
        """
        Format conversation history for context

        Args:
            messages: List of conversation messages

        Returns:
            str: Formatted conversation history
        """
        formatted_history = []

        for msg in messages[-10:]:  # Last 10 messages for context
            role = "Guest" if msg["role"] == "guest" else "Agent"
            formatted_history.append(f"{role}: {msg['content']}")

        return "\n".join(formatted_history)

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass

    def validate_response(self, response: str) -> bool:
        """
        Validate agent response

        Args:
            response: Response to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Basic validation - can be overridden by subclasses
        return len(response.strip()) > 0 and len(response) < 2000