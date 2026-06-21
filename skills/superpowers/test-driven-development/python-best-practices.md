# Python Best Practices

**Load this reference when:** writing Python production code or tests.

## Type Annotations

**Always annotate function arguments and return types.**

<Good>
```python
def calculate_discount(price: float, percentage: float) -> float:
    return price * (percentage / 100)

def find_user(user_id: str) -> User | None:
    return db.users.get(user_id)

class OrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def create_order(self, customer_id: str, items: list[OrderItem]) -> Order:
        order = Order(customer_id=customer_id, items=items)
        return self._repository.save(order)

    def get_by_status(self, status: OrderStatus) -> list[Order]:
        return self._repository.find_by_status(status)
```
</Good>

<Bad>
```python
def calculate_discount(price, percentage):  # No types - unclear contract
    return price * (percentage / 100)

def find_user(user_id):  # Caller doesn't know return type
    return db.users.get(user_id)

class OrderService:
    def __init__(self, repository):  # What type is repository?
        self._repository = repository

    def create_order(self, customer_id, items):  # What does it return?
        order = Order(customer_id=customer_id, items=items)
        return self._repository.save(order)
```
</Bad>

**Why typing matters:**
- Documents function contracts explicitly
- Catches type errors before runtime (with mypy/pyright)
- Enables IDE autocomplete and refactoring
- Makes code self-documenting

**Guidelines:**
- Use `-> None` for methods with no meaningful return
- Use `X | None` (Python 3.10+) or `Optional[X]` for nullable returns
- Use `list[T]`, `dict[K, V]`, `set[T]` (Python 3.9+) instead of `List`, `Dict`, `Set`
- For complex types, create type aliases: `UserId = str`
- Annotate class attributes in `__init__` or as class variables

**Exceptions:**
- Test functions don't need return type annotations (always return `None`)
- Local variables usually don't need annotations (type inference handles them)

## Design Patterns

**Apply design patterns during the REFACTOR phase of TDD — never speculatively.**

When you observe structural code smells after tests are green, consult the `design-patterns` skill for pattern selection guidance and the accompanying `design-patterns-python.md` reference for idiomatic Python implementations.

**Common Python-specific pattern triggers:**

| Smell | Pattern | Python idiom |
|---|---|---|
| Growing `if/elif` selecting algorithm | Strategy | Use `Protocol` or plain callables |
| `if type == X: return X()` construction | Factory Method | Registry dict or ABC subclasses |
| Constructor with 5+ params | Builder | Fluent builder or `dataclass` with defaults |
| Subclass explosion from combining behaviors | Decorator | `functools.wraps` function decorators or class wrappers |
| Manual update calls after state change | Observer | Event manager with `Protocol` subscribers |
| Same `if state ==` in many methods | State | State classes with ABC |
| Duplicated method bodies differing in few lines | Template Method | ABC with `@abstractmethod` for variable steps |
| Need undo/queue for operations | Command | Command objects with `execute()`/`undo()` |
| Many nearly-identical objects in memory | Flyweight | `@dataclass(frozen=True)` shared instances |

**Rules:**
- Only apply a pattern when you have concrete evidence of a structural problem (a smell, not a hunch)
- Prefer Python-native solutions: callables over Strategy classes, generators over Iterator classes, modules over Singletons
- One concrete implementation does not need a factory — wait for the second variant
- See `design-patterns` skill for the full decision framework and all 23 GoF patterns
