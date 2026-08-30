with open("adapters/razorpay/provider.py", "r") as f:
    content = f.read()

content = content.replace(
    "self.injected_network_failure: bool = False",
    "self.injected_network_failure: bool = False\n        self.call_count = 0"
)

content = content.replace(
    "async def execute_payment(self, request: ExecutionRequest) -> ExecutionReceipt:",
    "async def execute_payment(self, request: ExecutionRequest) -> ExecutionReceipt:\n        self.call_count += 1"
)

with open("adapters/razorpay/provider.py", "w") as f:
    f.write(content)
