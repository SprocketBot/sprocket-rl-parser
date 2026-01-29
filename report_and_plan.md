# Report: Protobuf Usage in Carball

## Current State Analysis
Protobufs are currently deeply integrated into the `carball` architecture, serving as the **primary internal data structure** for the analysis phase, not just an export format.

1.  **Data Backbone**: The `AnalysisManager` initializes a `game_pb2.Game` object immediately. As the replay is parsed and analyzed, data is populated directly into this protobuf structure.
    *   **Metadata**: `ApiGame`, `ApiPlayer`, etc., convert parsed JSON data into protobuf fields.
    *   **Stats**: `StatsManager` and individual stat calculators (e.g., `BoostStat`, `HitAnalysis`) write calculated statistics directly into the protobuf hierarchy (e.g., `player.stats.boost`).
    *   **Events**: `EventsCreator` generates `Hit`, `Goal`, and `Demo` protobuf objects and appends them to the game object.
2.  **Serialization**: The `ProtobufManager` handles reading/writing these objects to files (`.pts`), which is the primary way analysis results are saved and loaded.
3.  **Build Process**: Currently, `setup.py` attempts to run `protoc` (the Protocol Buffer compiler) on the user's machine during installation (`PostInstallCommand`). This requires the user to have `protoc` installed and in their path, which is a major friction point and source of errors ("bane of existence").

## Option 1: Migrate Away (Rip Them Out)

This option involves replacing the Protobuf classes with native Python objects (e.g., `dataclasses` or `Pydantic` models). This removes the dependency on `protoc` and the `protobuf` library entirely.

### Pros
*   **Zero Build Dependencies**: No need for `protoc` or complex build steps. Pure Python.
*   **Easier Debugging**: Native Python objects are often easier to inspect and modify than generated protobuf classes.
*   **Flexibility**: Easier to add helper methods or properties to the data classes.

### Cons
*   **High Effort**: Requires a substantial refactor. Every file importing `carball.generated` (which is most of the analysis logic) needs modification.
*   **Performance**: Protobufs are generally faster and more compact for serialization than standard JSON/Pickle, though for this use case, the difference might be negligible compared to the analysis time.
*   **Breaking Change**: Any external tools relying on the `.pts` (protobuf) output format will break.

### Execution Plan
1.  **Define Data Models**: Create a new module (e.g., `carball.models`) with Python `dataclasses` that mirror the structure of the existing `.proto` files (Game, Player, Team, Stats, etc.).
2.  **Update Analysis Manager**: Modify `AnalysisManager` to initialize the new `Game` dataclass instead of `game_pb2.Game`.
3.  **Refactor Stats & Events**: Systematically go through `carball/analysis/stats/` and `carball/analysis/events/` to update all references from `proto_game.field` to `game_model.field`.
4.  **Update Metadata Parsers**: Rewrite `ApiGame`, `ApiPlayer`, etc., to populate the dataclasses.
5.  **Implement Serialization**: Create a new `JsonManager` (or similar) to handle saving/loading the dataclasses to disk (likely using `json` or `pickle`).
6.  **Cleanup**: Remove `api/` directory, `utils/create_proto.py`, `setup.py` hooks, and `protobuf` dependency.
7.  **Fix Tests**: Update the test suite to assert against the new data models.

## Option 2: Fix Build Process (Keep Protobufs)

This option keeps the Protobuf code but fixes the "version hell" and installation issues by changing *how* the code is generated and packaged.

### Pros
*   **Lower Effort**: Preserves the existing logic and data structures.
*   **Backward Compatibility**: Keeps the `.pts` format for existing tools.
*   **Type Safety**: Generated protobuf code provides strict typing.

### Cons
*   **Retains Dependency**: Still depends on the `protobuf` runtime library (though not the compiler for the end-user).

### Execution Plan
1.  **Pre-Generate Code**: Shift the responsibility of running `protoc` from the **end-user** (at install time) to the **developer/CI** (at build time).
2.  **Remove Setup Hooks**: Delete `PostInstallCommand` and `PostDevelopCommand` from `setup.py`. The `pip install` process should *never* run `protoc`.
3.  **Include Generated Files**: Update `MANIFEST.in` to explicitly include the generated `_pb2.py` files in the source distribution (`sdist`) and wheels.
    *   *Crucial*: The generated files must be present in the package uploaded to PyPI.
4.  **Pin Dependencies**: In `setup.py`, pin the `protobuf` runtime library to a version compatible with the generated code (e.g., `protobuf>=3.0.0,<4.0.0` or similar, depending on what `protoc` version is used).
5.  **CI Automation**: Configure GitHub Actions to:
    *   Install `protoc`.
    *   Run `utils/create_proto.py` to generate the Python files.
    *   Build the package (Wheel/Sdist).
    *   Publish to PyPI.
6.  **Version Control (Optional)**: You could choose to commit the generated `_pb2.py` files to the repo (so they are always there), or just ensure they are generated before packaging. Committing them is often easier for ensuring they are present.

## Recommendation
If your primary pain point is "ridiculous version hell/protoc mismatch/generated files missing" during **installation/usage**, **Option 2 is the most pragmatic and immediate fix**. It solves the user-facing problem completely: users just `pip install carball` and it works, because the generated files are already inside the package.

If you fundamentally dislike Protobufs or want to remove the dependency for other reasons (e.g., binary size, complexity), **Option 1** is cleaner in the long run but requires significantly more work upfront.