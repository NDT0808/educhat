# 🧭 ORB-SLAM3 Control Panel (Advanced IPC & Safe Checkpointing)

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![C++](https://img.shields.io/badge/C++-11%2F14-00599C?style=for-the-badge&logo=c%2B%2B)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv)
![Ubuntu](https://img.shields.io/badge/WSL-Ubuntu_20.04-E95420?style=for-the-badge&logo=ubuntu)

An advanced, intuitive Graphical User Interface (GUI) and Inter-Process Communication (IPC) wrapper designed to control the **ORB-SLAM3** C++ core securely. This project solves critical multi-threading crashes and memory management issues inherent in the original SLAM implementation, providing a stable environment for visual odometry testing.

<img width="1916" height="907" alt="Educhat_img" src="https://github.com/user-attachments/assets/36efea3c-d66f-4b6f-a153-6b91a9258dc9" />

<p align="center">
  <img src="https://github.com/user-attachments/assets/..." width="750" alt="ORB-SLAM3 GUI Interface">
</p>

## 🌟 Key Features

* **Soft Pause (Tạm Dừng Mềm):** Utilizes `SIGUSR2` signals to halt the C++ tracking loop dynamically. This freezes the camera and 3D map in RAM perfectly without killing the OS process, preventing coordinate drift.
* **Midway Checkpointing (Lưu Chặng):** Employs `SIGUSR1` to extract 3D trajectory data (`.txt`) in real-time. Users can save multiple path segments (Checkpoints) while the vehicle is either paused or actively moving, without losing Map spatial consistency.
* **Crash-Proof Shutdown (Bảo Toàn Dữ Liệu):** Overcomes the notorious ORB-SLAM3 `Shutdown()` segmentation fault. The system orchestrates an automated 3-step stop sequence (Brake -> Save -> Kill) to ensure trajectory files are fully written to the disk before safely terminating the C++ threads.
* **Auto-Sync Dataset Manager:** Validates and mounts KITTI sequences from the host OS directly to the WSL environment dynamically.

## 🛠️ Technology Stack

* **Core Algorithms:** C++, ORB-SLAM3, Eigen3
* **Computer Vision:** OpenCV
* **GUI Framework:** Python, CustomTkinter
* **System Architecture:** POSIX Signals (IPC), Subprocess Threading, Linux (WSL)

## 📂 Project Structure

```text
ORB_SLAM3_Control/
├── slam_gui.py                 # Core Python GUI & Subprocess Manager
├── KITTI00-02.yaml             # Camera calibration parameters
├── Examples/
│   └── Stereo/
│       └── stereo_kitti.cc     # Modified C++ Core (Integrated Signal Handlers)
└── README.md



