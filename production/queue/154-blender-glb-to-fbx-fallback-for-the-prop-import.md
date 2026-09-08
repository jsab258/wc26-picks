line: production (the prop line)
spec: If the engine cannot translate glTF headlessly, the smallest route is Blender,
  which is already installed on that machine and already has a directory at
  tools/meshgen/blender: convert GLB to FBX headlessly, then import FBX, which
  Unreal has imported natively for ever. Carries the axis and scale note from
  section 2.4 of the ruling.
acceptance: the sixteen assets reach uassets by whichever route the measurement chose, and
  the verdict names the route
max_sessions: 1
status: DEAD. 2026-09-08. Closed by the reading it was blocked on, which is the
  outcome a blocked-on-a-measurement item is supposed to have.
  production/d1-probe/ue-mesh-import.txt on f3f395c printed
  propGltfCanTranslate=3/3 and propGltfImporter=PRESENT/engine-says-it-can-translate/3-of-3,
  with eleven Interchange plugins present, six enabled including InterchangeAssets
  and InterchangeEditor, and all four Python import classes available. The engine
  can import glTF headlessly, so there is nothing for a Blender conversion to
  solve and building one would add a second asset pipeline to work around a
  capability the machine has.
  THE FINDING THIS REFUTES, recorded because it was acted on twice: the reading
  propGltfPlugins=GLTFExporter/1 from run 1 was taken as "this engine has no
  glTF importer". It was an instrument fault. The glob looked for *GLTF*.uplugin
  and the importer ships inside the Interchange plugins, whose names contain no
  GLTF at all. Refuted by the engine itself.
  WHAT THE WORK BECAME: the remaining fault is the invocation and the load-back,
  not the engine. Both routes ran and raised nothing while the asset did not load
  at the expected path, which is now measured rather than inferred by
  propImportedNames, propImportResolvedVia and propImportWaitChanged in
  tools/ue/import_prop_meshes.py. No new queue item: it is the same prop-import
  line, continuing.
