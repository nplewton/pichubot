#!/usr/bin/python3
import melee
import argparse
import signal
import sys
from strategy import Strategy

import globals
#This example program demonstrates how to use the Melee API to run dolphin programatically,
#   setup controllers, and send button presses over to dolphin

def check_port(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 4:
         raise argparse.ArgumentTypeError("%s is an invalid controller port. \
         Must be 1, 2, 3, or 4." % value)
    return ivalue

chain = None

parser = argparse.ArgumentParser(description='Example of libmelee in action')
parser.add_argument('--port', '-p', type=check_port,
                    help='The controller port your AI will play on',
                    default=2)
parser.add_argument('--opponent', '-o', type=check_port,
                    help='The controller port the opponent will play on',
                    default=1)
parser.add_argument('--live', '-l',
                    help='The opponent is playing live with a GCN Adapter',
                    default=True)
parser.add_argument('--debug', '-d', action='store_true',
                    help='Debug mode. Creates a CSV of all game state')
parser.add_argument('--framerecord', '-r', default=False, action='store_true',
                    help='Records frame data from the match, stores into framedata.csv')

args = parser.parse_args()

log = None
if args.debug:
    log = melee.logger.Logger()

framedata = melee.framedata.FrameData(args.framerecord)

#Options here are:
#   "Standard" input is what dolphin calls the type of input that we use
#       for named pipe (bot) input
#   GCN_ADAPTER will use your WiiU adapter for live human-controlled play
#   UNPLUGGED is pretty obvious what it means
opponent_type = melee.enums.ControllerType.UNPLUGGED
if args.live:
    opponent_type = melee.enums.ControllerType.GCN_ADAPTER

#Create our Dolphin object. This will be the primary object that we will interface with
dolphin = melee.dolphin.Dolphin(ai_port=args.port, opponent_port=args.opponent,
    opponent_type=opponent_type, logger=log)
#initialize our global objects
globals.init(dolphin, args.port, args.opponent)

gamestate = globals.gamestate
controller = globals.controller

def signal_handler(signal, frame):
    dolphin.terminate()
    if args.debug:
        log.writelog()
        print("") #because the ^C will be on the terminal
        print("Log file created: " + log.filename)
    print("Shutting down cleanly...")
    if args.framerecord:
        framedata.saverecording()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#Run dolphin and render the output
#dolphin.run(render=True)

#Plug our controller in
#   Due to how named pipes work, this has to come AFTER running dolphin
#   NOTE: If you're loading a movie file, don't connect the controller,
#   dolphin will hang waiting for input and never receive it
controller.connect()

strategy = Strategy()

#Main loop
while True:
    #"step" to the next frame
    gamestate.step()

    #What menu are we in?
    if gamestate.menu_state == melee.enums.Menu.IN_GAME:
        try:
            strategy.step()
        except Exception as error:
            # Do nothing in case of error thrown!
            controller.empty_input()
            if log:
                log.log("Notes", "Exception thrown: " + repr(error) + " ", concat=True)
            strategy = Strategy()
         
    #If we're at the character select screen, choose our character
    elif gamestate.menu_state == melee.enums.Menu.CHARACTER_SELECT:
        melee.menuhelper.choosecharacter(character=melee.enums.Character.PIKACHU,
            gamestate=gamestate, controller=controller, swag=False, start=True)
    #If we're at the postgame scores screen, spam START
    elif gamestate.menu_state == melee.enums.Menu.POSTGAME_SCORES:
        melee.menuhelper.skippostgame(controller=controller)
    #If we're at the stage select screen, choose a stage
    elif gamestate.menu_state == melee.enums.Menu.STAGE_SELECT:
        melee.menuhelper.choosestage(stage=melee.enums.Stage.FINAL_DESTINATION,
            gamestate=gamestate, controller=controller)
    #Flush any button presses queued up
    controller.flush()
    if log:
        log.logframe(gamestate)
        log.writeframe()
