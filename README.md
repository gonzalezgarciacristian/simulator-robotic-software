# Robotic Software Simulator
<p align="center">
  <img src="assets/logo.svg" width="200" alt="Simulator Robotic Software logo">
</p>

## Simulator for Linear Actuator and Mobile Robots (using Arduino)
This simulator is an Arduino simulator for robots, those being:
- Linear Actuator, which is composed by a servo, a joystick and two buttons acting as path limiters.
- Mobile robot, composed by two servos which will move the wheels, an ultrasonic sensor and, depending on the case:
    - Two infrared sensors: This robot is thought to be used in path following cases.
    - Four infrared sensors: This robot is thought to be used in labyrinth solving.

This system is designed with the intent to allow the development of new robots and libraries. In fewer words, it can be expanded with more robots and more Arduino code (not only libraries, but further Arduino syntax).

# Getting the simulator
## Binary downloads
Official binaries for the simulator can be found [here](https://github.com/diegofs29/simulator-robotic-software/releases).

## Generate executable
There are two ways of generating the program's executable. First one is by calling the build.py module:

`python build.py`

The alternative way is by using [Pyinstaller](https://pyinstaller.org/en/stable/) on a command prompt:

`pyinstaller main.spec`

Both ways, a build and a dist folder will be created. It is under the second one where the application's folder will be found. In this folder you can find the executable for the application. If opened, it will show two windows, a console and the program itself.

# License
This program is distributed under the [GNU General Public License Version 3](https://github.com/diegofs29/simulator-robotic-software/blob/main/LICENSE)