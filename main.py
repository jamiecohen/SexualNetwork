import sys
import uuid
from sexualnetwork import Data, Woman, Man, Timer


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
            Women[woman_id] = Woman(age, woman_id, Model_Data, 0)
            Women[woman_id].seed_HPV()  # Seed HPV
        age += 1

    age = 1
    for x in NumMen:
        for _ in range(x):
            man_id = uuid.uuid1()
            Men[man_id] = Man(age, man_id, Model_Data, 0)
            Men[man_id].seed_HPV()  # Seed HPV
        age += 1

    # Run simulation to burn in partnerships

    t = Timer()
    t.start()

    for i in range(Model_Data.SIM_MONTHS):

        for _, w in Women.items():
            if w.alive:
                w.natural_history()

        for _, m in Men.items():
            if m.alive:
                m.natural_history()

        for _, w in Women.items():
            if w.alive:
                w.run_partnerships(Men, Partnerships)

        for _, p in Partnerships.items():
            p.check_relationships()

        dead_women = 0

        for j, w in Women.items():
            if w.alive:
                w.month_age += 1
                w.simmonth += 1
                if w.month_age % 12 == 0:
                    w.age += 1
                if w.simmonth % 12 == 0:
                    w.simyear += 1
            else:
                dead_women += 1

        for _ in range(dead_women):
            woman_id = uuid.uuid1()
            Women[woman_id] = Woman(0, woman_id, Model_Data, i)

        dead_men = 0

        for j, m in Men.items():
            if m.alive:
                m.month_age += 1
                m.simmonth += 1
                if m.month_age % 12 == 0:
                    m.age += 1
                if m.simmonth % 12 == 0:
                    m.simyear += 1
            else:
                dead_men += 1

        for _ in range(dead_men):
            man_id = uuid.uuid1()
            Men[man_id] = Man(0, man_id, Model_Data, i)

    t.stop()
    Model_Data.write_infections(Model_Data.incidentinfections)


if __name__ == "__main__":
    main()
