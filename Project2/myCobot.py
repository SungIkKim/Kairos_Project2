import cv2
import numpy as np
import threading
import time
import random
from pymycobot import MyCobot


# 색상별 카운터
color_counter = {
    "Red": 0,
    "Blue": 0,
    "Yellow": 0,
    "Purple": 0
}

# 색상 범위 및 각 색상에 대한 딕셔너리 정의
color_ranges = {
    "Red": ([0, 120, 70], [10, 255, 255]),
    "Blue": ([100, 150, 0], [140, 255, 255]),
    "Yellow": ([20, 100, 100], [30, 255, 255]),
    "Purple": ([115, 50, 40], [160, 255, 255])  
}

# 색상별 글자 색 딕셔너리
color_dict = {
    "Red": (0, 0, 255),
    "Blue": (255, 0, 0),
    "Yellow": (0, 255, 255),
    "Purple": (128, 0, 128)
}

# 색상별 위치 딕셔너리
angles_dict = {
    "Red": [-30, -92, 40.5, -44, 90, -90],
    "Blue": [-45, -92, 40.5, -44, 90, -90],
    "Yellow": [-60, -92, 40.5, -44, 90, -90],
    "Purple": [-75, -92, 40.5, -44, 90, -90]
}


def change_angle(angles):
    angles[1] += 7
    angles[2] -= 3.3  
    angles[3] -= 2
    return angles

# 로봇제어 플래그
robot_moving = False

# 로봇 제어 함수
def control_robot(color, speed):
    global robot_moving
    robot_moving = True
    angles = angles_dict[color]
    cobot.set_color(128, 0, 128)

    print(f"Detect {color}")
    if color == "Red":
        cobot.set_color(255, 0, 0)
    elif color == "Blue":
        cobot.set_color(0, 0, 255)
    elif color == "Yellow":
        cobot.set_color(255, 255, 0)
    elif color == "Purple":
        cobot.set_color(128, 0, 128)
    time.sleep(1)
    
    print("Angle adjustment")
    cobot.send_angle(1, 10, 20)
    time.sleep(2)
    cobot.send_angle(2, -60, 20)
    time.sleep(2)

    print(f"Gripper Open1 {color} Position: {angles}, Speed: {speed}")
    cobot.set_gripper_value(100, 20, 1)
    time.sleep(2)

    print(f"Gripper Close1 {color} Position: {angles}, Speed: {speed}")
    cobot.set_gripper_value(15, 20, 1)
    time.sleep(2)

    print("robot moving")
    cobot.send_angles([0, 0, 0, 0, 0, 0], 60)
    time.sleep(4)

    if color_counter[color] > 0:
        new_angles = change_angle(angles)
        cobot.send_angles(new_angles, speed)
    else:
        cobot.send_angles(angles, speed)
    time.sleep(4)
  
    print(f"Gripper Open2 {color} Position: {angles}, Speed: {speed}")
    cobot.set_gripper_value(100, 20, 1)
    time.sleep(3)
    
    print("Come Back")
    cobot.set_color(255, 255, 255)
    cobot.send_angles([-5, -45, 25, -51, 90, -90], 60)
    time.sleep(4)
    
    color_counter[color] += 1

    robot_moving = False

# 색상 감지 함수
def detect_color(frame):
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for color, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv_frame, np.array(lower), np.array(upper))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            Area = cv2.contourArea(contour)
            if Area >= 250:
                cv2.rectangle(frame, (x, y), (x + w, y + h), color_dict[color], 2)
                cv2.putText(frame, color, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color_dict[color], 2)
                return color
    return None

# 비디오 프레임 처리 함수
def video_frame():
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Camera Error")
            break
        frame = cv2.resize(frame, (480, 480))
        detect_color_result = detect_color(frame)
        if detect_color_result and not robot_moving:
            # detect_color_result에 따라 로봇 제어 함수를 별도의 스레드로 실행
            control_thread = threading.Thread(target=control_robot, args=(detect_color_result, 60))
            control_thread.start()
       
        else:
            if detect_color_result is None:
                cv2.putText(frame, "None", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        #frame = cv2.resize(frame, (320, 240))
        cv2.imshow("Color Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    # mycobot 인스턴스 생성
    cobot = MyCobot("COM9", 115200)
    
    # 랜덤하게 하나의 색상 제외
    exclude_color = random.choice(list(color_ranges.keys()))
    del color_ranges[exclude_color]
    print(f"{exclude_color} except")

    # 초기 그리퍼 & 위치 설정
    cobot.set_gripper_calibration()
    cobot.set_gripper_mode(0)
    cobot.init_eletric_gripper()
    cobot.send_angles([-5, -45, 25, -51, 90, -90], 60)
    time.sleep(0.5)

    # 비디오 프레임 처리 함수를 별도의 스레드로 실행
    video_thread = threading.Thread(target=video_frame)
    video_thread.start()