
def shuffle(arr:list, part_start:int, part_end:int, target_index:int):
    part_start, part_end, target_index = part_start-1, part_end-1, target_index
    part = arr[part_start:part_end+1]
    rest = arr.copy()
    del rest[part_start:part_end+1]
    new = [0 for _ in range(len(arr))]
    print(arr)
    print(rest, part)
    print()
    for i in range(len(arr)):
        if target_index-part_end+part_start-1<= i<= target_index-1:
            new[i] = part.pop(0)
            print('N', end=" ")
        else:
            new[i] = rest.pop(0)
            print('.', end=" ")
        print(i, new)
    print()
    return new

a = shuffle([1, 2, 3, 4, 5, 6], 2, 3, 5)
print(a)
print()
print('nigga')
print()
print(shuffle(a, 3, 5, 1))
