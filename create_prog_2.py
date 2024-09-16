from random import randint
for num in [0,5,10,15,20,25,30,35,40,45,50]:
    print(f'CREATE_{num},CREATE,{num},' + '6d6460016001016000526005601cf3600052' + '6000' * 60 + '600d60126000' * num + 'f050' * num)
    

memory_stores = ''
for i in range(0, 51):
    hexed_i = hex(i)[2:] if i > 15 else '0' + hex(i)[2:]
    memory_stores += '6d6460' + hexed_i + '6001016000526005601cf360' + hexed_i + '52'

for num in [0,5,10,15,20,25,30,35,40,45,50]:
    args = ''
    for i in range(1, num + 1):
        salt = hex(i)[2:] if i > 15 else '0' + hex(i)[2:]
        for _ in range(0,62):
            salt = salt + str(randint(0,9))
        mem_offset = (i - 1) * 32 + 18
        hexed_mem_offset = ''
        if mem_offset < 255:
            hexed_mem_offset = '00' + hex(mem_offset)[2:]
        else:
            hexed_mem_offset = '0' + hex(mem_offset)[2:]
        args += '7f' + salt + '600d61' + hexed_mem_offset + '6000'
    print(f'CREATE2_{num},CREATE2,{num},' + memory_stores + '6000' * 60 + args + 'f550' * num)

