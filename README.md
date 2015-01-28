# py-minidrone #

This is an unfinished Python library to control Parrot Rolling Spiders (one of the minidrones announced in 2014) over BLE.

I've started working on this project in September 2014, then stopped due to lack of free time.
The code is _NOT_ clean (especially the demo), I was still in the middle of testing and implementing several functions. There are things that just do not work.

Expect something like this: https://www.youtube.com/watch?v=zAfGR75qia8

I am planning to finish the library (at least what I planned originally), though.

#### I am not responsible for any harm done by/to your drone! Use this at your own risk. ####


### How do I get set up? ###

* Install Python 2.7+, Pexpect (pip install pexpect)
* Install BlueZ 5+ (probably you will need to compile it from source, watch out for dependencies)
  + If you compiled it from source, don't forget to copy the %BlueZ%/attrib/gatttool binary to your PATH
* Clone repo
* Edit top of demo.py, replace MAC with yours
  + You can check it from CLI with "sudo hcitool lescan"
* ./demo.py
* Press 'c'
* If the top menu gets filled with data from the drone, you're all set
* FLY!
* If anything goes wrong, press Esc (emergency cut-off)
 
BT chips (both in the drone and in adapters) are pretty nitpicking regarding BLE connections, you might need to turn off/on your drone sometimes, also don't forget to use 'sudo hciconfig hciX reset'.


### Contribution ###

* Pull requests are more than welcome

