---
name: design-patterns
description: Use when designing new systems, refactoring tangled code, adding features that cause coupling, or when code smells like rigidity, fragility, or immobility appear
---

# Design Patterns

## Overview

Design patterns are **proven structural solutions to recurring software design problems**. They are not copy-paste templates — they are communication tools and thinking frameworks that prevent you from reinventing broken wheels.

**Core principle:** Every pattern exists to solve a specific tension between competing forces (flexibility vs. simplicity, decoupling vs. indirection). Pick the pattern that resolves the tension you actually have. Never apply a pattern because it "seems right."

## When to Use

**Apply a pattern when you observe these symptoms:**

- Adding a feature requires changing many unrelated files (rigidity)
- A change in one module breaks another (fragility)
- You cannot reuse a module in another context without dragging in dependencies (immobility)
- You find yourself writing switch/if-else chains that grow with each new variant
- You are duplicating logic across classes that share a common structure
- You need to vary one axis of behavior independently of another
- You want to shield a subsystem from external change

**Do NOT apply patterns when:**

- The code is simple and direct — patterns add indirection
- You have only one concrete variant (YAGNI — You Aren't Gonna Need It)
- A function or module does the job without needing classes
- You're writing throwaway/prototype code

## Pattern Selection Decision Framework

Before reaching for a pattern, answer three questions:

1. **What varies?** Identify the axis of change.
2. **What is stable?** Identify the invariant structure.
3. **What force am I resolving?** Name the tension (coupling, complexity, extensibility).

Then match to the right category:

| If you need to... | Category | Start here |
|---|---|---|
| Create objects without specifying exact classes | Creational | Factory Method, Abstract Factory |
| Build complex objects step by step | Creational | Builder |
| Compose objects into larger structures | Structural | Composite, Decorator |
| Decouple an abstraction from its implementation | Structural | Bridge, Adapter |
| Simplify access to a complex subsystem | Structural | Facade |
| Vary an algorithm or behavior at runtime | Behavioral | Strategy, State |
| Notify dependents of state changes | Behavioral | Observer |
| Encapsulate a request as an object | Behavioral | Command |
| Traverse a collection without exposing internals | Behavioral | Iterator |
| Define skeleton algorithm, let subclasses fill steps | Behavioral | Template Method |

---

## Creational Patterns

Object creation mechanisms that increase flexibility and decouple client code from concrete classes.

### Factory Method

**Problem:** Client code is coupled to concrete class constructors. Adding a new type requires modifying client code.

**Solution:** Define an interface for creating objects, but let subclasses decide which class to instantiate.

**When to apply:**
- You don't know ahead of time which concrete types your code will need
- You want to let users extend your library with their own types
- You're building a framework where the framework controls *when* to create, but users control *what* to create

**Key structure:**
```
Creator (declares factory_method) → ConcreteCreator (overrides factory_method)
Product (interface)               → ConcreteProduct (implements Product)
```

**Smell that signals need:** `if type == "X": return X()` chains in construction code.

### Abstract Factory

**Problem:** You need to create families of related objects that must be used together, but you don't want client code to depend on concrete classes.

**Solution:** Provide an interface for creating families of related objects without specifying their concrete classes.

**When to apply:**
- Your system must work with multiple families of related products (e.g., UI themes: buttons + checkboxes + scrollbars per theme)
- You need to enforce that products from the same family are used together
- You want to swap entire product families at runtime or configuration time

**Key structure:**
```
AbstractFactory    → ConcreteFactory1, ConcreteFactory2
AbstractProductA   → ProductA1, ProductA2
AbstractProductB   → ProductB1, ProductB2
```

**Smell that signals need:** Parallel `if/switch` blocks creating related objects that must stay in sync.

### Builder

**Problem:** A constructor with many parameters is unreadable and error-prone. Some parameters are optional. Object construction requires multiple steps.

**Solution:** Separate the construction of a complex object from its representation so that the same construction process can create different representations.

**When to apply:**
- Object has many optional fields or construction steps
- You need to construct different representations of the same product
- Construction logic is complex enough to warrant isolation from business logic

**Key structure:**
```
Director (defines build order) → Builder (interface for steps)
                                → ConcreteBuilder (implements steps, holds product)
```

**Smell that signals need:** Constructors with 5+ parameters, telescoping constructors, or objects that are invalid until multiple setters are called.

### Prototype

**Problem:** Creating objects is expensive (DB calls, deep hierarchies) or involves complex setup that you want to duplicate.

**Solution:** Create new objects by copying an existing instance (the prototype) rather than constructing from scratch.

**When to apply:**
- Object creation is costly and the new object is similar to an existing one
- You want to avoid subclassing just to configure an object differently
- Runtime determines which objects to create

**Smell that signals need:** Complex initialization code duplicated across factory methods.

### Singleton

**Problem:** You need exactly one instance of a class with a global access point.

**Solution:** Ensure a class has only one instance and provide a global point of access to it.

**When to apply (SPARINGLY):**
- Shared resource that must not be duplicated (connection pool, hardware interface, configuration registry)
- You must control concurrent access to a shared resource

**WARNING:** Singleton is heavily overused. Prefer dependency injection. Singletons make testing hard, hide dependencies, and create tight coupling. If you're reaching for Singleton, first consider whether passing the instance explicitly would work.

**Smell that signals need:** Global mutable state accessed from many places — but first try DI.

---

## Structural Patterns

How to assemble objects and classes into larger structures while keeping them flexible.

### Adapter

**Problem:** You have a class with a useful interface, but it doesn't match the interface your client code expects.

**Solution:** Wrap the incompatible object in an adapter that translates calls between the expected and actual interfaces.

**When to apply:**
- Integrating third-party or legacy code with a different interface
- You want to use several existing subclasses but it's impractical to modify each one
- You need to convert data formats between systems

**Key structure:**
```
Target (interface client expects) ← Adapter (wraps Adaptee) → Adaptee (existing interface)
```

**Smell that signals need:** Wrapper functions scattered across your codebase to translate between two interfaces.

### Bridge

**Problem:** You have a class that varies along two independent dimensions. Subclassing causes a combinatorial explosion (e.g., Shape × Color = many classes).

**Solution:** Split the monolithic class into two separate hierarchies — abstraction and implementation — that can vary independently.

**When to apply:**
- A class has orthogonal dimensions of variation (platform × feature, shape × renderer)
- You want to switch implementations at runtime
- Changes in implementation should not affect clients

**Key structure:**
```
Abstraction (holds ref to Implementor) → RefinedAbstraction
Implementor (interface)                → ConcreteImplementorA, ConcreteImplementorB
```

**Smell that signals need:** Class hierarchy growing as M×N with two independent axes.

### Composite

**Problem:** You need to treat individual objects and compositions of objects uniformly (e.g., a file vs. a folder containing files).

**Solution:** Compose objects into tree structures. Let clients treat individual objects and compositions identically through a common interface.

**When to apply:**
- You have a part-whole hierarchy (trees)
- Clients should not distinguish between leaf nodes and branches
- Operations should propagate recursively through the tree

**Key structure:**
```
Component (interface) ← Leaf (terminal)
                      ← Composite (contains children: Component[])
```

**Smell that signals need:** `isinstance` checks to distinguish between single items and collections.

### Decorator

**Problem:** You need to add responsibilities to objects dynamically without modifying existing classes or using subclassing.

**Solution:** Wrap objects in decorator objects that add behavior before or after delegating to the wrapped object.

**When to apply:**
- You need to add behavior to individual objects, not entire classes
- Behaviors must be combinable (logging + caching + auth on a request)
- Subclassing would cause an explosion of combinations

**Key structure:**
```
Component (interface) ← ConcreteComponent
                      ← Decorator (wraps Component, implements Component)
                          ← ConcreteDecoratorA, ConcreteDecoratorB
```

**Smell that signals need:** Subclass explosion from combining orthogonal behaviors.

### Facade

**Problem:** A subsystem has many classes with complex interactions. Client code becomes coupled to subsystem internals.

**Solution:** Provide a simplified, unified interface to the subsystem. The facade delegates to subsystem objects.

**When to apply:**
- You want a simple interface to a complex subsystem
- You want to layer your system and define entry points to each layer
- You want to reduce dependencies between subsystems

**Smell that signals need:** Client code importing 5+ classes from the same subsystem.

### Flyweight

**Problem:** Your application creates a huge number of similar objects, consuming excessive memory.

**Solution:** Share common state (intrinsic) between objects. Store unique state (extrinsic) externally.

**When to apply:**
- You have thousands/millions of objects with shared data
- Most object state can be made extrinsic (moved outside the object)
- Memory consumption is a real, measured problem (not speculative)

**Smell that signals need:** Profiler shows memory dominated by many nearly-identical objects.

### Proxy

**Problem:** You need to control access to an object — for lazy initialization, access control, logging, caching, or remote access.

**Solution:** Provide a surrogate that controls access to the real object, implementing the same interface.

**When to apply:**
- Lazy initialization (virtual proxy) — object is expensive to create
- Access control (protection proxy) — restrict who can call what
- Logging/caching (smart proxy) — add bookkeeping transparently
- Remote access (remote proxy) — local stand-in for a remote object

**Smell that signals need:** Initialization code or access checks scattered across call sites.

---

## Behavioral Patterns

How objects communicate and distribute responsibilities.

### Strategy

**Problem:** You have multiple algorithms for a task and want to switch between them without changing client code.

**Solution:** Define a family of algorithms as separate classes implementing a common interface. Let the client choose at runtime.

**When to apply:**
- Multiple algorithms exist for a task (sorting, validation, pricing)
- You want to eliminate conditional statements that select behavior
- Algorithms must be swappable at runtime

**Key structure:**
```
Context (holds Strategy ref) → Strategy (interface) → ConcreteStrategyA, ConcreteStrategyB
```

**Smell that signals need:** A growing `if/elif/else` or `switch` that selects algorithm logic.

### Observer

**Problem:** One object changes state and many others must react, but you don't want tight coupling between them.

**Solution:** Define a one-to-many dependency. When the subject changes, all registered observers are notified.

**When to apply:**
- Changes to one object require updating others, and you don't know how many in advance
- An object should notify others without knowing who they are
- Event-driven architectures, pub/sub systems, reactive UIs

**Smell that signals need:** Manual update calls scattered after every state change.

### Command

**Problem:** You want to parameterize objects with operations, queue operations, support undo, or log operations.

**Solution:** Encapsulate a request as an object, thereby letting you parameterize clients with different requests, queue or log requests, and support undoable operations.

**When to apply:**
- You need undo/redo functionality
- You need to queue, schedule, or serialize operations
- You want to decouple the invoker of an operation from the performer

**Smell that signals need:** Methods that take callbacks but need undo, logging, or queuing.

### State

**Problem:** An object behaves differently based on its internal state, and transitions between states are complex.

**Solution:** Extract state-specific behavior into separate state classes. The context delegates to its current state object.

**When to apply:**
- An object has clearly defined states with different behaviors
- State transitions are complex enough to warrant explicit modeling
- Conditional logic based on state is spread across many methods

**Smell that signals need:** Multiple methods with the same `if state == ...` branching.

### Template Method

**Problem:** Several classes follow the same algorithm structure but vary in individual steps.

**Solution:** Define the skeleton of an algorithm in a base class. Let subclasses override specific steps without changing the algorithm's structure.

**When to apply:**
- You have a fixed algorithm with variable steps
- Multiple classes share the same structure but differ in details
- You want to let users extend specific steps but not the overall flow

**Smell that signals need:** Duplicated method bodies that differ only in a few lines.

### Chain of Responsibility

**Problem:** More than one object may handle a request, and the handler isn't known a priori. You want to decouple senders from receivers.

**Solution:** Pass the request along a chain of handlers. Each handler decides to process or pass it along.

**When to apply:**
- Multiple handlers may process a request
- You want to assemble the handler chain dynamically
- You need middleware-style processing (auth → validation → logging → handler)

**Smell that signals need:** Nested `if/elif` deciding which handler to invoke.

### Iterator

**Problem:** You need to traverse a collection's elements without exposing its internal structure.

**Solution:** Extract traversal behavior into a separate iterator object.

**When to apply:**
- You want to traverse complex data structures (trees, graphs) uniformly
- You want multiple simultaneous traversals
- You want to decouple traversal algorithms from data structures

**Note:** Most modern languages provide built-in iterator support (Python generators, `__iter__`/`__next__`). Use the pattern explicitly only when built-in support is insufficient.

### Mediator

**Problem:** Many objects communicate directly, creating a tangled web of dependencies.

**Solution:** Introduce a mediator object that encapsulates how a set of objects interact. Objects no longer communicate directly — they go through the mediator.

**When to apply:**
- Many classes are tightly coupled through direct communication
- Reusing a class requires bringing many other classes along
- You want to centralize complex communication logic

**Smell that signals need:** A class that imports/references many peers at the same level.

### Memento

**Problem:** You need to save and restore an object's state without violating encapsulation.

**Solution:** Capture the object's internal state in a memento object that can be stored and used to restore state later.

**When to apply:**
- You need snapshot/rollback (undo, checkpoints, transactions)
- Direct access to the object's fields would violate encapsulation

### Visitor

**Problem:** You need to define new operations on elements of a stable class hierarchy without modifying those classes.

**Solution:** Move the operation into a visitor object. Elements accept the visitor, which then performs the operation.

**When to apply:**
- You need to add many unrelated operations to a stable class hierarchy
- The class hierarchy rarely changes but operations change often
- You want to avoid polluting element classes with unrelated logic

**Tradeoff:** Adding a new element class requires updating all visitors. Use only when element types are stable.

---

## SOLID Principles — The Foundation

Design patterns implement these principles. Understand these first.

| Principle | What it means | Violation smell |
|---|---|---|
| **S**ingle Responsibility | A class has one reason to change | God classes, 500+ line classes |
| **O**pen/Closed | Open for extension, closed for modification | Modifying existing code for every new feature |
| **L**iskov Substitution | Subtypes must be substitutable for their base types | Overridden methods that throw "not supported" |
| **I**nterface Segregation | No client should depend on methods it doesn't use | Empty interface method implementations |
| **D**ependency Inversion | Depend on abstractions, not concretions | High-level modules importing low-level modules |

## Anti-Patterns to Avoid

| Anti-pattern | What it looks like | Better approach |
|---|---|---|
| **God Object** | One class that does everything | Extract classes by responsibility (SRP) |
| **Premature Abstraction** | Patterns applied before a second use case exists | Wait for the duplication; extract on second/third occurrence |
| **Pattern Worship** | Using Strategy when a simple function suffices | Apply patterns only when complexity warrants it |
| **Deep Inheritance** | 4+ levels of inheritance | Prefer composition over inheritance |
| **Leaky Abstraction** | Abstraction exposes implementation details | Redesign the interface boundary |
| **Shotgun Surgery** | One change requires editing many classes | Group related logic (may need Extract Class or Move Method) |

## Composition Over Inheritance

**Default to composition.** Use inheritance only when there is a genuine "is-a" relationship AND you want polymorphic behavior.

| Use inheritance when... | Use composition when... |
|---|---|
| Subtype IS-A base type in every context | You need HAS-A or USES-A relationships |
| You need polymorphism through a type hierarchy | You need to combine behaviors flexibly |
| The base class is designed for extension | You want to change behavior at runtime |
| Hierarchy is shallow (1-2 levels) | You want to avoid coupling to parent implementation |

## Python Reference

For concrete Python implementations of all 23 GoF patterns, see [design-patterns-python.md](design-patterns-python.md). This reference shows idiomatic Python implementations using `abc.ABC`, `Protocol`, dataclasses, `__iter__`/`__next__`, decorators, and other Python-native constructs.

**Baseline source:** Patterns follow the classification and structure from [refactoring.guru/design-patterns](https://refactoring.guru/design-patterns/python), adapted to emphasize Pythonic idioms.

## Common Mistakes

1. **Applying patterns prophylactically** — Wait for the symptom before applying the cure. One concrete class does not need a factory.
2. **Confusing Strategy and State** — Strategy: client chooses algorithm. State: object changes behavior based on internal state transitions.
3. **Overusing Singleton** — If you can pass the dependency explicitly, do that instead.
4. **Using inheritance when composition works** — Default to composition. Use inheritance for genuine type hierarchies.
5. **Creating abstractions with one implementation** — An interface with one implementor is overhead, not abstraction. Wait for the second.
6. **Pattern naming without understanding** — Saying "let's use Observer" means nothing if you can't explain what varies, what's stable, and what force it resolves.
