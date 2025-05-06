#!/usr/bin/env python3
import os
import yaml

# Define nodes and their interfaces
nodes = [
    {
        "name": "rnode-199-router0",
        "image": "seed-router-local",
        "interfaces": ["eth0", "eth1"],
        "is_router": True,
        "bird_conf_path": "output/rnode_199_router0/bird.conf"
    },
    {
        "name": "rnode-2-r100",
        "image": "seed-router-local",
        "interfaces": ["eth0", "eth1"],
        "is_router": False  # No bird.conf assumed yet
    }
]

# Define meshnet link connections
links = [
    {
        "uid": 1,
        "a": ("rnode-199-router0", "eth0"),
        "b": ("rnode-2-r100", "eth0")
    },
    {
        "uid": 2,
        "a": ("rnode-2-r100", "eth1"),
        "b": ("rnode-199-router0", "eth1")
    }
]

def generate_pod_yaml(node):
    pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": node["name"],
            "annotations": {
                "k8s.v1.cni.cncf.io/networks": str([
                    {"name": "meshnet", "interface": iface}
                    for iface in node["interfaces"]
                ])
            }
        },
        "spec": {
            "containers": [
                {
                    "name": node["name"],
                    "image": node["image"],
                    "command": ["sh", "-c", "mkdir -p /run/bird && bird -c /etc/bird/bird.conf -s /run/bird/bird.ctl"],
                    "securityContext": {"privileged": True},
                    "volumeMounts": []
                }
            ],
            "volumes": [],
            "securityContext": {},
        }
    }

    if node.get("is_router"):
        pod["spec"]["containers"][0]["volumeMounts"].append({
            "name": "bird-config",
            "mountPath": "/etc/bird"
        })
        pod["spec"]["volumes"].append({
            "name": "bird-config",
            "configMap": {
                "name": f"{node['name']}-bird-config"
            }
        })

    return pod

def generate_configmap(node):
    if not node.get("is_router"):
        return None
    path = node["bird_conf_path"]
    if not os.path.exists(path):
        print(f"Warning: bird.conf not found at {path}")
        return None
    with open(path, "r") as f:
        config_data = f.read()
    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": f"{node['name']}-bird-config"
        },
        "data": {
            "bird.conf": config_data
        }
    }

def generate_topology_yaml(links):
    topology = {
        "apiVersion": "networkop.co.uk/v1beta1",
        "kind": "Topology",
        "metadata": {
            "name": "bgp-topology"
        },
        "spec": {
            "links": []
        }
    }
    for link in links:
        # Forward
        topology["spec"]["links"].append({
            "uid": link["uid"],
            "peer_pod": link["b"][0],
            "local_intf": link["a"][1],
            "peer_intf": link["b"][1]
        })
        # Reverse (Meshnet needs both sides)
        topology["spec"]["links"].append({
            "uid": link["uid"] + 100,
            "peer_pod": link["a"][0],
            "local_intf": link["b"][1],
            "peer_intf": link["a"][1]
        })
    return topology

def write_yaml(path, data):
    with open(path, 'w') as f:
        yaml.dump_all(data if isinstance(data, list) else [data], f)

def main():
    os.makedirs("output/k8s", exist_ok=True)
    pod_yamls = []
    configmap_yamls = []

    for node in nodes:
        pod_yamls.append(generate_pod_yaml(node))
        cm = generate_configmap(node)
        if cm:
            configmap_yamls.append(cm)

    topology_yaml = generate_topology_yaml(links)

    write_yaml("output/k8s/pods.yaml", pod_yamls)
    write_yaml("output/k8s/configmaps.yaml", configmap_yamls)
    write_yaml("output/k8s/topology.yaml", topology_yaml)

    print("Kubernetes manifests written to output/k8s/")

if __name__ == "__main__":
    main()
