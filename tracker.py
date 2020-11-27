"""
物体追踪
需要安装包：opencv-contrib-python,openpyxl,json
"""
import math
import sys
import os
import json
import cv2
import numpy as np
from retrying import retry
from openpyxl import Workbook
print("物体追踪-判断角速度 by tjc\n框选两点完成后摁esc开始追踪")
try:
    with open("./setting.json", "r") as load_f:
        SETTING = json.load(load_f)
except IOError:
    print("未找到设置文件，程序退出")
    os.system('pause')
    sys.exit()
REAL_FPS=SETTING['real_fps']
VIDEO_PATH=SETTING['video_path']
EXCEL_FILE_PATH=SETTING['excel_file_path']
vid=cv2.VideoCapture(VIDEO_PATH)
TIME_PRE_FRAME=1/REAL_FPS
CAL_CEN_STEP=SETTING['cal_cen_step']
CAL_MOVE_V_STEP=SETTING['cal_move_v_step']
vid_height=int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
vid_width=int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
tracker1=cv2.TrackerCSRT_create()
tracker2=cv2.TrackerCSRT_create()
success,frame=vid.read()
if not success:
    print("视频读取失败,退出程序")
    os.system('pause')
    sys.exit()
cv2.imshow("A",frame)
roi=cv2.selectROIs("A",frame)
tracker1.init(frame,tuple(roi[0]))
tracker2.init(frame,tuple(roi[1]))
point1_list=[]
point2_list=[]
rot_v_list=[]
time_list=[]
FLAG=True
while True:
    success,frame=vid.read()
    if success:
        frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        success1,box1=tracker1.update(frame)
        success2,box2=tracker2.update(frame)
        if success1&success2:
            start1=(int(box1[0]),int(box1[1]))
            end1=(int(box1[0]+box1[2]),int(box1[1]+box1[3]))
            start2=(int(box2[0]),int(box2[1]))
            end2=(int(box2[0]+box2[2]),int(box2[1]+box2[3]))
            frame_cp=frame.copy()
            cv2.rectangle(frame,start1,end1,(255,255,255))
            cv2.rectangle(frame,start2,end2,(0,0,0))
            x1_value,y1_value=box1[0]+box1[2]/2,box1[1]+box1[3]/2
            x2_value,y2_value=box2[0]+box2[2]/2,box2[1]+box2[3]/2
            if len(point1_list)>=CAL_CEN_STEP:
                deno_x=(2*(point2_list[-CAL_CEN_STEP][0]*(point1_list[-CAL_CEN_STEP][1]-y1_value)+x2_value*(-point1_list[-CAL_CEN_STEP][1]+y1_value)-(point1_list[-CAL_CEN_STEP][0]-x1_value)*(point2_list[-CAL_CEN_STEP][1]-y2_value)))
                deno_y=(2*(x2_value*(point1_list[-CAL_CEN_STEP][1]-y1_value)+point2_list[-CAL_CEN_STEP][0]*(-point1_list[-CAL_CEN_STEP][1]+y1_value)+(point1_list[-CAL_CEN_STEP][0]-x1_value)*(point2_list[-CAL_CEN_STEP][1]-y2_value)))
                if deno_x:
                    rot_center_x=(point2_list[-CAL_CEN_STEP][0]**2*(point1_list[-CAL_CEN_STEP][1]-y1_value)+x2_value**2*(-point1_list[-CAL_CEN_STEP][1]+y1_value)+(-point1_list[-CAL_CEN_STEP][0]**2+x1_value**2-(point1_list[-CAL_CEN_STEP][1]-y1_value)*(point1_list[-CAL_CEN_STEP][1]-point2_list[-CAL_CEN_STEP][1]+y1_value-y2_value))*(point2_list[-CAL_CEN_STEP][1]-y2_value))/deno_x
                    rot_center_y=((x1_value)**2*(point2_list[-CAL_CEN_STEP][0]-x2_value)+(point1_list[-CAL_CEN_STEP][0])**2*(-point2_list[-CAL_CEN_STEP][0]+x2_value)-(point2_list[-CAL_CEN_STEP][0]-x2_value)*((point1_list[-CAL_CEN_STEP][1])**2-(y1_value)**2)+point1_list[-CAL_CEN_STEP][0]*((point2_list[-CAL_CEN_STEP][0])**2+(point2_list[-CAL_CEN_STEP][1])**2-(x2_value)**2-(y2_value)**2)+x1_value*(-(point2_list[-CAL_CEN_STEP][0])**2-(point2_list[-CAL_CEN_STEP][1])**2+(x2_value)**2+(y2_value)**2))/deno_y
                else:
                    try:
                        rot_center_x=pre_rot_center_x
                        rot_center_y=pre_rot_center_y
                    except NameError:
                        cv2.imshow("A",frame)
                        if cv2.waitKey(1) & 0xff == ord('q'):
                            break
                        continue
                cv2.circle(frame,(int(rot_center_x),int(rot_center_y)),20,(255,255,255))
                pre_rot_center_x=rot_center_x
                pre_rot_center_y=rot_center_y
                rot_r=math.hypot(x1_value-rot_center_x,y1_value-rot_center_y)
                move_v=math.hypot(x1_value-point1_list[-CAL_MOVE_V_STEP][0],y1_value-point1_list[-CAL_MOVE_V_STEP][1])/(CAL_MOVE_V_STEP*TIME_PRE_FRAME)
                ROT_V=move_v/rot_r
                text_size,baseline=cv2.getTextSize("Angular velocity="+str(format(ROT_V,'0.4f'))+"rad/s",cv2.FONT_HERSHEY_COMPLEX,0.5,1)
                cv2.putText(frame,"Angular velocity="+str(format(ROT_V,'0.4f'))+"rad/s",(vid_width-text_size[0],text_size[1]),cv2.FONT_HERSHEY_COMPLEX,0.5,(255,255,255))
                #裁剪center 寻找长度
                # cv2.imshow("center",frame_cp[int(rot_center_y)-SQUARE_LEN//2:int(rot_center_y)+SQUARE_LEN//2,int(rot_center_x)-SQUARE_LEN//2:int(rot_center_x)+SQUARE_LEN//2])
            else:
                ROT_V=0
            rot_v_list.append(ROT_V)
            point1_list.append((x1_value,y1_value))
            point2_list.append((x2_value,y2_value))
            time_list.append(vid.get(cv2.CAP_PROP_POS_FRAMES)*TIME_PRE_FRAME)
        elif not (success1 or success2):
            if FLAG:
                print("丢失1号及2号点位，您希望\n1.手动取点,此点不作为下一帧参考\n2.手动取点,此点作为下一帧参考\n3.跳过此帧\n4.全部跳过")
                choose=input()
                if choose=='1':
                    roi=cv2.selectROIs("A",frame)
                    point1_list.append((roi[0][0],roi[0][1]))
                    point2_list.append((roi[1][0],roi[1][1]))
                elif choose=='2':
                    roi=cv2.selectROIs("A",frame)
                    tracker1=cv2.TrackerKCF_create()
                    tracker2=cv2.TrackerKCF_create()
                    tracker1.init(frame,tuple(roi[0]))
                    tracker2.init(frame,tuple(roi[1]))
                    point1_list.append((roi[0][0],roi[0][1]))
                    point2_list.append((roi[1][0],roi[1][1]))
                elif choose=="4":
                    FLAG=False
        elif not success1:
            start2=(int(box2[0]),int(box2[1]))
            end2=(int(box2[0]+box2[2]),int(box2[1]+box2[3]))
            frame_cp=frame.copy()
            cv2.rectangle(frame,start2,end2,(0,255,255))
            if FLAG:
                print("丢失1号点位，您希望\n1.手动取点,此点不作为下一帧参考\n2.手动取点,此点作为下一帧参考\n3.跳过此帧\n4.全部跳过")
                choose=input()
                if choose=='1':
                    roi=cv2.selectROI("A",frame)
                    point1_list.append((roi[0],roi[1]))
                elif choose=='2':
                    roi=cv2.selectROI("A",frame)
                    tracker1=cv2.TrackerKCF_create()
                    tracker1.init(frame_cp,tuple(roi))
                    point1_list.append((roi[0],roi[1]))
                elif choose=="4":
                    FLAG=False
        elif not success2:
            start1=(int(box1[0]),int(box1[1]))
            end1=(int(box1[0]+box1[2]),int(box1[1]+box1[3]))
            frame_cp=frame.copy()
            cv2.rectangle(frame,start1,end1,(255,255,255))
            if FLAG:
                print("丢失2号点位，您希望\n1.手动取点,此点不作为下一帧参考\n2.手动取点,此点作为下一帧参考\n3.跳过此帧\n4.全部跳过")
                choose=input()
                if choose=='1':
                    roi=cv2.selectROI("A",frame)
                    point2_list.append((roi[0],roi[1]))
                elif choose=='2':
                    roi=cv2.selectROI("A",frame)
                    tracker2=cv2.TrackerKCF_create()
                    tracker2.init(frame_cp,tuple(roi))
                    point2_list.append((roi[0],roi[1]))
                elif choose=="4":
                    FLAG=False
        cv2.imshow("A",frame)
        key=cv2.waitKey(1)
        if (key & 0xff == ord('q')) or (key & 0xff == ord('Q')):
            cv2.destroyAllWindows()
            print("用户终止，程序退出")
            os.system('pause')
            sys.exit()
    else:
        break
cv2.destroyAllWindows()
print("开始保存")
point1_x_list=np.array(point1_list)[:,0]
point1_y_list=np.array(point1_list)[:,1]
point2_x_list=np.array(point2_list)[:,0]
point2_y_list=np.array(point2_list)[:,1]
data=np.vstack((time_list,point1_x_list,point1_y_list,point2_x_list,point2_y_list,rot_v_list))
wb=Workbook()
ws1 = wb.active
ws1.title = "v"
ws1.append(("时间","点1 x坐标","点1 y坐标","点2 x坐标","点2 y坐标","角速度"))
for i in data.T:
    ws1.append(i.tolist())
def if_retry(unused_excepton):
    """检测是否该重试"""
    yes_no=input("保存excel失败，可能文件已被打开或权限不足，输入Y重试，输入其他退出\n")
    return yes_no in ('y','Y')
@retry(retry_on_exception=if_retry)
def save_excel():
    """保存excel"""
    print("正在写入")
    wb.save(filename = EXCEL_FILE_PATH)
save_excel()
print("程序结束")
os.system('pause')
