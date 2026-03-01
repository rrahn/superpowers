# Design Patterns in Python — Implementation Reference

Idiomatic Python implementations of all 23 Gang of Four design patterns.
Baseline: [refactoring.guru/design-patterns/python](https://refactoring.guru/design-patterns/python), adapted for modern Python (3.10+).

**Conventions used throughout:**
- `abc.ABC` / `@abstractmethod` for interfaces where enforcement is needed
- `typing.Protocol` for structural (duck-typed) interfaces where flexibility is preferred
- `dataclasses` where appropriate to reduce boilerplate
- Python-native constructs (`__iter__`, `__next__`, decorators, `copy.deepcopy`) over manual plumbing
- Type hints on all public signatures

---

## Creational Patterns

### Factory Method

```python
from abc import ABC, abstractmethod


class Notification(ABC):
    """Product interface."""

    @abstractmethod
    def send(self, message: str) -> None: ...


class EmailNotification(Notification):
    def send(self, message: str) -> None:
        print(f"Email: {message}")


class SMSNotification(Notification):
    def send(self, message: str) -> None:
        print(f"SMS: {message}")


class PushNotification(Notification):
    def send(self, message: str) -> None:
        print(f"Push: {message}")


class NotificationService(ABC):
    """Creator — declares the factory method."""

    @abstractmethod
    def create_notification(self) -> Notification: ...

    def notify(self, message: str) -> None:
        """Template that uses the factory method."""
        notification = self.create_notification()
        notification.send(message)


class EmailService(NotificationService):
    def create_notification(self) -> Notification:
        return EmailNotification()


class SMSService(NotificationService):
    def create_notification(self) -> Notification:
        return SMSNotification()


# Usage
service: NotificationService = EmailService()
service.notify("Your order shipped")
```

**Pythonic alternative** — when you don't need a full class hierarchy, use a registry dict:

```python
_REGISTRY: dict[str, type[Notification]] = {
    "email": EmailNotification,
    "sms": SMSNotification,
    "push": PushNotification,
}


def create_notification(channel: str) -> Notification:
    cls = _REGISTRY.get(channel)
    if cls is None:
        raise ValueError(f"Unknown channel: {channel}")
    return cls()
```

---

### Abstract Factory

```python
from abc import ABC, abstractmethod


# --- Product interfaces ---
class Button(ABC):
    @abstractmethod
    def render(self) -> str: ...


class Checkbox(ABC):
    @abstractmethod
    def render(self) -> str: ...


# --- Concrete products: Light theme ---
class LightButton(Button):
    def render(self) -> str:
        return "<button class='light'>OK</button>"


class LightCheckbox(Checkbox):
    def render(self) -> str:
        return "<input type='checkbox' class='light'/>"


# --- Concrete products: Dark theme ---
class DarkButton(Button):
    def render(self) -> str:
        return "<button class='dark'>OK</button>"


class DarkCheckbox(Checkbox):
    def render(self) -> str:
        return "<input type='checkbox' class='dark'/>"


# --- Factory interface ---
class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button: ...

    @abstractmethod
    def create_checkbox(self) -> Checkbox: ...


class LightThemeFactory(UIFactory):
    def create_button(self) -> Button:
        return LightButton()

    def create_checkbox(self) -> Checkbox:
        return LightCheckbox()


class DarkThemeFactory(UIFactory):
    def create_button(self) -> Button:
        return DarkButton()

    def create_checkbox(self) -> Checkbox:
        return DarkCheckbox()


# --- Client code works with the factory interface, not concrete classes ---
def build_ui(factory: UIFactory) -> None:
    button = factory.create_button()
    checkbox = factory.create_checkbox()
    print(button.render(), checkbox.render())


build_ui(DarkThemeFactory())
```

---

### Builder

```python
from dataclasses import dataclass, field


@dataclass
class HTTPRequest:
    method: str = "GET"
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: str | None = None
    timeout: int = 30
    retries: int = 0


class HTTPRequestBuilder:
    """Fluent builder for HTTPRequest with clear step-by-step construction."""

    def __init__(self, method: str, url: str) -> None:
        self._method = method
        self._url = url
        self._headers: dict[str, str] = {}
        self._body: str | None = None
        self._timeout: int = 30
        self._retries: int = 0

    def header(self, key: str, value: str) -> "HTTPRequestBuilder":
        self._headers[key] = value
        return self

    def body(self, content: str) -> "HTTPRequestBuilder":
        self._body = content
        return self

    def timeout(self, seconds: int) -> "HTTPRequestBuilder":
        self._timeout = seconds
        return self

    def retries(self, count: int) -> "HTTPRequestBuilder":
        self._retries = count
        return self

    def build(self) -> HTTPRequest:
        return HTTPRequest(
            method=self._method,
            url=self._url,
            headers=self._headers,
            body=self._body,
            timeout=self._timeout,
            retries=self._retries,
        )


# Usage — reads like a specification
request = (
    HTTPRequestBuilder("POST", "https://api.example.com/users")
    .header("Content-Type", "application/json")
    .header("Authorization", "Bearer token123")
    .body('{"name": "Alice"}')
    .timeout(10)
    .retries(3)
    .build()
)
```

---

### Prototype

```python
import copy
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    host: str
    port: int
    options: dict[str, str] = field(default_factory=dict)

    def clone(self) -> "DatabaseConfig":
        """Deep copy — nested mutables are independent."""
        return copy.deepcopy(self)


# Usage
production = DatabaseConfig("db.prod.internal", 5432, {"ssl": "require"})
staging = production.clone()
staging.host = "db.staging.internal"
staging.options["ssl"] = "prefer"

assert production.options["ssl"] == "require"  # Original unchanged
```

---

### Singleton

**Thread-safe Singleton via metaclass:**

```python
import threading


class SingletonMeta(type):
    _instances: dict[type, object] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]


class AppConfig(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.settings: dict[str, str] = {}


# Usage
c1 = AppConfig()
c2 = AppConfig()
assert c1 is c2
```

**Preferred alternative — module-level instance (Pythonic singleton):**

```python
# config.py
class _AppConfig:
    def __init__(self) -> None:
        self.settings: dict[str, str] = {}

app_config = _AppConfig()  # Module-level singleton, import this
```

**Best alternative — dependency injection (no singleton needed):**

```python
# Pass the config explicitly. Easier to test, no global state.
def process_data(config: AppConfig, data: list) -> None: ...
```

---

## Structural Patterns

### Adapter

```python
from typing import Protocol


class JSONSerializer(Protocol):
    """Target interface our application expects."""

    def to_json(self, data: dict) -> str: ...


class XMLLibrary:
    """Adaptee — legacy library with incompatible interface."""

    def convert_to_xml(self, data: dict) -> str:
        entries = "".join(f"<{k}>{v}</{k}>" for k, v in data.items())
        return f"<root>{entries}</root>"


class XMLToJSONAdapter:
    """Adapter — wraps XMLLibrary to satisfy JSONSerializer protocol."""

    def __init__(self, xml_lib: XMLLibrary) -> None:
        self._xml_lib = xml_lib

    def to_json(self, data: dict) -> str:
        import json
        # Adapter translates the call; here we just serialize as JSON
        # but log that we could have used XML
        _ = self._xml_lib.convert_to_xml(data)  # Legacy side-effect
        return json.dumps(data)


# Client code depends only on the Protocol, not the concrete class
def export_data(serializer: JSONSerializer, data: dict) -> str:
    return serializer.to_json(data)


adapter = XMLToJSONAdapter(XMLLibrary())
result = export_data(adapter, {"name": "Alice", "role": "admin"})
```

---

### Bridge

```python
from abc import ABC, abstractmethod


# --- Implementation hierarchy ---
class Renderer(ABC):
    @abstractmethod
    def render_circle(self, x: float, y: float, radius: float) -> str: ...

    @abstractmethod
    def render_rect(self, x: float, y: float, w: float, h: float) -> str: ...


class SVGRenderer(Renderer):
    def render_circle(self, x: float, y: float, radius: float) -> str:
        return f'<circle cx="{x}" cy="{y}" r="{radius}"/>'

    def render_rect(self, x: float, y: float, w: float, h: float) -> str:
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>'


class CanvasRenderer(Renderer):
    def render_circle(self, x: float, y: float, radius: float) -> str:
        return f"ctx.arc({x}, {y}, {radius}, 0, 2*Math.PI)"

    def render_rect(self, x: float, y: float, w: float, h: float) -> str:
        return f"ctx.fillRect({x}, {y}, {w}, {h})"


# --- Abstraction hierarchy (varies independently) ---
class Shape(ABC):
    def __init__(self, renderer: Renderer) -> None:
        self._renderer = renderer

    @abstractmethod
    def draw(self) -> str: ...


class Circle(Shape):
    def __init__(self, renderer: Renderer, x: float, y: float, radius: float) -> None:
        super().__init__(renderer)
        self.x, self.y, self.radius = x, y, radius

    def draw(self) -> str:
        return self._renderer.render_circle(self.x, self.y, self.radius)


class Rectangle(Shape):
    def __init__(self, renderer: Renderer, x: float, y: float, w: float, h: float) -> None:
        super().__init__(renderer)
        self.x, self.y, self.w, self.h = x, y, w, h

    def draw(self) -> str:
        return self._renderer.render_rect(self.x, self.y, self.w, self.h)


# Shapes × Renderers without class explosion
circle = Circle(SVGRenderer(), 10, 20, 5)
print(circle.draw())  # <circle cx="10" cy="20" r="5"/>
```

---

### Composite

```python
from abc import ABC, abstractmethod


class FileSystemEntry(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def size(self) -> int: ...

    @abstractmethod
    def display(self, indent: int = 0) -> str: ...


class File(FileSystemEntry):
    def __init__(self, name: str, size_bytes: int) -> None:
        super().__init__(name)
        self._size = size_bytes

    def size(self) -> int:
        return self._size

    def display(self, indent: int = 0) -> str:
        return f"{'  ' * indent}{self.name} ({self._size}B)"


class Directory(FileSystemEntry):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._children: list[FileSystemEntry] = []

    def add(self, entry: FileSystemEntry) -> None:
        self._children.append(entry)

    def size(self) -> int:
        return sum(child.size() for child in self._children)

    def display(self, indent: int = 0) -> str:
        lines = [f"{'  ' * indent}{self.name}/"]
        for child in self._children:
            lines.append(child.display(indent + 1))
        return "\n".join(lines)


# Usage — uniform interface for files and directories
root = Directory("src")
root.add(File("main.py", 1200))
lib = Directory("lib")
lib.add(File("utils.py", 800))
lib.add(File("models.py", 2400))
root.add(lib)

print(root.display())
print(f"Total: {root.size()}B")
```

---

### Decorator

```python
from abc import ABC, abstractmethod


class DataSource(ABC):
    @abstractmethod
    def write(self, data: str) -> None: ...

    @abstractmethod
    def read(self) -> str: ...


class FileDataSource(DataSource):
    def __init__(self, filename: str) -> None:
        self._filename = filename
        self._data = ""

    def write(self, data: str) -> None:
        self._data = data
        print(f"Writing to {self._filename}: {data[:50]}...")

    def read(self) -> str:
        return self._data


class DataSourceDecorator(DataSource, ABC):
    """Base decorator — delegates to wrapped component."""

    def __init__(self, source: DataSource) -> None:
        self._wrapped = source

    def write(self, data: str) -> None:
        self._wrapped.write(data)

    def read(self) -> str:
        return self._wrapped.read()


class CompressionDecorator(DataSourceDecorator):
    def write(self, data: str) -> None:
        compressed = f"[compressed]{data}[/compressed]"
        super().write(compressed)

    def read(self) -> str:
        raw = super().read()
        return raw.replace("[compressed]", "").replace("[/compressed]", "")


class EncryptionDecorator(DataSourceDecorator):
    def write(self, data: str) -> None:
        encrypted = f"[encrypted]{data}[/encrypted]"
        super().write(encrypted)

    def read(self) -> str:
        raw = super().read()
        return raw.replace("[encrypted]", "").replace("[/encrypted]", "")


# Stack decorators — order matters
source = EncryptionDecorator(CompressionDecorator(FileDataSource("data.txt")))
source.write("sensitive payload")
print(source.read())  # "sensitive payload"
```

**Pythonic alternative — function decorators for simpler cases:**

```python
import functools
import time
from typing import Callable, TypeVar
from typing import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


def retry(max_attempts: int = 3) -> Callable:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_attempts:
                        raise
                    time.sleep(2 ** attempt)
            raise RuntimeError("Unreachable")
        return wrapper
    return decorator


def log_calls(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result!r}")
        return result
    return wrapper


@retry(max_attempts=3)
@log_calls
def fetch_data(url: str) -> str:
    return f"data from {url}"
```

---

### Facade

```python
class VideoCodec:
    def decode(self, filename: str) -> bytes:
        return b"raw_video_data"


class AudioCodec:
    def decode(self, filename: str) -> bytes:
        return b"raw_audio_data"


class VideoMixer:
    def mix(self, video: bytes, audio: bytes) -> bytes:
        return video + audio


class FileWriter:
    def write(self, filename: str, data: bytes) -> None:
        print(f"Writing {len(data)} bytes to {filename}")


class VideoConverter:
    """Facade — single entry point to the complex video subsystem."""

    def __init__(self) -> None:
        self._video_codec = VideoCodec()
        self._audio_codec = AudioCodec()
        self._mixer = VideoMixer()
        self._writer = FileWriter()

    def convert(self, input_file: str, output_file: str) -> None:
        video = self._video_codec.decode(input_file)
        audio = self._audio_codec.decode(input_file)
        mixed = self._mixer.mix(video, audio)
        self._writer.write(output_file, mixed)


# Client code — one call instead of four
converter = VideoConverter()
converter.convert("input.avi", "output.mp4")
```

---

### Flyweight

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TreeType:
    """Flyweight — shared intrinsic state."""
    name: str
    color: str
    texture: str


class TreeTypeFactory:
    _cache: dict[tuple, TreeType] = {}

    @classmethod
    def get(cls, name: str, color: str, texture: str) -> TreeType:
        key = (name, color, texture)
        if key not in cls._cache:
            cls._cache[key] = TreeType(name, color, texture)
        return cls._cache[key]


@dataclass
class Tree:
    """Context — unique extrinsic state + shared flyweight."""
    x: float
    y: float
    tree_type: TreeType

    def draw(self) -> str:
        return f"{self.tree_type.name} at ({self.x}, {self.y})"


# 1 million trees, but only a handful of TreeType objects in memory
forest = [
    Tree(i * 0.1, i * 0.2, TreeTypeFactory.get("Oak", "green", "rough"))
    for i in range(1_000_000)
]
print(f"Trees: {len(forest)}, Unique types: {len(TreeTypeFactory._cache)}")
```

---

### Proxy

```python
from abc import ABC, abstractmethod


class Database(ABC):
    @abstractmethod
    def query(self, sql: str) -> list[dict]: ...


class RealDatabase(Database):
    def __init__(self, connection_string: str) -> None:
        self._conn = connection_string
        print(f"Connected to {connection_string}")

    def query(self, sql: str) -> list[dict]:
        print(f"Executing: {sql}")
        return [{"id": 1, "name": "Alice"}]


class CachingDatabaseProxy(Database):
    """Smart proxy — adds caching and lazy initialization."""

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string
        self._db: RealDatabase | None = None
        self._cache: dict[str, list[dict]] = {}

    def _get_db(self) -> RealDatabase:
        if self._db is None:
            self._db = RealDatabase(self._connection_string)
        return self._db

    def query(self, sql: str) -> list[dict]:
        if sql in self._cache:
            print(f"Cache hit: {sql}")
            return self._cache[sql]
        result = self._get_db().query(sql)
        self._cache[sql] = result
        return result


# Client uses the same interface — doesn't know about caching or lazy init
db: Database = CachingDatabaseProxy("postgres://localhost/mydb")
db.query("SELECT * FROM users")  # Connects + executes
db.query("SELECT * FROM users")  # Cache hit
```

---

## Behavioral Patterns

### Strategy

```python
from typing import Protocol


class PricingStrategy(Protocol):
    """Strategy interface using Protocol for structural typing."""

    def calculate(self, base_price: float) -> float: ...


class RegularPricing:
    def calculate(self, base_price: float) -> float:
        return base_price


class PremiumDiscount:
    def __init__(self, discount_pct: float = 0.2) -> None:
        self._discount = discount_pct

    def calculate(self, base_price: float) -> float:
        return base_price * (1 - self._discount)


class HappyHourPricing:
    def calculate(self, base_price: float) -> float:
        return base_price * 0.5


class Order:
    def __init__(self, items: list[float], pricing: PricingStrategy) -> None:
        self._items = items
        self._pricing = pricing

    @property
    def pricing(self) -> PricingStrategy:
        return self._pricing

    @pricing.setter
    def pricing(self, strategy: PricingStrategy) -> None:
        self._pricing = strategy

    def total(self) -> float:
        return sum(self._pricing.calculate(p) for p in self._items)


# Swap strategies at runtime
order = Order([100.0, 50.0, 75.0], RegularPricing())
print(f"Regular: ${order.total():.2f}")

order.pricing = PremiumDiscount(0.15)
print(f"Premium: ${order.total():.2f}")

order.pricing = HappyHourPricing()
print(f"Happy Hour: ${order.total():.2f}")
```

**Pythonic alternative — callables as strategies:**

```python
from typing import Callable

PricingFn = Callable[[float], float]


def regular(price: float) -> float:
    return price


def premium(discount: float = 0.2) -> PricingFn:
    return lambda price: price * (1 - discount)


def calculate_total(items: list[float], pricing: PricingFn) -> float:
    return sum(pricing(p) for p in items)


print(calculate_total([100, 50, 75], regular))
print(calculate_total([100, 50, 75], premium(0.15)))
```

---

### Observer

```python
from typing import Protocol, Any


class Subscriber(Protocol):
    def update(self, event: str, data: Any) -> None: ...


class EventManager:
    """Subject / Publisher — manages subscriptions and notifications."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Subscriber]] = {}

    def subscribe(self, event: str, listener: Subscriber) -> None:
        self._listeners.setdefault(event, []).append(listener)

    def unsubscribe(self, event: str, listener: Subscriber) -> None:
        self._listeners.get(event, []).remove(listener)

    def notify(self, event: str, data: Any = None) -> None:
        for listener in self._listeners.get(event, []):
            listener.update(event, data)


class LoggingListener:
    def __init__(self, log_file: str) -> None:
        self._log_file = log_file

    def update(self, event: str, data: Any) -> None:
        print(f"[LOG → {self._log_file}] {event}: {data}")


class AlertListener:
    def __init__(self, email: str) -> None:
        self._email = email

    def update(self, event: str, data: Any) -> None:
        print(f"[ALERT → {self._email}] {event}: {data}")


class Editor:
    def __init__(self) -> None:
        self.events = EventManager()
        self._content = ""

    def open_file(self, path: str) -> None:
        self._content = f"content of {path}"
        self.events.notify("open", path)

    def save(self) -> None:
        self.events.notify("save", self._content)


# Wire up observers
editor = Editor()
editor.events.subscribe("open", LoggingListener("editor.log"))
editor.events.subscribe("save", AlertListener("admin@example.com"))
editor.events.subscribe("save", LoggingListener("editor.log"))

editor.open_file("README.md")
editor.save()
```

---

### Command

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class Command(ABC):
    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...


class TextEditor:
    def __init__(self) -> None:
        self.content = ""

    def insert(self, text: str, position: int) -> None:
        self.content = self.content[:position] + text + self.content[position:]

    def delete(self, position: int, length: int) -> str:
        deleted = self.content[position:position + length]
        self.content = self.content[:position] + self.content[position + length:]
        return deleted


class InsertCommand(Command):
    def __init__(self, editor: TextEditor, text: str, position: int) -> None:
        self._editor = editor
        self._text = text
        self._position = position

    def execute(self) -> None:
        self._editor.insert(self._text, self._position)

    def undo(self) -> None:
        self._editor.delete(self._position, len(self._text))


class DeleteCommand(Command):
    def __init__(self, editor: TextEditor, position: int, length: int) -> None:
        self._editor = editor
        self._position = position
        self._length = length
        self._deleted_text = ""

    def execute(self) -> None:
        self._deleted_text = self._editor.delete(self._position, self._length)

    def undo(self) -> None:
        self._editor.insert(self._deleted_text, self._position)


@dataclass
class CommandHistory:
    _history: list[Command] = field(default_factory=list)

    def push(self, cmd: Command) -> None:
        cmd.execute()
        self._history.append(cmd)

    def undo(self) -> None:
        if self._history:
            self._history.pop().undo()


# Usage with undo support
editor = TextEditor()
history = CommandHistory()

history.push(InsertCommand(editor, "Hello", 0))
history.push(InsertCommand(editor, " World", 5))
print(editor.content)  # "Hello World"

history.undo()  # Undo " World"
print(editor.content)  # "Hello"

history.undo()  # Undo "Hello"
print(editor.content)  # ""
```

---

### State

```python
from abc import ABC, abstractmethod


class State(ABC):
    @abstractmethod
    def insert_coin(self, machine: "VendingMachine") -> str: ...

    @abstractmethod
    def select_product(self, machine: "VendingMachine") -> str: ...

    @abstractmethod
    def dispense(self, machine: "VendingMachine") -> str: ...


class NoCoinState(State):
    def insert_coin(self, machine: "VendingMachine") -> str:
        machine.state = HasCoinState()
        return "Coin accepted"

    def select_product(self, machine: "VendingMachine") -> str:
        return "Insert coin first"

    def dispense(self, machine: "VendingMachine") -> str:
        return "Insert coin first"


class HasCoinState(State):
    def insert_coin(self, machine: "VendingMachine") -> str:
        return "Coin already inserted"

    def select_product(self, machine: "VendingMachine") -> str:
        machine.state = DispensingState()
        return "Product selected"

    def dispense(self, machine: "VendingMachine") -> str:
        return "Select a product first"


class DispensingState(State):
    def insert_coin(self, machine: "VendingMachine") -> str:
        return "Please wait, dispensing"

    def select_product(self, machine: "VendingMachine") -> str:
        return "Already dispensing"

    def dispense(self, machine: "VendingMachine") -> str:
        machine.state = NoCoinState()
        return "Here's your product!"


class VendingMachine:
    def __init__(self) -> None:
        self.state: State = NoCoinState()

    def insert_coin(self) -> str:
        return self.state.insert_coin(self)

    def select_product(self) -> str:
        return self.state.select_product(self)

    def dispense(self) -> str:
        return self.state.dispense(self)


# State transitions happen automatically
vm = VendingMachine()
print(vm.select_product())  # "Insert coin first"
print(vm.insert_coin())     # "Coin accepted"
print(vm.select_product())  # "Product selected"
print(vm.dispense())        # "Here's your product!"
print(vm.dispense())        # "Insert coin first"
```

---

### Template Method

```python
from abc import ABC, abstractmethod


class DataPipeline(ABC):
    """Template method — defines the algorithm skeleton."""

    def run(self, source: str) -> dict:
        """Fixed algorithm. Subclasses fill in the steps."""
        raw = self.extract(source)
        cleaned = self.transform(raw)
        result = self.load(cleaned)
        self.notify(result)
        return result

    @abstractmethod
    def extract(self, source: str) -> list[dict]: ...

    @abstractmethod
    def transform(self, data: list[dict]) -> list[dict]: ...

    def load(self, data: list[dict]) -> dict:
        """Default implementation — subclasses may override."""
        return {"rows_loaded": len(data), "data": data}

    def notify(self, result: dict) -> None:
        """Hook — optional override."""
        print(f"Pipeline complete: {result['rows_loaded']} rows")


class CSVPipeline(DataPipeline):
    def extract(self, source: str) -> list[dict]:
        print(f"Reading CSV from {source}")
        return [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": ""}]

    def transform(self, data: list[dict]) -> list[dict]:
        # Remove rows with empty required fields
        return [row for row in data if all(row.values())]


class APIPipeline(DataPipeline):
    def extract(self, source: str) -> list[dict]:
        print(f"Fetching from API {source}")
        return [{"id": 1, "status": "active"}, {"id": 2, "status": "inactive"}]

    def transform(self, data: list[dict]) -> list[dict]:
        return [row for row in data if row["status"] == "active"]

    def notify(self, result: dict) -> None:
        print(f"API sync done: {result['rows_loaded']} active records")


CSVPipeline().run("data.csv")
APIPipeline().run("https://api.example.com/users")
```

---

### Chain of Responsibility

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Request:
    path: str
    method: str
    headers: dict[str, str]
    body: str = ""
    user: str | None = None


@dataclass
class Response:
    status: int
    body: str


class Middleware(ABC):
    def __init__(self) -> None:
        self._next: Middleware | None = None

    def set_next(self, handler: "Middleware") -> "Middleware":
        self._next = handler
        return handler

    def handle(self, request: Request) -> Response:
        if self._next:
            return self._next.handle(request)
        return Response(200, "OK")


class AuthMiddleware(Middleware):
    def handle(self, request: Request) -> Response:
        token = request.headers.get("Authorization")
        if not token:
            return Response(401, "Unauthorized")
        request.user = token.split(" ")[-1]  # Extract user from token
        return super().handle(request)


class RateLimitMiddleware(Middleware):
    def __init__(self, max_requests: int = 100) -> None:
        super().__init__()
        self._counts: dict[str, int] = {}
        self._max = max_requests

    def handle(self, request: Request) -> Response:
        user = request.user or "anonymous"
        self._counts[user] = self._counts.get(user, 0) + 1
        if self._counts[user] > self._max:
            return Response(429, "Too Many Requests")
        return super().handle(request)


class LoggingMiddleware(Middleware):
    def handle(self, request: Request) -> Response:
        print(f"{request.method} {request.path} (user={request.user})")
        response = super().handle(request)
        print(f"  → {response.status}")
        return response


# Build the chain
auth = AuthMiddleware()
rate_limit = RateLimitMiddleware(max_requests=10)
logging = LoggingMiddleware()

auth.set_next(rate_limit).set_next(logging)

# Process requests through the chain
req = Request("/api/data", "GET", {"Authorization": "Bearer alice"})
resp = auth.handle(req)
```

---

### Iterator

```python
from __future__ import annotations
from collections.abc import Iterator, Iterable
from dataclasses import dataclass, field


@dataclass
class TreeNode:
    value: int
    left: TreeNode | None = None
    right: TreeNode | None = None


class InOrderIterator(Iterator[int]):
    """Iterates a binary tree in-order (left, root, right)."""

    def __init__(self, root: TreeNode | None) -> None:
        self._stack: list[TreeNode] = []
        self._push_left(root)

    def _push_left(self, node: TreeNode | None) -> None:
        while node:
            self._stack.append(node)
            node = node.left

    def __next__(self) -> int:
        if not self._stack:
            raise StopIteration
        node = self._stack.pop()
        self._push_left(node.right)
        return node.value


class BinaryTree(Iterable[int]):
    def __init__(self, root: TreeNode | None = None) -> None:
        self.root = root

    def __iter__(self) -> Iterator[int]:
        return InOrderIterator(self.root)


# Usage — works with for loops, list(), etc.
tree = BinaryTree(
    TreeNode(4,
        left=TreeNode(2, TreeNode(1), TreeNode(3)),
        right=TreeNode(6, TreeNode(5), TreeNode(7)),
    )
)

for value in tree:
    print(value, end=" ")  # 1 2 3 4 5 6 7
```

**Pythonic alternative — generators:**

```python
from collections.abc import Iterator


def in_order(node: TreeNode | None) -> Iterator[int]:
    if node:
        yield from in_order(node.left)
        yield node.value
        yield from in_order(node.right)
```

---

### Mediator

```python
from typing import Protocol, Any


class Mediator(Protocol):
    def notify(self, sender: object, event: str, data: Any = None) -> None: ...


class Component:
    def __init__(self, mediator: Mediator | None = None) -> None:
        self._mediator = mediator

    @property
    def mediator(self) -> Mediator | None:
        return self._mediator

    @mediator.setter
    def mediator(self, m: Mediator) -> None:
        self._mediator = m


class AuthComponent(Component):
    def login(self, user: str) -> None:
        print(f"Auth: {user} logged in")
        if self._mediator:
            self._mediator.notify(self, "login", user)


class ProfileComponent(Component):
    def load_profile(self, user: str) -> None:
        print(f"Profile: Loading data for {user}")

    def show_welcome(self, user: str) -> None:
        print(f"Profile: Welcome back, {user}!")


class NotificationComponent(Component):
    def send_login_alert(self, user: str) -> None:
        print(f"Notification: Login alert sent for {user}")


class AppMediator:
    """Concrete mediator — coordinates component interactions."""

    def __init__(self, auth: AuthComponent, profile: ProfileComponent,
                 notifications: NotificationComponent) -> None:
        self._auth = auth
        self._profile = profile
        self._notifications = notifications
        auth.mediator = self
        profile.mediator = self
        notifications.mediator = self

    def notify(self, sender: object, event: str, data: Any = None) -> None:
        if event == "login":
            self._profile.load_profile(data)
            self._profile.show_welcome(data)
            self._notifications.send_login_alert(data)


# Components interact through mediator, not directly
auth = AuthComponent()
profile = ProfileComponent()
notif = NotificationComponent()
mediator = AppMediator(auth, profile, notif)

auth.login("alice")
# Triggers: profile load, welcome, and notification — all via mediator
```

---

### Memento

```python
from dataclasses import dataclass, field
from datetime import datetime
import copy


@dataclass(frozen=True)
class EditorMemento:
    """Memento — immutable snapshot of editor state."""
    content: str
    cursor_position: int
    timestamp: str


class TextEditor:
    def __init__(self) -> None:
        self.content = ""
        self.cursor_position = 0

    def type_text(self, text: str) -> None:
        self.content = (
            self.content[:self.cursor_position]
            + text
            + self.content[self.cursor_position:]
        )
        self.cursor_position += len(text)

    def save(self) -> EditorMemento:
        return EditorMemento(
            content=self.content,
            cursor_position=self.cursor_position,
            timestamp=datetime.now().isoformat(),
        )

    def restore(self, memento: EditorMemento) -> None:
        self.content = memento.content
        self.cursor_position = memento.cursor_position


@dataclass
class History:
    _snapshots: list[EditorMemento] = field(default_factory=list)

    def push(self, memento: EditorMemento) -> None:
        self._snapshots.append(memento)

    def pop(self) -> EditorMemento | None:
        return self._snapshots.pop() if self._snapshots else None


# Usage
editor = TextEditor()
history = History()

editor.type_text("Hello")
history.push(editor.save())

editor.type_text(" World")
history.push(editor.save())

editor.type_text("!!!")
print(editor.content)  # "Hello World!!!"

memento = history.pop()
if memento:
    editor.restore(memento)
print(editor.content)  # "Hello World"
```

---

### Visitor

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


# --- Element hierarchy (stable) ---
class DocumentNode(ABC):
    @abstractmethod
    def accept(self, visitor: "NodeVisitor") -> str: ...


@dataclass
class Heading(DocumentNode):
    level: int
    text: str

    def accept(self, visitor: "NodeVisitor") -> str:
        return visitor.visit_heading(self)


@dataclass
class Paragraph(DocumentNode):
    text: str

    def accept(self, visitor: "NodeVisitor") -> str:
        return visitor.visit_paragraph(self)


@dataclass
class CodeBlock(DocumentNode):
    language: str
    code: str

    def accept(self, visitor: "NodeVisitor") -> str:
        return visitor.visit_code_block(self)


# --- Visitor interface ---
class NodeVisitor(ABC):
    @abstractmethod
    def visit_heading(self, node: Heading) -> str: ...

    @abstractmethod
    def visit_paragraph(self, node: Paragraph) -> str: ...

    @abstractmethod
    def visit_code_block(self, node: CodeBlock) -> str: ...


# --- Concrete visitors (new operations without modifying elements) ---
class HTMLExporter(NodeVisitor):
    def visit_heading(self, node: Heading) -> str:
        return f"<h{node.level}>{node.text}</h{node.level}>"

    def visit_paragraph(self, node: Paragraph) -> str:
        return f"<p>{node.text}</p>"

    def visit_code_block(self, node: CodeBlock) -> str:
        return f"<pre><code class='{node.language}'>{node.code}</code></pre>"


class MarkdownExporter(NodeVisitor):
    def visit_heading(self, node: Heading) -> str:
        return f"{'#' * node.level} {node.text}"

    def visit_paragraph(self, node: Paragraph) -> str:
        return node.text

    def visit_code_block(self, node: CodeBlock) -> str:
        return f"```{node.language}\n{node.code}\n```"


class WordCounter(NodeVisitor):
    def visit_heading(self, node: Heading) -> str:
        return str(len(node.text.split()))

    def visit_paragraph(self, node: Paragraph) -> str:
        return str(len(node.text.split()))

    def visit_code_block(self, node: CodeBlock) -> str:
        return "0"  # Don't count code as words


# Usage — add new operations without touching element classes
doc: list[DocumentNode] = [
    Heading(1, "Design Patterns"),
    Paragraph("Patterns solve recurring design problems."),
    CodeBlock("python", "print('hello')"),
]

html = HTMLExporter()
md = MarkdownExporter()
counter = WordCounter()

for node in doc:
    print(node.accept(html))

print("---")

for node in doc:
    print(node.accept(md))

total_words = sum(int(node.accept(counter)) for node in doc)
print(f"\nWord count: {total_words}")
```

---

## Pattern Selection Quick Reference

| Pattern | Problem | Key Signal |
|---|---|---|
| **Factory Method** | Decouple object creation from usage | `if type == X: return X()` |
| **Abstract Factory** | Create families of related objects | Parallel construction `if/switch` |
| **Builder** | Complex object with many optional parts | 5+ constructor params |
| **Prototype** | Clone expensive-to-create objects | Repeated complex init |
| **Singleton** | Single shared instance | Global state (try DI first) |
| **Adapter** | Incompatible interface bridging | Wrapper functions everywhere |
| **Bridge** | Two independent axes of variation | M×N class explosion |
| **Composite** | Uniform tree structure treatment | `isinstance` checks for leaf vs. container |
| **Decorator** | Dynamic behavior stacking | Subclass explosion from combos |
| **Facade** | Simplify complex subsystem API | 5+ imports from one subsystem |
| **Flyweight** | Memory optimization for many similar objects | Profiler shows object memory waste |
| **Proxy** | Controlled access to expensive/remote object | Scattered init/auth checks |
| **Strategy** | Swappable algorithms | Growing `if/elif` for algorithm selection |
| **Observer** | One-to-many event notification | Manual update calls after state change |
| **Command** | Encapsulate operations as objects | Need undo/queue/log for operations |
| **State** | Behavior changes with internal state | Same `if state ==` in many methods |
| **Template Method** | Fixed algorithm, variable steps | Duplicated methods differing in few lines |
| **Chain of Responsibility** | Dynamic handler pipeline | Nested `if/elif` for handler routing |
| **Iterator** | Traverse collections uniformly | Need custom traversal (use generators first) |
| **Mediator** | Decouple many-to-many communication | Class importing many siblings |
| **Memento** | Save/restore object state | Need undo/snapshots |
| **Visitor** | Add operations to stable type hierarchy | New operations on fixed element types |
