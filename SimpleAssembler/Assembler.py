import sys

riscv_r_type = {  
    "ADD":  {"opcode": "0110011", "func3": "000", "func7": "0000000"},  
    "SUB":  {"opcode": "0110011", "func3": "000", "func7": "0100000"},  
    "AND":  {"opcode": "0110011", "func3": "111", "func7": "0000000"},  
    "OR":   {"opcode": "0110011", "func3": "110", "func7": "0000000"},      
    "SRL":  {"opcode": "0110011", "func3": "101", "func7": "0000000"},    
    "SLT":  {"opcode": "0110011", "func3": "010", "func7": "0000000"}  
}

riscv_i_type = {  
    "ADDI": {"opcode": "0010011", "func3": "000", "func7": ""},    
    "LW":   {"opcode": "0000011", "func3": "010", "func7": ""},  
    "JALR": {"opcode": "1100111", "func3": "000", "func7": ""}  
}

riscv_s_type = {  
    "SW":   {"opcode": "0100011", "func3": "010", "func7": ""}   
}

riscv_b_type = {  
    "BEQ":  {"opcode": "1100011", "func3": "000", "func7": ""},  
    "BNE":  {"opcode": "1100011", "func3": "001", "func7": ""}  
}

riscv_j_type = {  
    "JAL": {"opcode": "1101111", "func3": "", "func7": ""}  
}


def inttobinary(value, bit_width):
    if value < 0:
        value = (2 ** bit_width) + value
    
    binary_representation = format(value & ((2 ** bit_width) - 1), f'0{bit_width}b')
    return binary_representation

'''conversion fn takes a risc-v assembly instruction, operands, and PC address as input
it converts the given instruction (r,i,s,j,b types) into its 32-bit binary repesentation
also performs error checking so that registers and immediate values are valid
if a label is referenced, the function resolves it using a dictionary L that stores label addresses
inttobinary() converts immediate values into binary 
depending on the instruction type, the function assembles the binary representation by combining opcode, function codes, and register values
if an invalid instruction/operand is encountered, it prints an error message and stops execution. final binary instruction is returned as a string.'''
def conversion(instr,data,curr_address):
    PC = '' #stores the final binary conversion
    #Checks which type the instruction belongs to
    #note to self: instr and data are both strings
    is_label = False
    for key in L: #Checks for label headers and label calls, truth and false on a variable to check for this
        if key in data:
            is_label = True
    if ":" in instr:
        instr = (instr.split(":")[1]) #if instruction contains a label, extract only the instruction part
        
    #r type instructions
    if instr in riscv_r_type: 
        Operands = data.split(',')
        if Operands[0] not in riscv_registers or Operands[1] not in riscv_registers or Operands[2] not in riscv_registers:          #Error testing, if register is invalid
            print("INVALID REGISTER(S)")
            quit()
        PC += riscv_r_type[instr]['func7'] + riscv_registers[Operands[2]] + riscv_registers[Operands[1]] + riscv_r_type[instr]['func3'] + riscv_registers[Operands[0]] + riscv_r_type[instr]['opcode']
        #Above line constructs binary encoding using func7, rs2, rs1, func3, rd, opcode

    #i type instructions
    elif instr in riscv_i_type: 
        info = data.split(',')
        Operands = [info[0],0,0] #placeholder for indexing
        
        try:
            if instr in "LW": #Handles the different format of LW specifically
                Operands[1] = info[1].split('(')[1].strip(')')
                if Operands[0] not in riscv_registers or Operands[1] not in riscv_registers:
                    print("INVALID REGISTER(S)")
                    print("Line number -",(curr_address+4)//4) 
                    quit() #Error handling for underflow and invalid registers
                if int(info[1].split('(')[0]) < -(curr_address):
                    print("INVALID IMMEDIATE VALUE")
                    print("Line number -",(curr_address+4)//4)
                    quit()
                Operands[2] = inttobinary(int(info[1].split('(')[0]),12)
                PC += Operands[2] + riscv_registers[Operands[1]] + riscv_i_type[instr]['func3'] + riscv_registers[Operands[0]] + riscv_i_type[instr]['opcode']
            else: #Other i type instructions are handled here
                Operands[1] = info[1]
                if Operands[0] not in riscv_registers or Operands[1] not in riscv_registers: #More error handling
                    print("INVALID REGISTER(S)")
                    print("Line number -",(curr_address+4)//4) 
                    quit()
                if int(info[2]) < -(curr_address):
                    print("INVALID IMMEDIATE VALUE")
                    print("Line number -",(curr_address+4)//4)
                    quit()
                Operands[2] = inttobinary(int(info[2]),12)
                PC += Operands[2] + riscv_registers[Operands[1]] + riscv_i_type[instr]['func3'] + riscv_registers[Operands[0]] + riscv_i_type[instr]['opcode']
        except:
            return "UNKNOWN"

    # s type instructions
    elif instr in riscv_s_type:
        rs2, offset_rs1 = data.split(',')
        offset, rs1 = offset_rs1.split('(')
        rs1 = rs1.strip(')')
        if rs1 not in riscv_registers or rs2 not in riscv_registers:
            print("INVALID REGISTER(S)")
            print("Line number -",(curr_address+4)//4)
            quit()
        if int(offset) < -(curr_address):
            print("INVALID IMMEDIATE VALUE")
            print("Line number -",(curr_address+4)//4)
            quit()

        imm_bin = inttobinary(int(offset), 12) #splits the immediate value into two parts
        imm_high, imm_low = imm_bin[:7], imm_bin[7:]

        PC += (imm_high + riscv_registers[rs2] + riscv_registers[rs1] +
            riscv_s_type[instr]['func3'] + imm_low + riscv_s_type[instr]['opcode'])

    #b type instructions
    elif instr in riscv_b_type: #If instruction is b type
        try:
            if not is_label: #Checks label call exists
                rs1, rs2, offset = data.split(',')
                imm_bin = inttobinary(int(offset), 12)
                imm_high, imm_low = imm_bin[:7], imm_bin[7:]
                if rs1 not in riscv_registers or rs2 not in riscv_registers: #error handling
                    print("INVALID REGISTER(S)")
                    print("Line number -",(curr_address+4)//4)
                    quit()
                if int(offset) < -(curr_address):
                    print("INVALID IMMEDIATE VALUE")
                    print("Line number -",(curr_address+4)//4)
                    quit()

                PC += (imm_high + riscv_registers[rs2] + riscv_registers[rs1] + 
                    riscv_b_type[instr]['func3'] + imm_low + riscv_b_type[instr]['opcode'])
            else: #Label exists
                rs1, rs2, label = data.split(',')
                rs1,rs2,label = rs1.strip(),rs2.strip(),label.strip()
                if rs1 not in riscv_registers or rs2 not in riscv_registers: #Error handling
                    print("INVALID REGISTER(S)")
                    print("Line number -",(curr_address+4)//4)
                    quit()
                if label not in L:
                    print(label,"LABEL NOT DEFINED")
                    print("Line number -",(curr_address+4)//4)
                    quit()
                label_address = L[label] #Get label address
                imm_bin = (inttobinary((label_address-curr_address)//2, 12))[::-1] #Numerical value of imm
                PC += imm_bin[11] + imm_bin[9:3:-1] + riscv_registers[rs2] + riscv_registers[rs1] + riscv_b_type[instr]['func3'] + imm_bin[3::-1] + imm_bin[10] + riscv_b_type[instr]['opcode']
        except:
            print("An error has occured")
            quit()
    #j type instructions
    elif instr in riscv_j_type:
        try:
            if not is_label: #No label
                rd, imm = data.split(',')
                if rd not in riscv_registers: #Error handling
                    print("INVALID REGISTER(S)")
                    print("Line number -",(curr_address+4)//4)
                    quit()
                if int(imm) < -(curr_address):
                    print("INVALID IMMEDIATE VALUE")
                    print("Line number -",(curr_address+4)//4)
                    quit()
                imm_bin = inttobinary(int(imm), 21)
                PC += imm_bin[0] + imm_bin[10:20] + imm_bin[9] + imm_bin[1:9] + riscv_registers[rd] + riscv_j_type[instr]['opcode']
            else: #Label exists
                rd, label = data.split(',')
                rd,label = rd.strip(),label.strip()                             
                if rd not in riscv_registers: #error handling
                    print("INVALID REGISTER(S)")
                    print("Line number -",(curr_address+4)//4)
                    quit()
                if label not in L:
                    print(label,"LABEL NOT DEFINED")
                    print("Line number -",(curr_address+4)//4)
                    quit()
                label_address = L[label] #Address of label
                imm_bin = (inttobinary((label_address-curr_address), 21)) #Numerical value of imm
                if label_address-curr_address < 0:
                    imm_bin = '1' + imm_bin[:20]
                PC += imm_bin[0] + imm_bin[10:20] + imm_bin[9] + imm_bin[1:9] + riscv_registers[rd] + riscv_j_type[instr]['opcode']
                
        except:
            return "UNKNOWN"

    else:
        print("INVALID OPERATION")
        print("Line number -",(curr_address+4)//4)
    return PC

riscv_registers = {
    "x0":  "00000", "x1":  "00001", "x2":  "00010", "x3":  "00011",
    "x4":  "00100", "x5":  "00101", "x6":  "00110", "x7":  "00111",
    "x8":  "01000", "x9":  "01001", "x10": "01010", "x11": "01011",
    "x12": "01100", "x13": "01101", "x14": "01110", "x15": "01111",
    "x16": "10000", "x17": "10001", "x18": "10010", "x19": "10011",
    "x20": "10100", "x21": "10101", "x22": "10110", "x23": "10111",
    "x24": "11000", "x25": "11001", "x26": "11010", "x27": "11011",
    "x28": "11100", "x29": "11101", "x30": "11110", "x31": "11111",
    "zero":"00000", "ra":"00001", "sp":"00010", "gp":"00011", "tp":"00100",
    "t0":"00101", "t1":"00110", "t2":"00111", "s0":"01000", "fp":"01000", "s1":"01001", "a0":"01010",
    "a1":"01011", "a2":"01100", "a3":"01101", "a4":"01110", "a5":"01111", "a6":"10000", "a7":"10001", "s2":"10010", "s3":"10011", "s4":"10100",
    "s5":"10101", "s6":"10110", "s7":"10111", "s8":"11000", "s9":"11001", "s10":"11010", "s11":"11011", "t3":"11100", "t4":"11101", "t5":"11110", "t6":"11111"
}

def labels(file_name): #Parces the entire file to check for every label header
    L = {}  #{label:address}
    address = 0
    f = open(file_name,'r')
    lines = f.readlines()
    if "beq zero,zero,0" not in lines[-1]: #Checks if final halt is applicable(only to stop garbage instructions from running after execution)
        print("Invalid last line")
        quit()
    for line in lines:
        if (':' in line) and (line.split(':')[0] not in L) and (' :' not in line):
            L[line.split(':')[0]] = address
        address += 4
    return L


def extract(file_name): # purpose of this fuction is to read from file and extract data into dictionary for analysis
    main={} # general structure to be {address:{operation:data}}
    f = open(file_name,"r") # opens set file name
    count = 0 # count used to set address values
    for line in f:
        if ':' in line: # checks for : to detect labels
            operation = line.split(':')[1].split()[0].strip() # takes LHS
            data = line.split(':')[1].split()[1].strip() # takes RHS
        else: # if no labels then splits normally no special case
            operation = line.split(" ")[0].strip() # takes LHS
            data = line.split(" ")[1].strip() # takes RHS
        main[count] = {operation.strip().upper():data} # adds operation and data to dictionary
        count+=4 # increases count by 4 to do address 
    f.close() # closes file
    return main # returns dictionary of operations and data

def write(main,ofile): # calculates the binary instruction wise and write it to output file
    f = open(ofile,'w') 
    for i,j in main.items(): # loops over dict, i = address, j = dict of operation and data
        for k,g in j.items(): # k = operation, g = data
            bin = conversion(k,g,i) # puts in operation, data and address to calculate binary
            f.write(bin) # writes binary to file for the instruction
            f.write("\n") 
    f.close() # closes file
    return main # returns dict

ifile = str(sys.argv[1])
ofile = str(sys.argv[2])
L = labels(ifile)
main = extract(ifile)
count = 1
for i,j in main.items():
    count+=1
write(main,ofile)