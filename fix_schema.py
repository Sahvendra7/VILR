import re
with open("app/semantic/provider.py", "r") as f:
    text = f.read()

schema_dict = """                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "status": {"type": "STRING", "enum": ["PASS", "REVIEW", "FAIL"]},
                        "confidence": {"type": "NUMBER"},
                        "checks": {"type": "OBJECT"},
                        "violations": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "type": {"type": "STRING"},
                                    "severity": {"type": "STRING", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                                    "evidence": {"type": "STRING"}
                                },
                                "required": ["type", "severity", "evidence"]
                            }
                        },
                        "reasoning": {"type": "STRING"}
                    },
                    "required": ["status", "confidence", "checks", "violations", "reasoning"]
                },"""

text = text.replace("response_schema=SemanticAssessment,", schema_dict)

with open("app/semantic/provider.py", "w") as f:
    f.write(text)
