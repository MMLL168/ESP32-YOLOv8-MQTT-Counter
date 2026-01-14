# Project: AIoT People Counter with YOLOv8 & MQTT
# Description: Real-time people counting with pose estimation, sending data via MQTT WSS (Port 443).

from ultralytics import YOLO
import cv2
import time
import json
import ssl
import paho.mqtt.client as mqtt

# --- 新增：處理中文顯示需要的庫 ---
from PIL import Image, ImageDraw, ImageFont
import numpy as np
# ------------------------------

# ================= 參數設定 =================
CONF_THRESHOLD = 0.5  # 信心門檻
# ===========================================

# ================= MQTT 連線資訊 (請自行填入) =================
# Security Note: Do not commit real credentials to GitHub!
# 請將下方的 ****** 替換為您自己的 Broker 資訊
MQTT_BROKER = "******"      # 例如: public.cloud.shiftr.io
MQTT_PORT = 443             # 通常為 443 (WSS) 或 8883 (MQTTS)
MQTT_PATH = "/mqtt"         # WebSocket 路徑
MQTT_TOPIC = "******"       # 例如: my_project/count
MQTT_USER = "******"        # MQTT 使用者名稱
MQTT_PASSWORD = "******"    # MQTT 密碼

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, transport='websockets')
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
client.tls_set_context(context)

client.ws_set_options(path=MQTT_PATH)

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print(f">>> MQTT 連線成功! ({MQTT_BROKER}:{MQTT_PORT})")
    else:
        print(f">>> 連線失敗, 代碼: {rc}")

client.on_connect = on_connect

try:
    print(f"正在連線至 {MQTT_BROKER}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
except Exception as e:
    print(f"MQTT 連線錯誤: {e}")
# =======================================================

cv2.namedWindow('YOLOv8', cv2.WINDOW_NORMAL)

# 載入模型
model = YOLO('yolov8s-pose.pt') 
names = model.names
print(names)

# ================= 影像來源設定 =================
# 請將 ****** 替換為您的 ESP32-CAM 串流網址或是 WebCam 編號 (0)
video_source = "******"  # 例如: http://192.168.1.100:81/stream
cap = cv2.VideoCapture(video_source)
# ===============================================

# --- 設定中文字型 (依據作業系統調整路徑) ---
# Windows 預設路徑範例
fontPath = "C:/Windows/Fonts/msjh.ttc" 
try:
    font = ImageFont.truetype(fontPath, 40)
except:
    font = ImageFont.load_default()
    print("找不到指定字型，將使用預設字體")
# ------------------------------------------

last_send_time = 0
send_interval = 1.0 

while 1:
    st = time.time()  
    r, frame = cap.read()
    if r == False:
        print("無法讀取影像，嘗試重連中...")
        time.sleep(2)
        try:
            cap = cv2.VideoCapture(video_source)
        except:
            pass
        continue
    
    # 取得畫面寬度 (用於靠右對齊計算)
    h, w, _ = frame.shape

    # 推論
    results = model(frame, verbose=False, conf=CONF_THRESHOLD)

    personcount = 0
    p_id = 1 

    if results[0].boxes:
        for box in results[0].boxes.data:
            if len(box) >= 6:
                x1 = int(box[0])
                y1 = int(box[1])
                x2 = int(box[2])
                y2 = int(box[3])
                
                r_conf = float(box[4]) 
                cls_id = int(box[5])
                n = names[cls_id]
                
                if n in ['person']:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    label_name = f"pson{p_id}"
                    cv2.putText(frame, label_name, (x1, y1), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                    
                    conf_text = f"{r_conf:.2f}"
                    (text_w, text_h), _ = cv2.getTextSize(conf_text, cv2.FONT_HERSHEY_PLAIN, 2, 2)
                    
                    # 右上角顯示信心度 (橘色)
                    cv2.putText(frame, conf_text, (x2 - text_w, y1), cv2.FONT_HERSHEY_PLAIN, 2, (0, 165, 255), 2)
                    
                    personcount += 1
                    p_id += 1

    frame = results[0].plot(boxes=False, labels=False, probs=False, img=frame)

    # MQTT 發送邏輯
    current_time = time.time()
    if current_time - last_send_time > send_interval:
        current_fps = int(1/(time.time()-st)) if (time.time()-st) > 0 else 0
        payload = {
            "count": personcount,
            "fps": current_fps,
            "ts": current_time
        }
        try:
            if client.is_connected():
                client.publish(MQTT_TOPIC, json.dumps(payload))
        except Exception as e:
            print(f"發送失敗: {e}")
        last_send_time = current_time

    et = time.time()
    FPS = int(1/(et-st)) if (et-st) > 0 else 0 

    # ================= 介面顯示區 (右上角) =================
    
    # 1. 顯示 FPS
    fps_str = 'FPS=' + str(FPS)
    (fps_w, fps_h), _ = cv2.getTextSize(fps_str, cv2.FONT_HERSHEY_PLAIN, 2, 2)
    fps_x = w - fps_w - 20
    fps_y = 50
    cv2.putText(frame, fps_str, (fps_x, fps_y), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)

    # 2. 顯示 "偵測人數" (中文)
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    count_str = f"偵測人數: {personcount}"
    
    left, top, right, bottom = draw.textbbox((0, 0), count_str, font=font)
    txt_w = right - left
    txt_h = bottom - top
    
    count_x = w - txt_w - 20
    count_y = 100 
    
    draw.text((count_x, count_y), count_str, font=font, fill=(255, 0, 0))
    
    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    # ===========================================================
    
    cv2.imshow('YOLOv8', frame)
    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
