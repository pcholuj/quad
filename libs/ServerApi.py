class Api : 
    def __init__(self, parent):
        self.parent = parent
    def testMotorSpeed(self, speed) :
        print speed
        for esc in self.parent.getEscList():
            esc.update(speed)