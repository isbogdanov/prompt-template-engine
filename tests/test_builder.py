import os
import pytest
from builder import PromptBuilder


@pytest.fixture
def react_agent_builder():
    # Construct the path to the blueprint file, now located inside the builder package
    blueprint_path = os.path.join(
        "builder", "templates", "blueprints", "react_agent.bp.yaml"
    )
    return PromptBuilder(blueprint_path)


def test_generate_react_prompt_and_print(react_agent_builder):
    """
    Tests the generation of a ReAct prompt and prints it to the console.
    This is not a traditional test with assertions, but rather a way to
    visually inspect the generated prompt using `pytest -s`.
    """
    # Define runtime arguments, like conversation history or other dynamic data
    runtime_kwargs = {
        "history": "User: What was the score of the last Real Madrid game?\nAI: I'm sorry, I don't have real-time access to sports scores.",
        "question": "What is the capital of France?",
    }

    # Build the prompt
    final_prompt = react_agent_builder.build(**runtime_kwargs)

    # Print the final prompt to the console
    print("\n--- Generated ReAct Prompt ---")
    print(final_prompt)
    print("--- End of Prompt ---")

    # We'll add a simple assertion to make it a valid test
    assert final_prompt is not None
    assert "Tool Name: search" in final_prompt
    assert "User: What was the score of the last Real Madrid game?" in final_prompt
