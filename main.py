import sys
import uuid
from sexualnetwork import Data, Woman, Man, Individual, Timer


def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "example.ini"

    model_data = Data(filename)

    # Create dictionary of men, women and partnerships
    women = dict()
    men = dict()
    dead_women = dict()
    dead_men = dict()
    partnerships = dict()
    inactive_partnerships = dict()
    lookup_table = dict()

    # Initialize men and women

    num_men = []
    num_women = []
    model_ages = model_data.INITIAL_POPULATION.shape[0]

    for k in range(model_ages):
        num_men.append(int(model_data.INITIAL_POPULATION.iloc[k]["MALE"] * model_data.COHORT_SIZE))
        num_women.append(int(model_data.INITIAL_POPULATION.iloc[k]["FEMALE"] * model_data.COHORT_SIZE))

    age = 0
    for x in num_women:
        for _ in range(x):
            woman_id = uuid.uuid1()
            women[woman_id] = Woman(age, woman_id, model_data)
            women[woman_id].seed_infection()  # Seed HPV
        age += 1

    age = 0
    for x in num_men:
        lookup_table[age] = dict()
        for _ in range(x):
            man_id = uuid.uuid1()
            men[man_id] = Man(age, man_id, model_data)
            lookup_table[age][man_id] = men[man_id]
            men[man_id].seed_infection()  # Seed HPV
        age += 1

    # Run simulation

    t = Timer()
    t.start()

    for month in range(model_data.SIM_MONTHS):

        for _, w in women.items():
            w.natural_history()
            if w.alive:
                w.run_partnerships(lookup_table, partnerships)

        for _, m in men.items():
            m.natural_history()

        for _, p in partnerships.items():
            p.check_relationships()

        partnerships_to_delete = [keys for keys in partnerships if not partnerships[keys].active]

        for key in partnerships_to_delete:
            inactive_partnerships[key] = partnerships[key]
            del partnerships[key]

        women_to_delete = []

        for j, w in women.items():
            if w.alive:
                w.month_age += 1
                if w.month_age % 12 == 0:
                    w.age += 1
            else:
                dead_women[j] = w
                women_to_delete.append(j)

        for key in women_to_delete:
            del women[key]
            woman_id = uuid.uuid1()
            women[woman_id] = Woman(0, woman_id, model_data)

        men_to_delete = []

        for j, m in men.items():
            if m.alive:
                m.month_age += 1
                if m.month_age % 12 == 0:
                    m.age += 1
                    lookup_table[m.age][j] = m
                    del lookup_table[m.age-1][j]
            else:
                dead_men[j] = m
                men_to_delete.append(j)
                del lookup_table[m.age][j]

        for key in men_to_delete:
            del men[key]
            man_id = uuid.uuid1()
            men[man_id] = Man(0, man_id, model_data)
            lookup_table[0][man_id] = men[man_id]

        Individual.month += 1
        if Individual.month % 12 == 0:
            Individual.year += 1

    t.stop()
    model_data.write_infections()


if __name__ == "__main__":
    main()
