import sys

from ortools.sat.python import cp_model
from reader import read_file

# constants
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
NUM_MONTHS = 12
PLANT = 3
CYCLES = 3

#read the file
filename = sys.argv[1]
crops, dishes = read_file(filename)

#get next 3 month :: [3 months]
def occ_months(start):
    return [(start + i) % NUM_MONTHS for i in range(CYCLES)]

#check overlap :: bool
def overlap(start1, start2):
    return len(set(occ_months(start1)) & set(occ_months(start2))) > 0

print(f"Crops: {crops}")
print(f"Dishes: {len(dishes)}")

# create solver
model = cp_model.CpModel()

# Decision variable start of cycle
starty = {}
for plant in range(PLANT):
    starty[plant] = {}
    for month in range(NUM_MONTHS):
        starty[plant][month] = {}
        for crop in crops:
            var_name = f"slot:{plant}+month:{month}+ingredient{crop}"
            starty[plant][month][crop] = model.NewBoolVar(var_name)

# decision variable whole cycle
growing = {}
for plant in range(PLANT):
    growing[plant] = {}
    for month in range(NUM_MONTHS):
        growing[plant][month] = {}
        for crop in crops:
            var_name = f"slot:{plant}+month:{month}+ingredient{crop}"
            growing[plant][month][crop] = model.NewBoolVar(var_name)

# Decision variable cookable dish
dish = []
for i in range(len(dishes)):
    var_name = f"dish:{i}"
    dish.append(model.NewBoolVar(var_name))

# starty is first of growing
for plant in range(PLANT):
    for s in range(NUM_MONTHS):
        for crop in crops:
            occupied_months = occ_months(s)
            for month in occupied_months:
                model.AddImplication(starty[plant][s][crop],growing[plant][month][crop])

# impose length of 3
for plant in range(PLANT):
    for month in range(NUM_MONTHS):
        for crop in crops:
            poss_start = [(month - i) % NUM_MONTHS for i in range(CYCLES)]
            model.Add(sum(starty[plant][start][crop] for start in poss_start) >= 1).OnlyEnforceIf(growing[plant][month][crop])
            model.Add(sum(starty[plant][start][crop] for start in poss_start) == 0).OnlyEnforceIf(growing[plant][month][crop].Not())

# no simultaneous start
for month in range(NUM_MONTHS):
    curr_plants = []
    for plant in range(PLANT):
        for crop in crops:
            curr_plants.append(starty[plant][month][crop])
    model.Add(sum(curr_plants) <= 1)

# no same plants
for plant in range(PLANT):
    for month in range(NUM_MONTHS):
        model.Add(sum(growing[plant][month][crop] for crop in crops) <= 1)

# avoid multiple of the same crops being grown
for plant in range(PLANT):
    for s_month1 in range(NUM_MONTHS):
        for s_month2 in range(s_month1 + 1, NUM_MONTHS):
            if overlap(s_month1, s_month2):
                for crop1 in crops:
                    for crop2 in crops:
                        model.AddBoolOr([starty[plant][s_month1][crop1].Not(), starty[plant][s_month2][crop2].Not()])

#count imposed constraints
constraint_c = 0
constraint_c += PLANT * NUM_MONTHS * len(crops) * CYCLES
constraint_c += PLANT * NUM_MONTHS * len(crops) * 2
constraint_c += NUM_MONTHS
constraint_c += PLANT * NUM_MONTHS

# Decision variable crop is available
available = {}
for month in range(NUM_MONTHS):
    available[month] = {}
    for crop in crops:
        var_name = f"available:{month}+{crop}"
        available[month][crop] = model.NewBoolVar(var_name)

# add available condition
for month in range(NUM_MONTHS):
    for crop in crops:
        curr_grow = [growing[slot][month][crop] for slot in range(PLANT)]
        model.Add(sum(curr_grow) >= 1).OnlyEnforceIf(available[month][crop])
        model.Add(sum(curr_grow) == 0).OnlyEnforceIf(available[month][crop].Not())

# Decision variable dish can be made in given month
dish_completable_in = {}
for dish_ind in range(len(dishes)):
    dish_completable_in[dish_ind] = {}
    for month in range(NUM_MONTHS):
        var_name = f"dish:{dish_ind}+month:{month}"
        dish_completable_in[dish_ind][month] = model.NewBoolVar(var_name)

# check all ingredients available
for dish_ind, (reward, ing) in enumerate(dishes):
    for month in range(NUM_MONTHS):
        ing_month = [available[month][ing] for ing in ing]
        model.Add(sum(ing_month) == len(ing)).OnlyEnforceIf(dish_completable_in[dish_ind][month])
        model.Add(sum(ing_month) < len(ing)).OnlyEnforceIf(dish_completable_in[dish_ind][month].Not())

# set max of 1
for dish_ind in range(len(dishes)):
    model.Add(sum(dish_completable_in[dish_ind][month] for month in range(NUM_MONTHS)) <= 1)

# connect to completable in
for dish_ind in range(len(dishes)):
    model.Add(sum(dish_completable_in[dish_ind][month] for month in range(NUM_MONTHS)) >= 1).OnlyEnforceIf(dish[dish_ind])
    model.Add(sum(dish_completable_in[dish_ind][month] for month in range(NUM_MONTHS)) == 0).OnlyEnforceIf(dish[dish_ind].Not())

# maximise reward/dishes
to_max = []
for dish_ind, (reward, ingredients) in enumerate(dishes):
    to_max.append(reward * dish[dish_ind])

model.Maximize(sum(to_max))

# solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60.0  # time limit (can be variable)
solver.parameters.log_search_progress = False  # Show progress off for submission
solver.parameters.num_search_workers = 16  # available threads (maximise if possible)
status = solver.Solve(model)

# optimal?
if status == cp_model.OPTIMAL: print("Optimal Solution/Time limit not reached")
elif status == cp_model.FEASIBLE: print("Some Solution/Time limit reached")
elif status == cp_model.INFEASIBLE: print("No dishes can be cooked") # should not occur
elif status == cp_model.MODEL_INVALID: print("Something went wrong")
else: print(f"{status}") #something else happened (debugging)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print(f"\nTotal dishes: {solver.ObjectiveValue()}")
    print(f"Time(in s): {solver.WallTime():.3f}")

    # Here starts the output
    # It is created with AI as explained in the Docs
    # The comments are added by hand to explain the steps taken by the AI
    print("\n" + "=" * 60)
    print("COMPLETED DISHES")
    print("=" * 60)

    # list all dishes that have been completed
    completed_dishes_list = []
    for dish_ind, (reward, ingredients) in enumerate(dishes):
        if solver.Value(dish[dish_ind]):
            completion_month = None
            for month in range(NUM_MONTHS):
                if solver.Value(dish_completable_in[dish_ind][month]):
                    completion_month = month
                    break

            completed_dishes_list.append({
                'dish_num': dish_ind + 1,
                'reward': reward,
                'ingredients': ingredients,
                'month': completion_month
            })

    if completed_dishes_list:
        for dish_info in completed_dishes_list:
            month_name = MONTHS[dish_info['month']] if dish_info['month'] is not None else "Unknown"
            print(f"Dish {dish_info['dish_num']}: {', '.join(dish_info['ingredients'])}")
            print(f"  Reward: {dish_info['reward']} points | Completed in: {month_name}")
    else:
        print("No dishes completed")

    print(f"\nTotal Reward: {solver.ObjectiveValue()}")

    # Create schedule visualization aka. timetable with crops
    print("\n" + "=" * 60)
    print("PLANTING SCHEDULE")
    print("=" * 60)

    # make a data structure containing all info
    schedule = {slot: {month: None for month in range(NUM_MONTHS)} for slot in range(PLANT)}

    for plant in range(PLANT):
        for month in range(NUM_MONTHS):
            for crop in crops:
                if solver.Value(growing[plant][month][crop]):
                    schedule[plant][month] = crop
                    break

    # header
    print("\n{:<10}".format("Slots"), end="")
    for month_name in MONTHS:
        print(f"{month_name:<12}", end="")
    print()
    print("-" * (10 + 12 * NUM_MONTHS))

    # insert the plants
    for plant in range(PLANT):
        print(f"Slot {plant + 1:<5}", end="")
        for month in range(NUM_MONTHS):
            crop_name = schedule[plant][month] if schedule[plant][month] else "-"
            print(f"{crop_name:<12}", end="")
        print()


else:
    print("\nNo solution.") #aka error