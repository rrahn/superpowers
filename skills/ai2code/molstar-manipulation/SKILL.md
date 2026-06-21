---
name: molstar-manipulation
description: >
  Interactive small molecule manipulation in Mol* (molstar) — coordinate transforms via
  TransformStructureConformation, Canvas3D drag event handling, 60fps update patterns with
  requestAnimationFrame coalescing, spatial queries for collision detection, and
  React 19 integration patterns for imperative 3D libraries. Load when: (1) implementing
  drag-to-move for ligands or molecular fragments in Mol*, (2) applying rigid-body
  transforms (translation/rotation) to substructures, (3) integrating Mol* with React 19
  state management, (4) implementing undo/redo for coordinate changes, (5) detecting
  VDW clashes during molecular manipulation, (6) working with Canvas3D interaction events.
  Trigger phrases: "move ligand", "drag molecule", "manipulate structure", "transform
  coordinates", "TransformStructureConformation", "interactive docking", "ligand placement".
alwaysApply: false
tier: 3
user-invocable: true
metadata:
  version: "1.0"
  sources: "https://github.com/molstar/molstar/tree/v5.9.0 (reviewed 2026-05), https://react.dev/blog/2024/12/05/react-19"
---

# Mol* Interactive Manipulation

Patterns and APIs for implementing interactive small molecule (ligand) manipulation
within a Mol* viewer embedded in a React 19 application.

---

## 1. Core Concept: Coordinate Immutability

Mol* coordinates are **immutable** after first access. You cannot mutate `atomicConformation`
directly. Instead, use one of these state tree mechanisms:

| Strategy | API | Cost | Best For |
|----------|-----|------|----------|
| Rigid-body transform | `TransformStructureConformation` (`'components'` mode) | Medium | Interactive drag (60fps) |
| Replace coordinates | `ModelWithCoordinates` (swap `atomicConformation`) | Low | After minimization |
| New trajectory frame | `ModelFromTrajectory` (change `modelIndex`) | Medium | Frame switching |

---

## 2. `TransformStructureConformation` — The Primary API

Located in `mol-plugin-state/transforms/model.ts`. This is a `StateTransformer` decorator
applied to a `Structure` node in the state tree.

### Two Modes

| Mode | canAutoUpdate | Use For |
|------|--------------|---------|
| `'matrix'` | `false` (always Recreate) | One-shot alignment (superposition) |
| `'components'` | `true` (incremental) | **Interactive dragging** |

### `'components'` Parameters

```typescript
{
  translation: Vec3,           // ABSOLUTE position (not delta!)
  axis: Vec3,                  // Rotation axis (unit vector)
  angle: number,               // Degrees [-360, 360]
  rotationCenter: {
    name: 'centroid' | 'point',
    params: {} | { point: Vec3 }
  }
}
```

> **Critical**: `translation` is absolute. Accumulate deltas yourself in a local variable.

### Hard Constraint

`Structure.transform()` **throws** on non-rotation/translation matrices. No scaling, no shear.

---

## 3. Implementation Workflow

### Step 1: Isolate Ligand as Component

```typescript
import { MolScriptBuilder as MS } from 'molstar/lib/mol-script/language/builder';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { Vec3 } from 'molstar/lib/mol-math/linear-algebra';

const ligandExpr = MS.struct.generator.atomGroups({
  'residue-test': MS.core.rel.eq([
    MS.struct.atomProperty.macromolecular.label_comp_id(),
    MS.core.type.str(['LIG'])  // Your ligand's 3-letter code
  ])
});

const structureCell = plugin.managers.structure.hierarchy.current.structures[0].cell;
const componentRef = await plugin.builders.structure.tryCreateComponentFromExpression(
  structureCell, ligandExpr, 'ligand-component', { label: 'Ligand' }
);
```

### Step 2: Attach Transform Decorator

```typescript
await plugin.state.data.build()
  .to(componentRef!)
  .apply(StateTransforms.Model.TransformStructureConformation, {
    transform: {
      name: 'components',
      params: {
        translation: Vec3.create(0, 0, 0),
        axis: Vec3.create(1, 0, 0),
        angle: 0,
        rotationCenter: { name: 'centroid', params: {} }
      }
    }
  }, { ref: 'ligand-transform' })  // Stable ref for updates
  .commit();
```

### Step 3: Subscribe to Drag Events

```typescript
plugin.canvas3d!.interaction.drag.subscribe((event) => {
  if (!StructureElement.Loci.is(event.current.loci)) return;
  
  const camera = plugin.canvas3d!.camera;
  const center = event.current.loci.structure.boundary.sphere.center;
  const pixelSize = camera.getPixelSize(center);
  
  const dx = (event.pageEnd[0] - event.pageStart[0]) * pixelSize;
  const dy = -(event.pageEnd[1] - event.pageStart[1]) * pixelSize;
  
  onDragMove(dx, dy, 0);
});
```

### Step 4: rAF-Coalesced Updates

```typescript
let cumulative = Vec3.create(0, 0, 0);
let rafId: number | null = null;

function onDragMove(dx: number, dy: number, dz: number) {
  Vec3.add(cumulative, cumulative, Vec3.create(dx, dy, dz));
  if (!rafId) rafId = requestAnimationFrame(flush);
}

async function flush() {
  rafId = null;
  await plugin.state.data.build()
    .to('ligand-transform')
    .update(StateTransforms.Model.TransformStructureConformation, () => ({
      transform: { name: 'components', params: {
        translation: Vec3.clone(cumulative),
        axis: Vec3.create(1, 0, 0), angle: 0,
        rotationCenter: { name: 'centroid', params: {} }
      }}
    }))
    .commit({ doNotLogTiming: true });
}
```

---

## 4. TrackballControls Conflict

Default drag rotates camera. Disambiguation strategies:

1. **Modifier key** (recommended): `Alt+drag` = move ligand, plain drag = rotate camera
2. **Mode toggle**: UI button switches between "view" and "edit" mode
3. **Selection-aware**: If drag starts on selected ligand, move it; otherwise, rotate camera

---

## 5. React 19 Integration

### Plugin Lifecycle (useEffect + cleanup)

```tsx
useEffect(() => {
  let cancelled = false;
  (async () => {
    const plugin = await createPluginUI({ target: ref.current!, render: renderReact18 });
    if (cancelled) { plugin.dispose(); return; }
    pluginRef.current = plugin;
  })();
  return () => { cancelled = true; pluginRef.current?.dispose(); };
}, []);
```

### State Sync (useSyncExternalStore)

```tsx
function usePluginState(plugin: PluginContext) {
  const store = useMemo(() => ({
    subscribe: (cb: () => void) => {
      const sub = plugin.state.data.events.changed.subscribe(cb);
      return () => sub.unsubscribe();
    },
    getSnapshot: () => plugin.state.data.snapshot,
  }), [plugin]);
  return useSyncExternalStore(store.subscribe, store.getSnapshot, () => null);
}
```

### Async Operations (useTransition)

```tsx
const [isPending, startTransition] = useTransition();
function loadStructure(pdbId: string) {
  startTransition(async () => { /* load structure */ });
}
```

---

## 6. Spatial Queries & Clash Detection

```typescript
// StructureLookup3D for proximity checks
const lookup = structure.lookup3d;
const result = lookup.find(x, y, z, radiusAngstroms);
// result: { count, indices, squaredDistances }
```

---

## 7. Undo/Redo

Push ONE command on `mouseup`, not per `mousemove`:
- `mousedown`: record `translationAtDragStart`
- `mousemove`: update visual (no undo entry)
- `mouseup`: `undoStack.push({ before, after })`

---

## 8. Vite + TypeScript Configuration

These options apply when integrating Mol* into a Vite + React 19 + TypeScript app on the
v5.9.0 reviewed line:

```typescript
// tsconfig.json
"useDefineForClassFields": false  // CRITICAL for Mol*
"skipLibCheck": true               // Mol* types include webxr
```

**Legacy workaround (Mol* < v5.7 only):** If you are stuck on v5.6.1 or earlier, add the
following to `vite.config.ts` to dodge a circular-dependency bug:

```typescript
optimizeDeps: { exclude: ['molstar'] }
```

The circular-dep bug was fixed in v5.7; on v5.7+ (including the v5.9.0 reviewed version)
this exclude is unnecessary and can be removed.

---

## 9. Known Limitations

- RDKit.js (WASM MinimalLib) has NO force field minimization — use server-side Python
- No built-in rotation gizmo — must implement custom
- `Structure.transform()` cost unknown for large structures — profile empirically
- `renderReact18` from Mol* is compatible with React 19 (confirmed v4.10.0+)

---

## 10. Key Imports Cheatsheet

```typescript
import { Vec3, Mat4 } from 'molstar/lib/mol-math/linear-algebra';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { MolScriptBuilder as MS } from 'molstar/lib/mol-script/language/builder';
import { StructureElement, StructureProperties } from 'molstar/lib/mol-model/structure';
import { Loci } from 'molstar/lib/mol-model/loci';
import { Canvas3D } from 'molstar/lib/mol-canvas3d/canvas3d';
import { createPluginUI } from 'molstar/lib/mol-plugin-ui';
import { renderReact18 } from 'molstar/lib/mol-plugin-ui/react18';
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
```

---

## 11. Verification

After implementing interactive ligand manipulation, verify with:

1. **Load a PDB with a ligand** (e.g., `1CBS` with retinol `REA`, or `3PTB` with benzamidine `BEN`)
2. **Alt+drag on the ligand** — it should translate smoothly at 60fps with no jank
3. **Check browser console** — no `Structure.transform` errors or state tree warnings
4. **Release mouse** — undo entry should be created; `Ctrl+Z` reverts to original position
5. **Drag beyond pocket** — constraint should limit movement; visual warning if clash detection enabled
6. **Profile DevTools Performance tab** — each drag frame should complete in <16ms (60fps budget)
7. **StrictMode test** — run in React 19 StrictMode; verify no double-initialization or leaked subscriptions
