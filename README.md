# DS252 — Introduction to Cloud Computing

**Department of Computational and Data Sciences (CDS)**  
**Indian Institute of Science (IISc), Bengaluru**

**Course code:** DS 252 · **Credits:** 3:1 · **Semester:** Aug 2025

**Course page:** [https://cds.iisc.ac.in/courses/ds252/](https://cds.iisc.ac.in/courses/ds252/)

---

## Course Overview

This repository contains the laboratory materials, tutorials, and supporting artifacts for **DS252 — Introduction to Cloud Computing**, offered by the Department of Computational and Data Sciences at the Indian Institute of Science. The course covers virtualization and distributed architectures, cloud service models (IaaS/PaaS/SaaS), cloud storage, serverless and orchestration, DevOps and observability, and emerging topics such as MLOps and the edge–cloud continuum. The labs provide hands-on experience with virtualization, containerization, serverless and hybrid cloud architectures, Kubernetes, observability, and MLOps on modern cloud platforms.

---

## Repository Structure

The repository is organized by lab session. Each directory corresponds to a scheduled lab and includes README files, scripts, and configuration as needed.

| Lab Session   | Topic |
|---------------|--------|
| **lab-session1-2208** | Ubuntu VM setup, Docker, KVM; resource profiling (bare metal, VM, Docker) |
| **lab-session2-2908** | Cloud account setup (AWS, Azure), CLI installation, Flask server basics |
| **lab-session3-1709** | S3 versioning and lifecycle; ECS (EC2) with ALB; autoscaling; JMeter load testing; FinOps (tagging, budgets) |
| **lab-session4-2609** | Serverless workflows: Lambda ingestion, Step Functions (preprocessing, ML inference, aggregation) |
| **lab-session5-0310** | Amazon EKS: Kubernetes cluster deployment and scaling |
| **lab-session6-1710** | Hybrid architecture with Terraform: Lambda, EC2 (Flask), S3 |
| **lab-session7-2410** | IAM (IRSA), OpenTelemetry, Prometheus, and Grafana on EKS |
| **lab-session8-3110** | Kubeflow MLOps: Feast, KServe, drift monitoring on AWS EKS |
| **lab-session9-1411** | K3s edge computing: lightweight Kubernetes on EC2 |

---

## Prerequisites

- An active **AWS account** (and optionally **Azure**) with CLI configured; billing may apply beyond free tier.
- **Ubuntu 22.04** (bare metal or VM) for labs and consistent environment across labs.
- Basic familiarity with the command line, Python, and Git.

Specific tools (Docker, Terraform, AWS SAM, kubectl, Helm, etc.) are documented in each lab’s README.

---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/dream-lab/ds252-2025.git
   cd ds252-2025
   ```

2. **Follow lab order**  
   Labs are intended to be done in sequence; later sessions may depend on resources or concepts from earlier ones (e.g., EKS from Lab 5 is reused in Labs 7 and 8).

3. **Use per-lab READMEs**  
   Each `lab-session*` directory contains a README (and sometimes STEPS or TUTORIAL files) with prerequisites, setup, and instructions for that session.

---

## More Information

Course content and lab materials are provided for educational use at the Indian Institute of Science (Department of Computational and Data Sciences). Please refer to the [course page](https://cds.iisc.ac.in/courses/ds252/) for more information.
