# Copyright 2024 Igor Bogdanov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re
from typing import Dict, Any, Set

from .loader import load_template
from .exceptions import MissingPlaceholderError


class PromptBuilder:
    def __init__(self, agent_definition_path: str):
        self.agent_template: Dict[str, Any] = load_template(agent_definition_path)
        self.agent_type: str = self.agent_template.get("agent_type", "default")

        instruction_path = f"templates/instructions/{self.agent_type.lower()}.inst.yaml"
        self.instruction_template: Dict[str, Any] = load_template(instruction_path)

    def build(self, **runtime_kwargs) -> str:
        build_method = getattr(
            self, f"_build_{self.agent_type.lower()}_prompt", self._build_default_prompt
        )
        return build_method(**runtime_kwargs)

    def _build_react_prompt(self, **runtime_kwargs) -> str:
        parts = []

        # 1. Preamble (Role + Instructions)
        preamble_parts = []
        preamble_parts.append(self.agent_template.get("system_message", ""))
        preamble_parts.append(self.instruction_template.get("instructions", ""))
        parts.append("\n\n".join(preamble_parts))

        # 2. History (if provided)
        if "history" in runtime_kwargs:
            parts.append(runtime_kwargs["history"])

        # 3. Rules
        rules = self.agent_template.get("rules", [])
        if rules:
            parts.append("CRITICAL RULES:\n" + "\n".join(f"- {rule}" for rule in rules))

        # 4. Tools
        tools = self.agent_template.get("tools", [])
        if tools:
            tool_strings = []
            for tool in tools:
                tool_str = f"Tool Name: {tool['name']}\nDescription: {tool['description']}\nExample: {tool['example_calling']}"
                tool_strings.append(tool_str)
            parts.append("TOOLS:\n" + "\n\n".join(tool_strings))

        # 5. Examples
        examples = self.agent_template.get("examples", [])
        if examples:
            example_strings = []
            for example in examples:
                step_strings = [f"--- Example: {example.get('name', '')} ---"]
                steps = example.get("steps", [])
                for i, step in enumerate(steps):
                    if step["type"] == "thought":
                        step_strings.append(f"Thought: {step['content']}")
                    elif step["type"] == "tool_call":
                        step_strings.append(f"Tool: {step['name']}: {step['input']}")
                    elif step["type"] == "observation":
                        step_strings.append(f"Observation: {step['content']}")
                    elif step["type"] == "answer":
                        step_strings.append(f"Answer: {step['content']}")
                    elif step["type"] == "custom":
                        step_strings.append(step["content"])
                example_strings.append("\n".join(step_strings))
            parts.append("EXAMPLES:\n" + "\n\n".join(example_strings))

        return "\n\n".join(parts).strip()

    def _build_cot_prompt(self, **runtime_kwargs) -> str:
        # Implementation for Chain of Thought prompts would go here
        pass

    def _build_few_shot_prompt(self, **runtime_kwargs) -> str:
        # This is a generic builder for few-shot prompts. It assembles parts
        # provided at runtime, without any internal conditional logic.
        parts = []
        parts.append(self.agent_template.get("system_message", ""))

        rules = self.agent_template.get("rules", [])
        if rules:
            parts.append("CRITICAL RULES:\n" + "\n".join(f"- {rule}" for rule in rules))

        # The calling code is responsible for constructing and passing these parts
        if "response_format_rules" in runtime_kwargs:
            parts.append(runtime_kwargs["response_format_rules"])

        if "valid_actions_list" in runtime_kwargs:
            parts.append(runtime_kwargs["valid_actions_list"])

        if "example" in runtime_kwargs:
            parts.append(runtime_kwargs["example"])

        return "\n\n".join(parts)

    def _build_default_prompt(self, **runtime_kwargs) -> str:
        # A fallback for basic string substitution if no type matches
        raw_string = self.agent_template.get("system_message", "")
