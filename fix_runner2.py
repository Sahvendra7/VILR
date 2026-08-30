with open("simulator/runner.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "transaction_id=exec_result.transaction_id" in line and "except Exception as e" in "".join(new_lines[-20:]):
        new_lines.append(line.replace("exec_result.transaction_id", '""'))
    elif "evidence=exec_result.evidence" in line and "except Exception as e" in "".join(new_lines[-20:]):
        new_lines.append(line.replace("exec_result.evidence", '""'))
    elif "actual=exec_result.outcome.value" in line and "except Exception as e" in "".join(new_lines[-20:]):
        new_lines.append(line.replace("exec_result.outcome.value", '"ERROR"'))
    elif "actual='ERROR'" in line:
        pass # remove it
    else:
        new_lines.append(line)

with open("simulator/runner.py", "w") as f:
    f.writelines(new_lines)
