import melee
import globals

class Nothing():
    def step(self):
        globals.controller.empty_input()
        self.interruptible = True
