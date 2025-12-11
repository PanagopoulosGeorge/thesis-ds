OUTPUT_POLICY = """
OUTPUT POLICY FOR RTEC RULE GENERATION

When generating rules:

1. Output Format:
    - include each RTEC rule within ```prolog ``` block.

2. Syntax Constraints:
    - Do not invent new predicates or fluents.
    - Do not modify argument structures of existing predicates.

3. Rule Semantics:
    - If the activity is simple, use initiatedAt/terminatedAt rules.
    - If the activity is statically determined, use holdsFor rules only.
    - The first literal of initiatedAt must always be a positive happensAt literal.

4. Variable Safety:
    - Each variable must be used consistently throughout the rule.
    - A variable must not appear only once unless it is intentionally free.

6. Consistency:
    - Use the exact event and fluent names provided in the system knowledge.
    - When ambiguous, prefer the simplest correct rule.

7. Error Handling:
    - If the user description lacks initiation/termination conditions, reply:
      "Insufficient information: please specify the initiation and termination conditions."
""".strip()