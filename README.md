# Prompt Template Engine - System Prompt Generator for Specific Techniques (COT, ReAct, few-shot etc)

## Overview

The `PromptEngine` is a standalone, "contract-driven" framework for constructing system prompts already optimized for specific prompting techniques.

## Core Architecture

1.  **Contracts (Blueprints)**: The engine provides official, commented YAML blueprints for different agent types (e.g., `react_agent.bp.yaml`). These live in `templates/blueprints/`.
2.  **Definitions (Implementations)**: Developers copy a blueprint and fill it with their agent's specific content (persona, rules, tools, examples). These definition files (e.g., `planner.yaml`) are the single source of truth for all prompt content.
3.  **Semantic Assembler**: The `PromptBuilder` class reads a definition file, understands its `agent_type`, and uses a corresponding internal method (e.g., `_build_react_prompt`) to correctly assemble the final prompt string.
4.  **Self-Correction Tools**: A suite of built-in tools (`raise_a_question`, `critique_the_answer`, `improve_based_on_critique`) enables agents to perform internal monologue and self-correction, leading to more robust reasoning.
5.  **Reflection Knowledge**: Developers can provide a set of guiding principles or "reflection knowledge" that the agent must use to ground its reasoning when using any tool.
6.  **Caching**: A caching loader ensures each template file is read from disk only once, preventing I/O bottlenecks.

## Usage Pattern

The intended usage follows three main steps:

### 1. Define Your Agent

1.  **Copy a Blueprint**: Find the appropriate blueprint in `templates/blueprints/` (e.g., `react_agent.bp.yaml`).
2.  **Create a Definition File**: Copy the blueprint to your project's `prompts/definitions/` directory and rename it (e.g., `my_agent.yaml`).
3.  **Fill the Blueprint**: Populate the YAML file with your agent's system message, rules, tools, and examples, following the structure of the contract.
4.  **(Optional) Add Reflection Knowledge**: To guide the agent's reasoning, you can add a `reflection_knowledge` section to your definition file. This can be a list of principles or a single string.

    ```yaml
    # in my_agent.yaml
    reflection_knowledge:
      - "Always prioritize user safety."
      - "Ensure responses are unbiased and neutral."
      - "When in doubt, ask a clarifying question."
    ```

### 2. Instantiate the `PromptBuilder`

In your application's startup or configuration code, create an instance of the builder, pointing it to your new definition file.

```python
from prompt_engine import PromptBuilder

my_agent_builder = PromptBuilder(
    agent_definition_path='prompts/definitions/my_agent.yaml'
)
```

### 3. Build the Prompt at Runtime

In your main application logic, call the builder's `.build()` method, passing any data that is only available at runtime (e.g., conversation history).

```python
# In your main application logic
history_string = get_recent_history()

final_prompt = my_agent_builder.build(history=history_string)
```

This pattern ensures a clean separation of concerns and produces a powerful, consistent, and maintainable prompt management system.
