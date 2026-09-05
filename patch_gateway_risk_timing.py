import re
with open("app/domain/gateway.py", "r") as f:
    content = f.read()

# Add Risk timing around risk = DeterministicRiskCalculator().calculate_risk(risk_signals)
replacement1 = """            perf.start("risk_latency")
            risk = DeterministicRiskCalculator().calculate_risk(risk_signals)
            perf.stop("risk_latency")"""

content = content.replace("            risk = DeterministicRiskCalculator().calculate_risk(risk_signals)", replacement1)

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
