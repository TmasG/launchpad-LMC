import pynput
import launchpad_py
import time
keyboard = pynput.keyboard.Controller()
key = pynput.keyboard.Key
lp = launchpad_py.LaunchpadMk2()
lp.Open( 0, "mk2" )
lp.ButtonFlush()
lp.Reset()
registers = {"pc":0,"ir":0,"ar":0,"acc":0}
ram = []
ramDims = [5,7]
for i in range(ramDims[0]*ramDims[1]):
    ram.append(0)
page = 0
output =  []
lmcColorsDefault = {}
for i in range(9):
    val = {}
    for j in range(9):
        val[j] = [0,0,0]
    lmcColorsDefault[i] = val
ready = True
lmcColorsTick = {0:{1:[173, 0, 144]},1:{7:[15,15,250],8:[15,15,250]},2:{6:[0,100,0]},3:{5:[0,100,0],6:[0,100,0]},4:{6:[0,100,0]}}
componentCoords = {"out":[[0,1],[0,2],[1,1],[1,2]],"pc":[[0,3],[1,3]],"inst":[[0,4],[1,4]],"acc":[[0,5],[1,5]],"alu":[[0,6],[1,6]],"inp":[[0,7],[1,7],[0,8],[1,8]],"ram":[]}
for x in range(5):
    for y in range(7):
        componentCoords["ram"].append([x+3,y+1])
def readFile(fileName):
  with open(fileName) as f:
    lines = list(f.readlines())
    return(lines)
def assembleToMemory():
    global ram
    components = {"hlt":0,"add":1,"sub":2,"sta":3,"lda":5,"bra":6,"brz":7,"brp":8,"int":91,"out":92}
    # loading source code file
    file = readFile("code.txt")
    dats = {}
    # clean and dat
    for ln in range(len(file)):
        file[ln] = file[ln].replace("\n","").split("#")[0].rstrip().lower().split(" ")
        if len(file[ln])>1 and "dat" == file[ln][1]:
            dats[file[ln][0]] = str(ln)
        # assembling
    for ln in range(len(file)):
        if len(file[ln])>1 and "dat" == file[ln][1]:
            ram[ln]= int(file[ln][2])
        else:
            if len(file[ln])>1:
                for i in dats:
                    if file[ln][1] == i:
                        file[ln][1] = dats[i]
                ram[ln] = int(str(components[file[ln][0]]) + file[ln][1])
            else:
                ram[ln] = components[file[ln][0]]

def setSection(default, section, colors):
    global lmcColorsTick
    global lmcColorsDefault
    if section in componentCoords:
        for i in range(len(componentCoords[section])):
            lp.LedCtrlXY(componentCoords[section][i][0],componentCoords[section][i][1],colors[0],colors[1],colors[2])
        if default:
            for i in range(len(componentCoords[section])):
                lmcColorsDefault[componentCoords[section][i][0]][componentCoords[section][i][1]] = colors
componentColors = {"out":[250,0,250],"pc":[0,0,250],"inst":[0,50,150],"acc":[250,0,250],"alu":[250,150,0],"inp":[0,150,250],"ram":[250,250,0]}
for component in componentColors:
    setSection(True, component, componentColors[component])

def intialiseLmcColors():
    global lmcColorsDefault
    global tickFlash
    tickFlash = []
    for x in lmcColorsDefault:
        for y in lmcColorsDefault[x]:
            lp.LedCtrlXY(x,y,lmcColorsDefault[x][y][0],lmcColorsDefault[x][y][1],lmcColorsDefault[x][y][2])

def clearPad():
    global lmcColorsDefault
    for x in lmcColorsDefault:
        for y in lmcColorsDefault[x]:
            lp.LedCtrlXY(x,y,0,0,0)
def updatePad():
    global tickFlash
    global lmcColorsDefault
    global ready
    tickFlashIncr = []
    for i in range(len(tickFlash)):
        x = tickFlash[i][0][0]
        y = tickFlash[i][0][1]
        pixActDelay = tickFlash[i][1]
        pixLifetime = tickFlash[i][2]
        color = tickFlash[i][3]
        if pixActDelay != 0:
            tickFlashIncr.append([[x,y],pixActDelay-1,pixLifetime,color])
        elif pixLifetime != 0:
            lp.LedCtrlXY(x,y,color[0],color[1],color[2])
            tickFlashIncr.append([[x,y],pixActDelay,pixLifetime-1,color])
        else:
            lp.LedCtrlXY(x,y,lmcColorsDefault[x][y][0],lmcColorsDefault[x][y][1],lmcColorsDefault[x][y][2])
    tickFlash = tickFlashIncr
    if tickFlash == []:
        ready = True
    else:
        ready = False
    
def q(x,y,a,b,c):
    global tickFlash
    tickFlash.append([[x,y],a,b,c])
def fetchData(adloc,offset):
    global ramDims
    commands = 0
    #formats list index as co-ordinate
    x = 3+(adloc)%ramDims[0]
    y = (adloc)//ramDims[0]+1
    q(x,y,offset+commands,1,[0,150,0])
    y+=1
    while y <= 7:
        q(x,y,offset+commands,1,[0,0,150])
        commands += 1
        y+=1
    y+=1
    while x >= 2:
        q(x,8,offset+commands,1,[0,0,150])
        commands += 1
        x-=1
    x-=1
    q(2,6,offset+commands+1,1,[0,0,150])
    q(2,7,offset+commands,1,[0,0,150])
    q(2,5,offset+commands+2,1,[0,0,150])
    q(0,5,offset+commands+3,1,[0,150,0])
    q(1,5,offset+commands+3,1,[0,150,0])
    return(commands+4)
def deliverData(adloc,offset):
    global ramDims
    # convert to list
    address = [4+(adloc)%ramDims[0],(adloc)//ramDims[0]]
    q(0,5,offset,1,[0,150,0])
    q(1,5,offset,1,[0,150,0])
    q(2,5,offset+1,1,[0,0,150])
    q(2,6,offset+2,1,[0,0,150])
    q(2,7,offset+3,1,[0,0,150])
    commands = 4
    x=2
    while x < address[0]:
        q(x,8,offset+commands,1,[0,0,150])
        commands += 1
        x+=1
    x-=1
    y=7
    while y > address[1]+1:
        q(x,y,offset+commands,1,[0,0,150])
        commands += 1
        y-=1
    q(x,y,offset+commands,1,[0,150,0])
    return(commands)

def inputData(offset):
    global registers
    # in to acc
    registers["acc"] = int(input("Input -->"))
    flashComponent("in",[150,150,150],0)
    q(2,7,1+offset,1,[0,150,0])
    q(2,6,2+offset,1,[0,150,0])
    q(2,5,3+offset,1,[0,150,0])
    q(0,5,4+offset,1,[0,0,150])
    q(1,5,4+offset,1,[0,0,150])
    return(4)
def outputData(offset):
    global registers
    # acc to out
    q(0,5,1+offset,1,[0,150,0])
    q(1,5,1+offset,1,[0,150,0])
    q(2,5,2+offset,1,[0,150,0])
    q(2,4,3+offset,1,[0,150,0])
    q(2,3,4+offset,1,[0,150,0])
    flashComponent("out",[150,150,150],5)
    print("Output: " + str(registers["acc"]))
    return(5)

# Defining light paths \/ (Start)
def instToPc(offset):
    q(0,4,0+offset,1,[150,0,0])
    q(1,4,0+offset,1,[150,0,0])
    q(2,4,1+offset,1,[150,0,0])
    q(2,3,2+offset,1,[150,0,0])
    q(1,3,3+offset,1,[150,0,0])
    q(0,3,3+offset,1,[150,0,0])
    return(3)

def pcToInst(offset):
    q(1,3,0+offset,1,[150,0,0])
    q(0,3,0+offset,1,[150,0,0])
    q(2,3,1+offset,1,[150,0,0])
    q(2,4,2+offset,1,[150,0,0])
    q(1,4,3+offset,1,[150,0,0])
    q(0,4,3+offset,1,[150,0,0])
    return(3)

def aluToAcc(offset):
    q(0,6,0+offset,1,[150,0,0])
    q(1,6,0+offset,1,[150,0,0])
    q(2,6,1+offset,1,[150,0,0])
    q(2,5,2+offset,1,[150,0,0])
    q(0,5,3+offset,1,[150,0,0])
    q(1,5,3+offset,1,[150,0,0])
    return(3)

def accToAlu(offset):
    q(0,5,0+offset,1,[150,0,0])
    q(1,5,0+offset,1,[150,0,0])
    q(2,5,1+offset,1,[150,0,0])
    q(2,6,2+offset,1,[150,0,0])
    q(0,6,3+offset,1,[150,0,0])
    q(1,6,3+offset,1,[150,0,0])
    return(3)
# Defining light paths /\ (end)

def flashComponent(component,color,offset):
    global tickFlash
    global componentCoords
    for i in range(len(componentCoords[component])):
        q(componentCoords[component][i][0],componentCoords[component][i][1],0+offset,1,color)

def endProcess():
    global programStatus
    programStatus = False
    exit()

def runInst():
    global registers
    global ram
    instruction = ram[registers["pc"]]
    registers["ir"] = int(str(instruction)[0:1])
    if len(str(instruction)) > 1:
        registers["ar"] = int(str(instruction)[1:])
    else:
        registers["ar"] = None
    if registers["ir"] == 0:
        endProcess()
    elif registers["ir"] == 1:
        print("add")
        delay = 0
        accToAlu(0)
        delay = fetchData(registers["ar"],3)
        aluToAcc(3 + delay)
        flashComponent("alu",[0,150,0],6 + delay)
        val = registers["acc"] + ram[registers["ar"]]
        aluToAcc(7 + delay)
        registers["acc"] = val
        return(10+delay)
    elif registers["ir"] == 2:
        print("sub")
        accToAlu(0)
        delay = fetchData(registers["ar"],3)
        accToAlu(3 + delay)
        flashComponent("alu",[0,150,0],6 + delay)
        val = registers["acc"] - ram[registers["ar"]]
        aluToAcc(7 + delay)
        registers["acc"] = val
        return(10+delay)
    elif registers["ir"] == 3:
        print("sta")
        delay = deliverData(registers["ar"],0)
        ram[registers["ar"]] = registers["acc"]
        return(delay)
    elif registers["ir"] == 5:
        print("ldr")
        flashComponent("acc",[150,0,0],0)
        delay = fetchData(registers["ar"],1)
        registers["acc"] = ram[registers["ar"]]
        return(delay)
    elif registers["ir"] == 6:
        print("bra")
        registers["pc"] = registers["ar"]
        return(0)
    elif registers["ir"] == 7:
        print("brz")
        accToAlu(0)
        if registers["acc"] == 0:
            flashComponent("alu",[0,150,0],3)
            registers["pc"] = registers["ar"]
            return(4)
        else:
            flashComponent("alu",[150,0,0],3)
            return(4)
    elif registers["ir"] == 8:
        print("brp")
        accToAlu(0)
        if registers["acc"] > 0:
            flashComponent("alu",[0,150,0],3)
            registers["pc"] = registers["ar"]
            return(4)
        else:
            flashComponent("alu",[150,0,0],3)
            return(4)
    elif registers["ir"] == 9:
        print("io")
        if registers["ar"] == 1:
            inputData(0)
            return(4)
        elif registers["ar"] == 2:
            outputData(0)
            return(5)
    return(3)
        

assembleToMemory()
lp.LedAllOn(0)
lp.Reset()
intialiseLmcColors()
# Time between ticks (ms)
tickLength = 150 
print("Start")
programStatus = True
i = 0
while True:
    if i %tickLength == 0:
        updatePad()
        if ready and programStatus:
            #FDE:
            delay = runInst()+1
            #iteration
            registers["pc"]+=1
            w = [150,150,150]
            q(0,3,delay,1,w)
            q(1,3,delay,1,w)
            q(2,3,delay+1,1,w)
            q(2,4,delay+2,1,w)
            q(2,5,delay+3,1,w)
            q(2,6,delay+4,1,w)
            q(0,6,delay+5,1,w)
            q(1,6,delay+5,1,w)
            q(2,6,delay+6,1,w)
            q(2,5,delay+7,1,w)
            q(2,4,delay+8,1,w)
            q(2,3,delay+9,1,w)
            q(0,3,delay+10,1,w)
            q(1,3,delay+10,1,w)
    i+=1
    time.sleep(0.001)