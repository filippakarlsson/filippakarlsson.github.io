# Portfolio House — interaction prototype

Live site: [filippakarlsson.github.io](https://filippakarlsson.github.io/)

This is the technical foundation for a portfolio navigated through the authored Blender house:

`load house → detect room → fade its practical lights on → fade off → select room`

## Blender source

The inspected source scene is:

`/Users/filippakarlsson/Desktop/filippa_house_reference_rebuilt.blend`

The export script opens that file, prepares a temporary in-memory web scene, and writes `public/models/house.glb`. It does **not** save or alter the `.blend`.

```sh
npm run model:export
```

The temporary export preparation:

- adds one invisible `HITBOX_<ROOM>` mesh per room for reliable raycasting;
- converts the 24 authored hover point lights into semantic placement anchors;
- preserves custom light metadata and practical-lamp object names;
- evaluates modifiers and converts Blender-supported text/curves through the glTF exporter;
- exports the authored orthographic front camera.

## Room configuration

Labels, content keys, descriptions, and light colors live in `src/rooms.ts`. The stable room IDs currently are:

- `basement`
- `welcome`
- `playroom`
- `office`
- `studio`
- `rooftop`

Changing a public label or content destination does not require changing raycasting code.

## Run

This is a Vite application and must be viewed through its local server. Opening
`index.html` directly with a `file://` URL will not load the TypeScript, CSS, or
3D model correctly.

On macOS, double-click `Start Portfolio House.command` in this folder. Or run:

```sh
npm install
npm run dev
```

Production check:

```sh
npm run build
```

The prototype dispatches a `portfolio-room-select` browser event when a room is clicked. Later content transitions can subscribe to that event or replace the callback in `src/main.ts`.

## Current prototype boundaries

The GLB uses lossless Meshopt buffer compression. This reduces download size without simplifying the house geometry or lowering material quality. Inactive room lights are also excluded from rendering, so the GPU only evaluates the currently fading room-light group. A later deployment pass can still evaluate lazy loading and material batching without changing the source-house design.
