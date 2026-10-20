import os


def read_file(filename):
    # get working dir
    curr_dir = os.path.dirname(os.path.abspath(__file__))

    # find folder 'input'
    input = os.path.join(curr_dir, 'input')
    path = os.path.join(input, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"file missing: {path}")

    with open(path, 'r', encoding='utf-8') as f: lines = [line.strip() for line in f.readlines() if line.strip()]

    ind = 0

    # num of crops
    num_crops = int(lines[ind])
    ind += 1 #ahhh python has no ++

    # read crops
    crops = []
    for i in range(num_crops):
        crops.append(lines[ind])
        ind += 1

    # num of dishes
    num_dishes = int(lines[ind])
    ind += 1

    # Read dishes
    dishes = []
    for i in range(num_dishes):
        ingredients = lines[ind].split()
        dishes.append((1, ingredients))
        ind += 1

    return crops, dishes