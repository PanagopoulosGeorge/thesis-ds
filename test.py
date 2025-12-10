from src.prompts.factory import get_prompt_builder

builder = get_prompt_builder("msa")
request = builder.build_prompt("Generate gap rules")
print(request)