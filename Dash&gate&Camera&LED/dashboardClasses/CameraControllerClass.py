import tkinter as tk
from tkinter import font

class CameraController:

    def buildFrame(self, frame, MQTTClient):
        self.client = MQTTClient
        # Camera control label frame ----------------------
        self.cameraControlFrame = tk.LabelFrame(frame, text="Camera control", padx=5, pady=5)
        self.takePictureFrame = tk.Frame (self.cameraControlFrame)
        self.takePictureFrame.pack(side = tk.LEFT)


        takePictureButton = tk.Button(self.takePictureFrame, text="Take Picture", bg='red', fg="white", command=self.takePictureButtonClicked)
        takePictureButton.grid(column=0, row=0, pady = 5, padx = 5)

        self.panel = tk.Label(self.takePictureFrame,borderwidth=2, width = 50,bg = 'red', relief="raised")
        self.panel.grid(column=0, row=1, columnspan = 2, rowspan = 5)


        clearPictureButton = tk.Button(self.takePictureFrame, text="Clear picture",bg = 'red', fg="white", command=self.clearPictureButtonClicked)
        clearPictureButton.grid(column=1, row=0, pady = 5, padx = 5)


        self.videoStreamFrame = tk.Frame(self.cameraControlFrame)
        self.videoStreamFrame.pack()

        self.videoStream = False;



        self.videoStreamButton = tk.Button(self.videoStreamFrame, text="Start video stream \n on a separaded window", width=50, height = 25, bg='red', fg="white",
                                      command=self.videoStreamButtonClicked)
        myFont = font.Font(size=12)
        self.videoStreamButton['font'] = myFont
        self.videoStreamButton.grid(column=0, row=0, pady=20, padx=20, )
        return self.cameraControlFrame


    def takePictureButtonClicked(self):
        print("Take picture")
        self.client.publish("cameraControllerCommand/takePicture")

    def clearPictureButtonClicked(self):
        self.panel.destroy()
        self.panel = tk.Label(self.takePictureFrame, borderwidth=2, width=50, relief="raised")
        self.panel.grid(column=0, row=1, columnspan=2, rowspan=5)


    def videoStreamButtonClicked(self):
        if not self.videoStream:
            self.videoStreamButton['text'] = "Stop video stream"
            self.videoStreamButton['bg'] = "green"
            self.videoStream = True
            self.client.publish("cameraControllerCommand/startVideoStream")

        else:
            self.videoStreamButton['text'] = "Start video stream on a separaded window"
            self.videoStreamButton['bg'] = "red"
            self.videoStream = False
            self.client.publish("cameraControllerCommand/stopVideoStream")
            self.cv.destroyWindow("Stream")

    def putPicture (self,imgtk) :
        self.panel.destroy()
        self.panel = tk.Label(self.takePictureFrame, borderwidth=2, relief="raised")
        self.panel.imgtk = imgtk
        self.panel.configure(image=imgtk)
        self.panel.grid(column=0, row=1, rowspan=5, columnspan = 2)