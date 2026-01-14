# ESP32 YOLOv8 AIoT People Counter 🚀

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![YOLOv8](https://img.shields.io/badge/AI-YOLOv8_Pose-green)
![MQTT](https://img.shields.io/badge/Protocol-MQTT_WSS-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

一個整合 **ESP32-CAM 影像串流** 與 **YOLOv8 姿態辨識** 的即時人數統計系統。本專案具備強大的網路適應性，利用 **MQTT over WebSocket (Port 443)** 技術，能夠穿透嚴格的公司/校園防火牆，將辨識數據即時傳送至雲端與遠端監控儀表板。

## ✨ 核心功能 (Key Features)

* **📷 邊緣視覺串流**: 接收來自 ESP32-CAM (或其他 IP Camera) 的 HTTP 影像流。
* **🧠 AI 骨架辨識**: 採用 `Ultralytics YOLOv8-Pose` 模型，精準辨識人體骨架，排除非人體誤判。
* **🛡️ 防火牆穿透技術**: 使用 **MQTT over WebSockets (WSS)** 經由 **Port 443** 傳輸，解決內網封鎖非標準 Port (1883) 的問題。
* **🔢 智慧計數與過濾**:
    * 自定義信心門檻 (Confidence Threshold > 0.5)。
    * 自動編號追蹤 (Person ID)。
    * 即時過濾低信心度物件。
* **🎨 視覺化介面**:
    * 支援 **中文顯示** (PIL 整合)，解決 OpenCV 無法顯示中文的問題。
    * 動態資訊疊加：右上角即時顯示 FPS 與偵測人數。
    * 彩色標註：綠色偵測框、橘色信心度、紅色 ID。
* **☁️ 雲端遙測**: 數據即時上傳至 `Shiftr.io` (或其他 MQTT Broker)，可對接 Node-RED 或其他戰情室系統。

## 🏗️ 系統架構 (Architecture)

```mermaid
graph LR
    A[ESP32-CAM] -- HTTP Stream --> B(Laptop / Edge Device)
    B -- YOLOv8 Inference --> B
    B -- MQTT WSS (Port 443) --> C[Shiftr.io Cloud Broker]
    C --> D[Remote Client / Node-RED]
