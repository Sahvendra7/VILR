with open("app/domain/gateway.py", "r") as f:
    lines = f.readlines()
    
out = []
for line in lines:
    if line.strip() == ", UTC":
        continue
    out.append(line)
with open("app/domain/gateway.py", "w") as f:
    f.writelines(out)
