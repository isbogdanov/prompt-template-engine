# Copyright 2025 Igor Bogdanov
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
import os

from .loader import load_template
from .exceptions import MissingPlaceholderError, TemplateNotFoundError


class PromptBuilder:
    def __init__(self, agent_definition_path: str):
        self.agent_template: Dict[str, Any] = load_template(agent_definition_path)
        self.agent_type: str = self.agent_template.get("agent_type", "default")

        # The templates are now located inside the 'builder' package,
        # so we construct the path relative to this file.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        instruction_path = os.path.join(
            current_dir,
            "templates",
            "instructions",
            f"{self.agent_type.lower()}.inst.yaml",
        )
        self.instruction_template: Dict[str, Any] = load_template(instruction_path)

    def build(self, **runtime_kwargs) -> str:
        build_method = getattr(
            self, f"_build_{self.agent_type.lower()}_prompt", self._build_default_prompt
        )
        return build_method(**runtime_kwargs)

    def _build_react_prompt(self, **runtime_kwargs) -> str:
        parts = []

        # 1. Preamble (Role + Instructions + Answer Format)
        preamble_parts = []
        preamble_parts.append(self.agent_template.get("system_message", ""))
        mode_of_operation = self.instruction_template.get("instructions", "")
        mode_of_operation += "\nIMPORTANT: The XML-like tags in this prompt are for context and structure. DO NOT include them in your response."
        preamble_parts.append(mode_of_operation)
        answer_format = self.agent_template.get("answer_format")
        if answer_format:
            preamble_parts.append(
                f"YOU MUST PROVIDE FINAL ANSWER IN SPECIFIC FORMAT SHOWN BELOW:\n{answer_format}"
            )
        parts.append("\n\n".join(preamble_parts))

        # 2. History (if provided)
        if "history" in runtime_kwargs:
            parts.append(runtime_kwargs["history"])

        # 4. Tools
        tools = self.agent_template.get("tools", [])

        # Conditionally add tools based on 'include_tool_*' flags
        for key, value in list(self.agent_template.items()):
            if key.startswith("include_tool_") and value:
                tool_name = key.replace("include_tool_", "")
                tool_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "templates",
                    "tools",
                    f"{tool_name}.tool.yaml",
                )
                try:
                    included_tool = load_template(tool_path)
                    tools.extend(included_tool)
                    # Check if the included tool has its own examples and merge them
                    if "examples" in included_tool[0]:
                        self.agent_template.setdefault("examples", []).extend(
                            included_tool[0]["examples"]
                        )
                except TemplateNotFoundError:
                    # You might want to log this as a warning or handle it as needed
                    print(
                        f"Warning: Tool definition not found for '{tool_name}' at {tool_path}"
                    )

        if tools:
            tool_strings = []
            for tool in tools:
                tool_str = f"<tool>\n{tool['name']}\ne.g. {tool['example_calling']}\n\n{tool['description']}"

                if tool.get("is_critical"):
                    answer_format = self.agent_template.get("answer_format", "")
                    tool_str += f"\n\n<loop_rules>This tool is critical. If you decide to call it, you must provide Answer immediately after calling this tool. After you receive the Observation from this tool, your ONLY next step is to output the final Answer.</loop_rules>"
                tool_strings.append(tool_str)
                tool_strings.append("</tool>\n")

            reflection_knowledge = self.agent_template.get("reflection_knowledge")
            intro_sentence = "Your available tools are in <tools_list>"
            if reflection_knowledge:
                intro_sentence += (
                    " and your guiding principles are in <reflection_knowledge>"
                )

            tools_section = (
                f"{intro_sentence}\n <tool_list>"
                + "\n".join(tool_strings)
                + "\nNo other actions are available to you."
            )
            parts.append(tools_section)
            parts.append("</tools_list>")

        # 2. Reflection Knowledge (if provided)
        reflection_knowledge = self.agent_template.get("reflection_knowledge")
        if reflection_knowledge:
            reflection_knowledge_str = ""
            if isinstance(reflection_knowledge, list):
                reflection_knowledge_str = "\n".join(
                    f"- {item}" for item in reflection_knowledge
                )
            else:
                reflection_knowledge_str = str(reflection_knowledge)

            enforcement_statement = (
                "CRITICAL: When using any tool, you MUST ground your reasoning in the following reflection knowledge. "
                "Your thought process must explicitly reference these principles."
            )
            reflection_section = f"\n\n<reflection_knowledge>\n{enforcement_statement}\n{reflection_knowledge_str.strip()}\n</reflection_knowledge>"
            parts.append(reflection_section)

        # 3. Rules
        rules = self.agent_template.get("rules", [])
        if rules:
            parts.append("CRITICAL RULES:\n" + "\n".join(f"- {rule}" for rule in rules))

        # 5. Examples
        examples = self.agent_template.get("examples", [])
        if examples:
            example_strings = []
            for i, example in enumerate(examples, 1):
                step_strings = [
                    f"--- Example {i}: {example.get('name', '')} ---",
                    f"Example Session: {example.get('description', '')}\n",
                ]
                steps = example.get("steps", [])
                for i, step in enumerate(steps):
                    if step["type"] == "thought":
                        step_strings.append(f"Thought: {step['content']}")
                    elif step["type"] == "tool_call":
                        tool_input = step.get("input")
                        if tool_input:
                            step_strings.append(f"Tool: {step['name']}: {tool_input}")
                        else:
                            step_strings.append(f"Tool: {step['name']}")
                        step_strings.append("PAUSE")
                        # Add the "You will be called again" part for all but the last step
                        if i < len(steps) - 1:
                            step_strings.append("\nYou will be called again with this:")
                    elif step["type"] == "observation":
                        step_strings.append(f"Observation: {step['content']}")
                    elif step["type"] == "answer":
                        # The thought preceding the answer is the last thought in the sequence
                        if step_strings and "Thought:" in step_strings[-1]:
                            # No need to add another thought if the last step was one
                            pass
                        step_strings.append("You then output:")
                        step_strings.append(f"Answer: {step['content']}")
                    elif step["type"] == "custom":
                        step_strings.append(step["content"])
                example_strings.append("\n".join(step_strings))
            parts.append("\n\n" + "\n\n".join(example_strings))

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
