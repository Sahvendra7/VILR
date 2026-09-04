with open("scripts/cli.py", "r") as f:
    text = f.read()

text = text.replace("from tests.utils import ScenarioGenerator", "from simulator.scenarios import ScenarioGenerator")
text = text.replace("from tests.utils import MOCK_MERCHANT_KEY", "from simulator.scenarios import MOCK_MERCHANT_KEY")

with open("scripts/cli.py", "w") as f:
    f.write(text)
