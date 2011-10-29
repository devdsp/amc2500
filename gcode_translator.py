#!/usr/bin/env python
from gcode import *
from amc2500 import *

def main():
  if len(sys.argv) <= 1:
    exit()
  commands = parse(sys.argv[1])
  amc = AMCGenerator()
  for i in range(0, len(commands)):
    print amc.render(commands[i])

if __name__ == "__main__":
    main()
