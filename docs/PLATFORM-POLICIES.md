# Hosted notebook platform policies — research snapshot

Research date: 2026-10-11. This is a short operational summary, not legal advice. The user is responsible for checking and complying with the platform's current terms, content policies, quotas, and model license before running a workload. Platform interfaces and policy pages can change.

## Kaggle Notebooks

The official notebook documentation describes notebooks as hosted computational environments with optional accelerators and a session setting for Internet. It documents limited free GPU availability and session/disk constraints; actual availability varies. The reviewed documentation explains the notebook environment and GPU settings, but does **not** explicitly guarantee that every video-generation model or workload is allowed. Therefore, model-specific or content-specific permissibility is **UNVERIFIED** and must be checked against the current Kaggle Terms of Service, community rules, and any competition/dataset rules before use. Do not assume a GPU quota or session duration.

Official references:
- https://www.kaggle.com/docs/notebooks
- https://www.kaggle.com/docs/efficient-gpu-usage
- https://www.kaggle.com/terms

## Google Colab

The official FAQ says GPU availability and resource limits are not guaranteed and can fluctuate. It expressly prohibits deepfakes in managed runtimes, and lists several disallowed uses such as file hosting/media serving and certain remote-control or web-UI workloads. The bundle worker is designed for interactive notebook compute and manual file transfer, not serving a website or exposing an endpoint. Whether a particular prompt, generated video, model, or use case complies is **UNVERIFIED**; the user must review the current FAQ and terms before running it. Do not use this workflow for deepfakes or other prohibited uses.

Official references:
- https://research.google.com/colaboratory/faq.html
- https://research.google.com/colaboratory/tos_v3.html

## User responsibility

The application does not grant permission to use hosted GPU services, model weights, input images, or generated outputs. The user is responsible for platform terms, copyright/privacy rights in inputs, model license obligations, export/sanctions restrictions, and permitted output use. If uncertain, do not upload the bundle.
