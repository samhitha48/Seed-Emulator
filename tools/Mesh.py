#!/usr/bin/env python3
import os
import sys
import yaml
from pathlib import Path

def sanitize_name(name):
    return name.replace("_", "-")

def get_pod_spec(name, image, ip, bird_conf=None):
    safe_name = sanitize_name(name)
    container = {
        "name": safe_name,
        "image": image,
        "imagePullPolicy": "IfNotPresent",
        "securityContext": { "privileged": True },
        "command": [
            "sh",
            "-c",
            f"ip addr add {ip}/24 dev eth0 && mkdir -p /run/bird && bird -c /etc/bird/bird.conf -s /run/bird/bird.ctl && sleep infinity"
        ],
        "volumeMounts": [] if not bird_conf else [{
            "mountPath": "/etc/bird",
            "name": f"{safe_name}-bird-config"
        }]
    }

    pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": safe_name,
            "annotations": {
                "k8s.v1.cni.cncf.io/networks": f'[{{"name": "meshnet", "interface": "eth0"}}]'
            }
        },
        "spec": {
            "containers": [container],
            "volumes": [] if not bird_conf else [{
                "name": f"{safe_name}-bird-config",
                "configMap": { "name": f"{safe_name}-bird-config" }
            }]
        }
    }
    return pod

def get_configmap(name, bird_conf_path):
    safe_name = sanitize_name(name)
    with open(bird_conf_path) as f:
        content = f.read()
    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": { "name": f"{safe_name}-bird-config" },
        "data": { "bird.conf": content }
    }

def get_topology(pods, links):
    return {
        "apiVersion": "networkop.co.uk/v1beta1",
        "kind": "Topology",
        "metadata": { "name": "autogen-topology" },
        "spec": {
            "links": [
                {
                    "uid": i,
                    "peer_pod": l["peer"],
                    "peer_intf": "eth0",
                    "peer_ip": l["peer_ip"],
                    "local_intf": "eth0",
                    "local_ip": l["local_ip"]
                } for i, l in enumerate(links)
            ]
        }
    }

def main(output_path):
    output = Path(output_path)
    pods = []
    configmaps = []
    links = []

    for pod_dir in output.iterdir():
        if not pod_dir.is_dir(): continue
        dockerfile = pod_dir / "Dockerfile"
        if not dockerfile.exists(): continue

        original_name = pod_dir.name
        safe_name = sanitize_name(original_name)
        image = safe_name
        ip_path = pod_dir / "ip.txt"
        bird_path = pod_dir / "bird.conf"

        ip = "10.105.0." + str(hash(safe_name) % 200 + 50)
        if ip_path.exists():
            ip = ip_path.read_text().strip()

        pods.append(get_pod_spec(original_name, image, ip, bird_path if bird_path.exists() else None))

        if bird_path.exists():
            configmaps.append(get_configmap(original_name, bird_path))

        for other in pods:
            if other["metadata"]["name"] == safe_name: continue
            links.append({
                "peer": other["metadata"]["name"],
                "peer_ip": "10.105.0.1", 
                "local_ip": ip
            })

    with open(output / "pods.yaml", "w") as f:
        yaml.dump_all(pods, f)
    with open(output / "configmaps.yaml", "w") as f:
        yaml.dump_all(configmaps, f)
    with open(output / "topology.yaml", "w") as f:
        yaml.dump(get_topology(pods, links), f)

    print(f"Generated manifests in: {output}/")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("python3 Mesh.py <path-to-SEED-output-dir>")
        sys.exit(1)
    main(sys.argv[1])
