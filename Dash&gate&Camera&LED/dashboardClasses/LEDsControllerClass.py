import tkinter as tk
class LEDsController:

    def buildFrame(self, frame, MQTTClient):
        self.client = MQTTClient
        self.ledsControlFrame = tk.LabelFrame(frame, text="LEDs control", padx=5, pady=5)

        self.v = tk.StringVar()
        s1r7 = tk.Radiobutton(self.ledsControlFrame, text="LED sequence START/STOP", variable=self.v, value=1).grid(
            column=2,
            row=2,
            columnspan=3)
        s1r8 = tk.Radiobutton(self.ledsControlFrame, text="LED sequence for N seconds", variable=self.v, value=2).grid(
            column=2,
            row=3,
            columnspan=3)

        self.seconds = tk.Entry(self.ledsControlFrame, width=5)
        self.seconds.grid(column=5, row=3, columnspan=3)
        self.v.set(1)

        self.lEDSequence = False;

        self.ledControlButton = tk.Button(self.ledsControlFrame, text="Start", bg='red', fg="white", width=10, height=3,
                                          command=self.LEDControlButtonClicked)
        self.ledControlButton.grid(column=8, row=1, padx=5, columnspan=4, rowspan=3)
        return self.ledsControlFrame

    def LEDControlButtonClicked(self):
        if self.v.get() == "1":
            if not self.lEDSequence:
                self.ledControlButton['text'] = "Stop"
                self.ledControlButton['bg'] = "green"
                self.lEDSequence = True
                self.client.publish("LEDsControllerCommand/startLEDsSequence")

            else:
                self.ledControlButton['text'] = "Start"
                self.ledControlButton['bg'] = "red"
                lEDSequence = False
                self.client.publish("LEDsControllerCommand/stopLEDsSequence")

        if self.v.get() == "2":
                self.client.publish("LEDsControllerCommand/LEDsSequenceForNSeconds", self.seconds.get())

