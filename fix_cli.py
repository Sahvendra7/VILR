with open('scripts/cli.py', 'r') as f:
    content = f.read()

content = content.replace("import fakeredis.aioredis", "import fakeredis")
content = content.replace("fakeredis.aioredis.FakeRedis()", "fakeredis.FakeAsyncRedis()")

with open('scripts/cli.py', 'w') as f:
    f.write(content)
