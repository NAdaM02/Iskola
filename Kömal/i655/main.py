"""
I. 655-ös feladat
Ancsin Ádám, 11.C
Budapesti Fazekas Mihály Gimnázium

* megjegyzés:
    A feladat példájában megadott kimenet első sorában a
    kezdeti 1-es és 4-es számok a műveletsorozat elvégzése
    utáni helyeit azonos (4-es) szám jelöli.
    A helyes kimenet:
     > 3 14 15 4
     > 23 24 1 4
"""

def shuffle(arr:list, part_start:int, part_end:int, target_index:int):
    part_start, part_end, target_index = part_start-1, part_end-1, target_index
    part = arr[part_start:part_end+1]
    rest = arr.copy()
    del rest[part_start:part_end+1]
    new = [0 for _ in range(len(arr))]
    if part_start<= target_index:
        for i in range(len(arr)):
            if target_index-part_end+part_start-1<= i<= target_index-1:
                new[i] = part.pop(0)
            else:
                new[i] = rest.pop(0)
    else:
        for i in range(len(arr)):
            if target_index<= i< target_index+1+part_end-part_start:
                new[i] = part.pop(0)
            else:
                new[i] = rest.pop(0)
    return new



if __name__ == '__main__':
    N, rep_count = map(int, input().split())
    numbers = [i for i in range(1, N)]
    
    a = numbers.copy()
    for _ in range(rep_count):
        part_start, part_end, target_index = map(int, input().split())
        a = shuffle(a, part_start, part_end, target_index)
    
    print(" ".join([str(a.index(interesting_number)+1) for interesting_number in numbers[:rep_count]]))
    print(" ".join(list(map(str, a[:rep_count]))))
