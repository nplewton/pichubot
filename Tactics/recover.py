import melee
import globals
import Chains
import random
import math
from melee.enums import Action
from Chains.edgedash import Edgedash
from Chains.di import DI
from Chains.nothing import Nothing
from Chains.firefox import Firefox
from Chains.jump import Jump

from Chains.firefox import FIREFOX

class Recover():
    chain = None

    def pickchain(self, chain, args=[]):
        if type(self.chain) != chain:
            self.chain = chain(*args)
        self.chain.step()

    # Do we need to recover?
    def needsrecovery():
        smashbot_state = globals.smashbot_state
        opponent_state = globals.opponent_state

        onedge = smashbot_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING]
        opponentonedge = opponent_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING]

        if not opponent_state.off_stage and onedge:
            return True

        # If we're on stage, then we don't need to recover
        if not smashbot_state.off_stage:
            return False

        if smashbot_state.on_ground:
            return False

        # We can now assume that we're off the stage...

        # If opponent is dead
        if opponent_state.action in [Action.DEAD_DOWN, Action.DEAD_RIGHT, Action.DEAD_LEFT, \
                Action.DEAD_FLY, Action.DEAD_FLY_STAR, Action.DEAD_FLY_SPLATTER]:
            return True

        # If opponent is on stage
        if not opponent_state.off_stage:
            return True

        # If opponent is in hitstun, then recover, unless we're on the edge.
        if opponent_state.off_stage and opponent_state.hitstun_frames_left > 0 and not onedge:
            return True

        if opponent_state.action == Action.DEAD_FALL and opponent_state.y < -30:
            return True

        # If opponent is closer to the edge, recover
        diff_x_opponent = abs(melee.stages.edgeposition(globals.gamestate.stage) - abs(opponent_state.x))
        diff_x = abs(melee.stages.edgeposition(globals.gamestate.stage) - abs(smashbot_state.x))

        opponent_dist = math.sqrt( (opponent_state.y+15)**2 + (diff_x_opponent)**2 )
        smashbot_dist = math.sqrt( (smashbot_state.y+15)**2 + (diff_x)**2 )

        if opponent_dist < smashbot_dist and not onedge:
            return True

        return False

    def __init__(self):
        # We need to decide how we want to recover
        pass


    def step(self):
        smashbot_state = globals.smashbot_state
        opponent_state = globals.opponent_state

        # If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step()
            return

        if smashbot_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING]:
            self.pickchain(Edgedash)
            return

        diff_x = abs(melee.stages.edgeposition(globals.gamestate.stage) - abs(smashbot_state.x))

        # If we can just grab the edge with a firefox, do that
        facinginwards = smashbot_state.facing == (smashbot_state.x < 0)
        if not facinginwards and smashbot_state.action == Action.TURNING and smashbot_state.action_frame == 1:
            facinginwards = True

        if smashbot_state.action == Action.DEAD_FALL:
            x = 0
            if smashbot_state.x < 0:
                x = 1
            self.chain = None
            self.pickchain(DI, [x, 0.5])
            return

        # Are we facing the wrong way in shine? Turn around
        if smashbot_state.action == Action.DOWN_B_STUN and not facinginwards:
            x = 0
            if smashbot_state.x < 0:
                x = 1
            self.chain = None
            self.pickchain(DI, [x, 0.5])
            return

        # If we can just do nothing and grab the edge, do that
        if -12 < smashbot_state.y and (diff_x < 10) and facinginwards and smashbot_state.speed_y_self < 0:
            # Do a Fastfall if we're not already
            if smashbot_state.action == Action.FALLING and smashbot_state.speed_y_self > -3.3:
                self.chain = None
                self.pickchain(DI, [0.5, 0])
                return

            # If we are currently moving away from the stage, DI in
            if (smashbot_state.speed_air_x_self > 0) == (smashbot_state.x > 0):
                x = 0
                if smashbot_state.x < 0:
                    x = 1
                self.chain = None
                self.pickchain(DI, [x, 0.5])
                return
            else:
                self.pickchain(Nothing)
                return

        if (-15 < smashbot_state.y < -5) and (diff_x < 10) and facinginwards:
            self.pickchain(Firefox, [FIREFOX.MEDIUM])
            return

        # First jump back to the stage if we're low
        if smashbot_state.jumps_left > 0 and smashbot_state.y < -20:
            self.pickchain(Jump)
            return

        # Don't firefox if we're super high up, wait a little to come down
        if smashbot_state.speed_y_self < 0 and smashbot_state.y < 30:
            self.pickchain(Firefox)
            return

        # DI into the stage
        x = 0
        if smashbot_state.x < 0:
            x = 1
        self.chain = None
        self.pickchain(DI, [x, 0.5])
