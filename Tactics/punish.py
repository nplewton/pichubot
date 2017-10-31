import melee
import globals
import Chains
import math
from melee.enums import Action, Button, Character
from Chains.smashattack import SMASH_DIRECTION
from Chains.shffl import SHFFL_DIRECTION
from Chains.nothing import Nothing
from Chains.smashattack import SmashAttack
from Chains.shffl import Shffl
from Chains.wavedash import Wavedash
from Chains.dashdance import DashDance

class Punish():
    chain = None

    def pickchain(self, chain, args=[]):
        if type(self.chain) != chain:
            self.chain = chain(*args)
        self.chain.step()

    # How many frames do we have to work with for the punish
    def framesleft():
        opponent_state = globals.opponent_state

        # For some dumb reason, the game shows the standing animation as having a large hitstun
        #   manually account for this
        if opponent_state.action == Action.STANDING:
            return 1

        # Shine wait
        if opponent_state.character in [Character.FOX, Character.FALCO]:
            if opponent_state.action in [Action.SWORD_DANCE_2_MID_AIR, Action.SWORD_DANCE_3_HIGH_AIR, Action.SWORD_DANCE_3_LOW_AIR]:
                return 3

        if opponent_state.action == Action.LOOPING_ATTACK_MIDDLE:
            return 1

        # Is opponent attacking?
        if globals.framedata.isattack(opponent_state.character, opponent_state.action):
            # What state of the attack is the opponent in?
            # Windup / Attacking / Cooldown
            attackstate = globals.framedata.attackstate_simple(opponent_state)
            if attackstate == melee.enums.AttackState.WINDUP:
                # Don't try to punish opponent in windup when they're invulnerable
                if opponent_state.invulnerability_left > 0:
                    return 0
                # Don't try to punish standup attack windup
                if opponent_state.action in [Action.GROUND_ATTACK_UP, Action.GETUP_ATTACK]:
                    return 0
                frame = globals.framedata.firsthitboxframe(opponent_state.character, opponent_state.action)
                return max(0, frame - opponent_state.action_frame - 1)
            if attackstate == melee.enums.AttackState.ATTACKING:
                return 0
            if attackstate == melee.enums.AttackState.COOLDOWN:
                frame = globals.framedata.iasa(opponent_state.character, opponent_state.action)
                return max(0, frame - opponent_state.action_frame)
        if globals.framedata.isroll(opponent_state.character, opponent_state.action):
            frame = globals.framedata.lastrollframe(opponent_state.character, opponent_state.action)
            return max(0, frame - opponent_state.action_frame)

        # Opponent is in hitstun
        if opponent_state.hitstun_frames_left > 0:
            # Special case here for lying on the ground.
            #   For some reason, the hitstun count is totally wrong for these actions
            if opponent_state.action in [Action.LYING_GROUND_UP, Action.LYING_GROUND_DOWN]:
                return 1

            # If opponent is in the air, we need to cap the retun at when they will hit the ground
            if opponent_state.y > .02 or not opponent_state.on_ground:
                # When will they land?
                speed = opponent_state.speed_y_attack + opponent_state.speed_y_self
                height = opponent_state.y
                gravity = globals.framedata.characterdata[opponent_state.character]["Gravity"]
                termvelocity = globals.framedata.characterdata[opponent_state.character]["TerminalVelocity"]
                count = 0
                while height > 0:
                    height += speed
                    speed -= gravity
                    speed = max(speed, -termvelocity)
                    count += 1
                    # Shortcut if we get too far
                    if count > 120:
                        break
                return count

            return opponent_state.hitstun_frames_left

        # Opponent is in a lag state
        if opponent_state.action in [Action.UAIR_LANDING, Action.FAIR_LANDING, \
                Action.DAIR_LANDING, Action.BAIR_LANDING, Action.NAIR_LANDING]:
            # TODO: DO an actual lookup to see how many frames this is
            return 9 - (opponent_state.action_frame // 3)


        # Opponent is in a B move
        if globals.framedata.isbmove(opponent_state.character, opponent_state.action):
            return globals.framedata.lastframe(opponent_state.character, opponent_state.action) - opponent_state.action_frame

        return 1

    # Static function that returns whether we have enough time to run in and punish,
    # given the current gamestate. Either a shine or upsmash
    def canpunish():
        opponent_state = globals.opponent_state

        # Can't punish opponent in shield
        shieldactions = [Action.SHIELD_START, Action.SHIELD, Action.SHIELD_RELEASE, \
            Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        if opponent_state.action in shieldactions:
            return False

        if globals.smashbot_state.off_stage:
            return False

        firefox = opponent_state.action == Action.SWORD_DANCE_3_LOW and opponent_state.character in [Character.FOX, Character.FALCO]
        if firefox and opponent_state.y > 15:
            return False

        left = Punish.framesleft()
        # Will our opponent be invulnerable for the entire punishable window?
        if left <= opponent_state.invulnerability_left:
            return False

        if left < 1:
            return False

        if globals.framedata.isroll(opponent_state.character, opponent_state.action):
            return True

        # Can we shine right now without any movement?
        downsmashablestate = [Action.STANDING, Action.WALK_SLOW, Action.WALK_MIDDLE, \
            Action.WALK_FAST, Action.EDGE_TEETERING_START, Action.EDGE_TEETERING, Action.CROUCHING]

        #TODO: Wrap the shine range into a helper
        downsmashrange = 11.8
        indownsmashrange = globals.gamestate.distance < downsmashrange

        if indownsmashrange and globals.smashbot_state.action in downsmashablestate:
            return True

        #TODO: Wrap this up into a helper
        pikarunspeed = 1.8
        #TODO: Subtract from this time spent turning or transitioning
        # Assume that we can run at max speed toward our opponent
        # We can only run for framesleft-1 frames, since we have to spend at least one attacking
        potentialrundistance = (left-1) * pikarunspeed

        if globals.gamestate.distance - potentialrundistance < downsmashrange:
            return True
        return False

    def step(self):
        smashbot_state = globals.smashbot_state
        opponent_state = globals.opponent_state
        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step()
            return

        # TODO: This should be all inactionalbe animations, actually
        if smashbot_state.action == Action.THROW_DOWN:
            self.pickchain(Nothing)
            return

        # Can we charge an upsmash right now?
        framesleft = Punish.framesleft()
        if globals.logger:
            globals.logger.log("Notes", "framesleft: " + str(framesleft) + " ", concat=True)

        # How many frames do we need for an upsmash?
        # It's 8 frames normally, plus some transition frames
        # 3 if in shield, or dash/running
        framesneeded = 8
        shieldactions = [Action.SHIELD_START, Action.SHIELD, Action.SHIELD_RELEASE, \
            Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        runningactions = [Action.DASHING, Action.RUNNING]
        if smashbot_state.action in shieldactions:
            framesneeded += 3
        if smashbot_state.action in runningactions:
            framesneeded += 3

        endposition = opponent_state.x
        isroll = globals.framedata.isroll(opponent_state.character, opponent_state.action)
        slideoff = False

        # If we have the time....
        if framesneeded <= framesleft:
            # Calculate where the opponent will end up
            if opponent_state.hitstun_frames_left > 0:
                endposition = opponent_state.x + globals.framedata.slidedistance(opponent_state, opponent_state.speed_x_attack, framesleft)

            if isroll:
                endposition = globals.framedata.endrollposition(opponent_state, globals.gamestate.stage)

                initialrollmovement = 0
                facingchanged = False
                try:
                    initialrollmovement = globals.framedata.framedata[opponent_state.character][opponent_state.action][opponent_state.action_frame]["locomotion_x"]
                    facingchanged = globals.framedata.framedata[opponent_state.character][opponent_state.action][opponent_state.action_frame]["facing_changed"]
                except KeyError:
                     pass
                backroll = opponent_state.action in [Action.ROLL_BACKWARD, Action.GROUND_ROLL_BACKWARD_UP, \
                    Action.GROUND_ROLL_BACKWARD_DOWN, Action.BACKWARD_TECH]
                if not (opponent_state.facing ^ facingchanged ^ backroll):
                    initialrollmovement = -initialrollmovement

                speed = opponent_state.speed_x_attack + opponent_state.speed_ground_x_self - initialrollmovement
                endposition += globals.framedata.slidedistance(opponent_state, speed, framesleft)

                # But don't go off the end of the stage
                if opponent_state.action in [Action.TECH_MISS_DOWN, Action.TECH_MISS_UP, Action.NEUTRAL_TECH]:
                    if abs(endposition) > melee.stages.edgegroundposition(globals.gamestate.stage):
                        slideoff = True
                endposition = max(endposition, -melee.stages.edgegroundposition(globals.gamestate.stage))
                endposition = min(endposition, melee.stages.edgegroundposition(globals.gamestate.stage))


            # And we're in range...
            # Take our sliding into account
            slidedistance = globals.framedata.slidedistance(smashbot_state, smashbot_state.speed_ground_x_self, framesleft)
            smashbot_endposition = slidedistance + smashbot_state.x

            # Do we have to consider character pushing?
            # Are we between the character's current and predicted position?
            if opponent_state.x < smashbot_endposition < endposition or \
                    opponent_state.x > smashbot_endposition > endposition:
                # Add a little bit of push distance along that path
                # 0.3 pushing for max of 16 frames
                #TODO Needs work here
                onleft = smashbot_state.x < opponent_state.x
                if onleft:
                    smashbot_endposition -= 4.8
                else:
                    smashbot_endposition += 4.8

            if globals.logger:
                globals.logger.log("Notes", "endposition: " + str(endposition) + " ", concat=True)
                globals.logger.log("Notes", "smashbot_endposition: " + str(smashbot_endposition) + " ", concat=True)

            facing = smashbot_state.facing == (smashbot_endposition < endposition)
            # Remember that if we're turning, the attack will come out the opposite way
            if smashbot_state.action == Action.TURNING:
                facing = not facing

            # Get height of opponent at the targeted frame
            height = opponent_state.y
            firefox = opponent_state.action == Action.SWORD_DANCE_3_LOW and opponent_state.character in [Character.FOX, Character.FALCO]
            speed = opponent_state.speed_y_attack
            gravity = globals.framedata.characterdata[opponent_state.character]["Gravity"]
            termvelocity = globals.framedata.characterdata[opponent_state.character]["TerminalVelocity"]
            if not opponent_state.on_ground and not firefox:
                # Loop through each frame and count the distances
                for i in range(framesleft):
                    speed -= gravity
                    # We can't go faster than termvelocity downwards
                    speed = max(speed, -termvelocity)
                    height += speed

            distance = abs(endposition - smashbot_endposition)
            if not slideoff and distance < 12.0 and -5 < height < 8:
                if facing:
                    # Do the upsmash
                    # NOTE: If we get here, we want to delete the chain and start over
                    #   Since the amount we need to charge may have changed
                    self.chain = None
                    self.pickchain(SmashAttack, [framesleft-framesneeded-1, SMASH_DIRECTION.UP])
                    return
                else:
                    # Do the bair if there's not enough time to wavedash, but we're facing away and out of shine range
                    #   This shouldn't happen often, but can if we're pushed away after powershield
                    offedge = melee.stages.edgegroundposition(globals.gamestate.stage) < abs(endposition)
                    if framesleft < 11 and distance > 9 and not offedge:
                        self.pickchain(Shffl, [SHFFL_DIRECTION.BACK])
                        return
            # If we're not in attack range, and can't run, then maybe we can wavedash in
            #   Now we need more time for the wavedash. 10 frames of lag, and 3 jumping
            framesneeded = 13
            if framesneeded <= framesleft:
                if smashbot_state.action in shieldactions or smashbot_state.action in shineactions:
                    self.pickchain(Wavedash)
                    return

        # Kill the existing chain and start a new one
        self.chain = None
        self.pickchain(DashDance, [endposition])
