An assembly launguage/machine code execution visualiser, made to run on a launchpad (mk2).
A simplified instruction set of mnemonics are assembled into a virtual ram. (Docs for the simplified mnemonics: https://peterhigginson.co.uk/LMC/help.html)
An instruction is then fetched, decoded and executed, with the animations queued into a sequence. The queue is then fulfilled tick-by-tick.
When then launchpad sequence queue is empty, the program counter is iterated, followed by the next fde cycle initiating.
The program is run until a 'HLT' mneumonic ends the cycle.