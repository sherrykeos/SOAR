from app.models.adapter import ModelCapability
from app.models.mock import MockModel
from app.models.registry import ModelRegistry


print("[TEST] Starting ModelRegistry test suite...\n")

# 1. Initialize registry
registry = ModelRegistry()
assert len(registry.list_models()) == 0
print("1. Initialized empty ModelRegistry successfully.")

# 2. Register Mock models
print("\n2. Registering mock models...")
mock_general = MockModel(
    model_id="mock-qwen",
    provider="mock",
    capabilities={ModelCapability.GENERAL, ModelCapability.REASONING},
    priority=10,
)
mock_coder = MockModel(
    model_id="mock-coder",
    provider="mock",
    capabilities={ModelCapability.CODING},
    priority=20,
)
registry.register(mock_general)
registry.register(mock_coder)
print("Registered mock-qwen and mock-coder successfully.")

# 3. List models
print("\n3. Testing model listing...")
models = registry.list_models()
assert len(models) == 2
model_ids = [m.model_id for m in models]
assert "mock-qwen" in model_ids and "mock-coder" in model_ids
print(f"Listed models: {model_ids}")

# 4. Retrieve model by ID
print("\n4. Testing model retrieval by ID...")
retrieved = registry.get("mock-qwen")
assert retrieved.model_id == "mock-qwen"
assert retrieved.provider == "mock"
assert ModelCapability.REASONING in retrieved.capabilities
print(f"Retrieved model: {retrieved.model_id}")

# 5. Duplicate registration handling
print("\n5. Testing duplicate model registration handling...")
try:
    registry.register(mock_general)
    assert False, "Should have raised ValueError on duplicate model_id"
except ValueError as e:
    print(f"Caught expected ValueError: {e}")

# 6. Unknown model handling
print("\n6. Testing unknown model retrieval...")
try:
    registry.get("non_existent_model")
    assert False, "Should have raised KeyError on unknown model_id"
except KeyError as e:
    print(f"Caught expected KeyError: {e}")

# 7. Find models by capability & priority sorting
print("\n7. Testing find_by_capability with priority sorting...")
mock_slow_coder = MockModel(
    model_id="mock-slow-coder",
    provider="mock",
    capabilities={ModelCapability.CODING},
    priority=50,  # lower priority than mock-coder (20)
)
registry.register(mock_slow_coder)

coders = registry.find_by_capability(ModelCapability.CODING)
assert len(coders) == 2
assert coders[0].model_id == "mock-coder"  # priority 20 comes before 50
assert coders[1].model_id == "mock-slow-coder"
print(f"Coding models ordered by priority: {[m.model_id for m in coders]}")

print("\n[TEST] All ModelRegistry tests completed successfully!")
