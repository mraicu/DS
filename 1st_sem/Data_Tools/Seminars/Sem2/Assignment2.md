#### Installation Log - Date: 02.11.2025

**Environment:**

-   Operating System: Linux - Pop!\_OS 22.04 LTS (jammy)
-   **CPU:** Intel Core Ultra 7 255HX (20 cores)
-   **GPU:** NVIDIA GeForce RTX 5070 (≈12 GB VRAM)
-   **Python Version:** 3.13.5

**Prerequisites:**

-   **GPU Drivers:** 570.133.07
-   **CUDA:** 12.8
-   **cuDNN:** Not detected system-wide (`/usr/include/cudnn_version.h` missing). Will install/provide via Conda during environment setup (e.g., `conda install cudnn`) or record version after installation.

**Python Installation (via Miniconda)**
**Step 1: Download Miniconda Installer**

```sh
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

**Step 2: Run the Installer**
Execute the installer script:

```sh
bash Miniconda3-latest-Linux-x86_64.sh
```

-   Accept the license terms.
-   Choose an installation path.
-   **Allow the installer to initialize Miniconda** when prompted.
    **Step 3: Update Conda**

```sh
conda update -n base -c defaults conda
```

**Step 4: Create a New Environment for PyTorch**

```sh
conda create -n pytorch_env python=3.10
```

**PyTorch Installation:**  
**Step 1: Activate Your Conda Environment**

```sh
conda activate pytorch_env
```

**Step 2: Install PyTorch with CUDA Support**

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

```

**CUDA Configuration:**
When i installed PyTorch using a command like:

`pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`

a **prebuilt wheel** was downloaded that already includes:

-   The correct **CUDA runtime libraries**
-   The correct **cuDNN**
-   All dependencies needed to use your GPU
    So, I **don’t need a separate system CUDA installation or configuration**

**Error Log:**

1. **Error 1: CUDA Driver/Runtime Mismatch (new GPU not supported by stable wheel)**

-   **Error Message:**
    `` RuntimeError: CUDA error: CUDA-capable device(s) is/are busy or unavailable CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect. For debugging consider passing CUDA_LAUNCH_BLOCKING=1 Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions. ``
-   **Occurred during:**  
    `import torch`
-   **Troubleshooting Attempted:**
    -   Verified driver & GPU were recognized:
        `nvidia-smi   # showed Driver Version: 570.133.07, CUDA Version: 12.8, RTX 5070 visible`
    -   Confirmed PyTorch build info (failed on CUDA use):
        `python - <<'PY' import torch print("torch:", torch.__version__) print("torch.version.cuda:", torch.version.cuda)  # e.g., 12.1 from cu121 wheels print("CUDA available:", torch.cuda.is_available())  # was False / raised error on use PY`
    -   Ensured no conflicting Conda CUDA packages (none installed).
    -   Considered device “busy” causes (checked running processes with `nvidia-smi`), issue persisted.
    -   Hypothesis: **stable cu121 wheel lacked support for the newer RTX 50-series/driver combo** on this system; needed a newer CUDA runtime build.
-   **Solution:**  
     Upgraded PyTorch to the **nightly CUDA 12.8** wheel, which includes newer GPU/driver support:
    `pip install --pre --upgrade --no-cache-dir torch \   --extra-index-url https://download.pytorch.org/whl/nightly/cu128`
