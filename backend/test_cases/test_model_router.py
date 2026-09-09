from app.models.adapter import ModelCapability
from app.models.mock import MockModel
from app.models.registry import ModelRegistry
from app.models.router import ModelRouter


print("[TEST] Starting ModelRouter test suite...\n")

# 1. Setup registry with specialized mock models
registry = ModelRegistry()

fast_general = MockModel(
    model_id="qwen-fast",
    provider="mock",
    capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
    priority=10,
    fixed_response="Fast reasoning plan generated.",
)
deep_coder = MockModel(
    model_id="qwen-coder",
    provider="mock",
    capabilities={ModelCapability.CODING},
    priority=20,
    fixed_response="def solve(): pass",
)

registry.register(fast_general)
registry.register(deep_coder)
print("1. Registered mock models into ModelRegistry.")

# 2. Initialize ModelRouter
router = ModelRouter(registry=registry, default_model_id="qwen-fast")
print("2. Initialized ModelRouter.")

# 3. Route general / reasoning task
print("\n3. Testing general and reasoning capability routing...")
general_model = router.route(task_type=ModelCapability.GENERAL)
assert general_model.model_id == "qwen-fast"
print(f"Routed 'general' task to: {general_model.model_id}")

reasoning_model = router.route(task_type=ModelCapability.REASONING)
assert reasoning_model.model_id == "qwen-fast"
print(f"Routed 'reasoning' task to: {reasoning_model.model_id}")

# 4. Route coding task
print("\n4. Testing coding capability routing...")
coding_model = router.route(task_type=ModelCapability.CODING)
assert coding_model.model_id == "qwen-coder"
print(f"Routed 'coding' task to: {coding_model.model_id}")

# 5. Route by exact ID
print("\n5. Testing explicit route by model_id...")
exact_model = router.route_by_id("qwen-coder")
assert exact_model.model_id == "qwen-coder"
print(f"Routed by ID to: {exact_model.model_id}")

# 6. Test unsupported capability handling
print("\n6. Testing unsupported capability handling...")
try:
    router.route(task_type=ModelCapability.VISION)
    assert False, "Should have raised ValueError for unsupported capability"
except ValueError as e:
    print(f"Caught expected ValueError: {e}")

# 7. Test generation through routed models
print("\n7. Testing text generation through routed models...")
res_reasoning = reasoning_model.generate("Plan task")
assert res_reasoning == "Fast reasoning plan generated."
res_coding = coding_model.generate("Write function")
assert res_coding == "def solve(): pass"
print("Generated responses successfully from routed models.")

print("\n[TEST] All ModelRouter tests completed successfully!")
