# Tools

This folder contains the tools developed for the emulator.


## Script: `Mesh.py`

`Mesh.py` is responsible for automatically generating Kubernetes manifests from the output of SEED emulator builds.

### Functionality

The script performs the following actions:
1. Scans the SEED output directory for pod definitions and configuration files.
2. Generates:
   - `pods.yaml` for pod specifications including networking annotations.
   - `topology.yaml` describing the virtual links between pods using the Meshnet CNI.
   - `configmaps.yaml` for BIRD routing configurations (when applicable).
3. Applies custom networking, BGP peering, and routing logic automatically based on the file structure and conventions.

### Usage

Run the script with:
```bash
python3 tools/Mesh.py <path-to-SEED-output-dir>
```

The following must be ensured before running:
- Meshnet CNI is installed and active in the cluster.
- All custom router images are built and available on the node or cluster.
- Pods that require routing functionality must have their `bird.conf` present inside their output subdirectory.
- If node selectors or affinity settings are required, they should be manually added post-generation or incorporated into future script logic.

### Output

Three manifest files will be created inside the specified output directory:
- `pods.yaml`
- `topology.yaml`
- `configmaps.yaml`

These files can be directly applied using:
```bash
kubectl apply -f output/
```
