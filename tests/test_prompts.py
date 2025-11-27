from langchain_core.prompts import SystemMessagePromptTemplate

from src.prompts.rtec_base import (
    basic_system_messages,
    example_system_messages,
    build_rtec_prompt,
)


def test_build_rtec_prompt_default_counts():
    prompt = build_rtec_prompt()
    messages = prompt.format_messages()

    assert len(messages) == len(basic_system_messages) + len(example_system_messages)
    assert "Run-Time Event Calculus" in messages[0].content
    assert ("static" in messages[-1].content) and ("fluent" in messages[-1].content)


def test_build_rtec_prompt_toggle_definitions():
    prompt_without_simple = build_rtec_prompt(include_simple_fluent_definition=False)
    messages_without_simple = prompt_without_simple.format_messages()
    assert len(messages_without_simple) == len(basic_system_messages) + len(example_system_messages) - 1

    prompt_minimal = build_rtec_prompt(
        include_simple_fluent_definition=False,
        include_static_fluent_definition=False,
    )
    minimal_messages = prompt_minimal.format_messages()
    assert len(minimal_messages) == len(basic_system_messages)

def test_build_rtec_prompt_accepts_additional_messages():
    extra = SystemMessagePromptTemplate.from_template("Custom domain constraints.")
    prompt = build_rtec_prompt(
        include_simple_fluent_definition=False,
        include_static_fluent_definition=False,
        additional_messages=[extra],
    )

    messages = prompt.format_messages()
    assert messages[-1].content == "Custom domain constraints."
    assert len(messages) == len(basic_system_messages) + 1

