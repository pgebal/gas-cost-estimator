from random import randint
for num in [0,5,10,15,20,25,30,35,40,45,50]:
    print(f'CREATE_{num},CREATE,{num},' + '6d6460016001016000526005601cf3600052' + '6000' * 60 + '600d60126000' * num + 'f050' * num)
    
for num in [0,5,10,15,20,25,30,35,40,45,50]:
    args = ''
    for i in range(1, num + 1):
        salt = hex(i)[2:] if i > 15 else '0' + hex(i)[2:]
        for _ in range(0,62):
            salt = salt + str(randint(0,9))
        args += '7f' + salt + '600d60126000'
    print(f'CREATE2_{num},CREATE2,{num},' + '6d6460016001016000526005601cf3600052' + '6000' * 60 + args + 'f550' * num)

