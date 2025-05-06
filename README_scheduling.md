# Topology-Aware Scheduling in Kubernetes

## Overview

This document outlines the concept and exploration of a topology-aware custom scheduler tailored for SEED Emulator pods deployed via Kubernetes. The goal is to place pods in a manner that reflects their logical network topologies, such as AS relationships or link locality, thereby improving simulation realism and reducing inter-node latency.

## Motivation

By default, the Kubernetes scheduler assigns pods to nodes based on resource availability without regard to the intended network topology. However, in simulations that emulate realistic inter-AS routing and communication, physical pod placement can impact performance and complexity—particularly when emulating BGP, OSPF, or VXLAN-based systems using Meshnet.

## Objectives

- Understand and evaluate the limitations of the default Kubernetes scheduler for network simulations.
- Define node affinity rules that reflect Autonomous System (AS) groupings and router-host proximity.
- Investigate and prototype a custom scheduler that uses topology metadata to inform pod placement decisions.

## Approaches Considered

### 1. Node Affinity and Taints
- **Pros**: Simple and native to Kubernetes.
- **Cons**: Manual setup required; limited dynamic capability for large or evolving topologies.

### 2. Custom Kubernetes Scheduler
- **Pros**: Full control over scheduling decisions; supports advanced logic.
- **Cons**: Requires running a secondary scheduler; needs robust integration and testing.

### 3. DCM (Distributed Cloud Manager)-based Scheduling
- **Pros**: Rich metadata support; policy-driven.
- **Cons**: Additional complexity; may require integrating external systems.

## Status

- Initial exploration completed with node labeling and pod-level affinity rules.
- Future plans include parsing AS relationships from the SEED topology to auto-label nodes and generate topology-aware scheduling constraints programmatically from `Mesh.py`.

## Future Work

- Automate node labeling based on AS partitioning.
- Integrate scheduling preferences directly into manifest generation.
- Prototype and benchmark a custom scheduler using Kubernetes' extender interface or a standalone pod scheduler service.
