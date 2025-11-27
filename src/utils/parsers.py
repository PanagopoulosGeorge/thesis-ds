import re

def extract_prolog_snippets(response: str):
    main_match = re.findall(r'```prolog(.*?)```', response, re.DOTALL)
    alternative_match = re.findall(r'```(.*?)```', response, re.DOTALL)
    return "\n".join(main_match) if main_match else "\n".join(alternative_match)
