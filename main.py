import sys
import uuid
from sexualnetwork import Data, Woman, Man


def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "example.ini"

    Model_Data = Data(filename)

    # Create dictionary of men, women and partnerships
    Women = dict()
    Men = dict()
    Partnerships = dict()

    # Initialize men and women
    NumMen = []
    NumWomen = []
    ModelAges = Model_Data.INITIAL_POPULATION.shape[0]

    for k in range(ModelAges):
        NumMen.append(int(Model_Data.INITIAL_POPULATION.iloc[k]["MALE"] * Model_Data.COHORT_SIZE))
        NumWomen.append(int(Model_Data.INITIAL_POPULATION.iloc[k]["FEMALE"] * Model_Data.COHORT_SIZE))

    age = 1
    for x in NumWomen:
        for _ in range(x):
            woman_id = uuid.uuid1()
            Women[woman_id] = Woman(age, woman_id, Model_Data, Men, Partnerships)
            Women[woman_id].seed_HPV()  # Seed HPV
        age += 1

    age = 1
    for x in NumMen:
        for _ in range(x):
            man_id = uuid.uuid1()
            Men[man_id] = Man(age, man_id, Model_Data)
            Men[man_id].seed_HPV()  # Seed HPV
        age += 1

    # Run simulation

    for _ in range(Model_Data.SIM_MONTHS):

        for _, w in Women.items():
            if w.alive:
                w.natural_history()

        for _, m in Men.items():
            if m.alive:
                m.natural_history()

        for _, w in Women.items():
            if w.alive:
                w.run_partnerships()

        for _, p in Partnerships.items():
            p.check_relationships()

        # Check who died in cycle, replace with new birth

        dead_women = 0

        for j, w in Women.items():
            if not w.alive:
                dead_women += 1

        for _ in range(dead_women):
            woman_id = uuid.uuid1()
            Women[woman_id] = Woman(0, woman_id, Model_Data, Men, Partnerships)

        dead_men = 0

        for j, m in Men.items():
            if not m.alive:
                dead_men += 1

        for _ in range(dead_men):
            man_id = uuid.uuid1()
            Men[man_id] = Man(0, man_id, Model_Data)


if __name__ == "__main__":
    main()
