import uuid
from enum import Enum
import random
import configparser
import numpy as np
import pandas as pd

config = configparser.ConfigParser()
config.read('example.ini')
run001 = config['run001']
COHORT_SIZE: int = int(run001["COHORT_SIZE"])
SIM_YEARS: int = int(run001["SIM_YEARS"])
CYCLE_LENGTH: int = int(run001["CYCLE_LENGTH"])
CONCURRENCY_MALE: float = float(run001["CONCURRENCY_MALE"])
CONCURRENCY_FEMALE: float = float(run001["CONCURRENCY_FEMALE"])
PROB_MARITAL: float = float(run001["PROB_MARITAL"])
PROB_CASUAL: float = float(run001["PROB_CASUAL"])
PROB_SHORT_TERM: float = float(run001["PROB_SHORT_TERM"])
PROB_INSTANTANEOUS: float = float(run001["PROB_INSTANTANEOUS"])
DUR_MARITAL: int = int(run001["DUR_MARITAL"])
DUR_CASUAL: int = int(run001["DUR_CASUAL"])
DUR_SHORT_TERM: int = int(run001["DUR_SHORT_TERM"])
SEX_PER_MONTH_MARITAL: int = int(run001["SEX_PER_MONTH_MARITAL"])
SEX_PER_MONTH_CASUAL: int = int(run001["SEX_PER_MONTH_CASUAL"])
SEX_PER_MONTH_SHORT_TERM: int = int(run001["SEX_PER_MONTH_SHORT_TERM"])
SEXUAL_DEBUT_AGE: int = int(run001["SEXUAL_DEBUT_AGE"])
TRANSMISSION_PER_SEX_ACT: float = float(run001["TRANSMISSION_PER_SEX_ACT"])
BACKGROUND_MORTALITY_FEMALE = pd.read_csv(run001["BACKGROUND_MORTALITY_FEMALE_FILE"])
BACKGROUND_MORTALITY_MALE = pd.read_csv(run001["BACKGROUND_MORTALITY_MALE_FILE"])
AGE_OF_PARTNER = pd.read_csv(run001["AGE_OF_PARTNER_FILE"])
PARTNERSHIP_FORMATION = pd.read_csv(run001["PARTNERSHIP_FORMATION_FILE"])
INITIAL_POPULATION = pd.read_csv(run001["INITIAL_POPULATION_FILE"])

SIM_MONTHS = SIM_YEARS * CYCLE_LENGTH

# Create empty dictionary of men, women and list of partnerships

Women = dict()
Men = dict()
Partnerships = dict()


class Gender(Enum):
    MALE = 1
    FEMALE = 2


class HPVType(Enum):
    HPV16 = 1
    HPV18 = 2
    HPV31 = 3
    HPV33 = 4
    HPV45 = 5
    HPV52 = 6
    HPV58 = 7
    HPVoHR = 8
    HPVLR = 9


class HPVInfection:

    def __init__(self, type):
        self.HPVTimer = 1
        self.HPVType = type


class PartnershipType(Enum):
    MARITAL = 1
    SHORT_TERM = 2
    CASUAL = 3
    INSTANTANEOUS = 4


class Partnership:

    def __init__(
            self,
            partnershipid,
            womanid,
            manid,
            poisson_randomizer=lambda average: np.random.poisson(average, None)):
        self.infections = dict()
        self.partnership_id = partnershipid
        self.male_id = manid
        self.female_id = womanid
        self.partnership_duration = 1
        self.maxdur = 12 * poisson_randomizer(self.average_duration())
        self.sexacts = poisson_randomizer(self.sex_acts())
        for m in Men[manid].HPVinfections:
            self.infections[manid] = Men[manid].HPVinfections[m]
        for w in Women[womanid].HPVinfections:
            self.infections[womanid] = Women[womanid].HPVinfections[w]

    def average_duration(self):
        # Kinda expected that we'd never instantiate this class directly, but instead instantiate the subclasses
        # So this really shouldn't be hit. Probably should make it error
        return -1

    def sex_acts(self):
        return -1

    def check_serodiscordance(self):
        # Want to return the id, HPVinfections that are not duplicate in dictionary of infections
        pass

    def disease_transmission(self):
        pass

    def check_relationships(self):
        if Women[self.female_id].alive and Men[self.male_id].alive:
            if self.partnership_duration < self.maxdur:
                self.partnership_duration += 1
            else:
                self.dissolve_relationship()
        else:
            self.dissolve_relationship()

    def dissolve_relationship(self):
        Women[self.female_id].numpartners -= 1
        Men[self.male_id].numpartners -= 1
        del self


class Marriage(Partnership):
    def __init__(
            self,
            partnershipid,
            womanid,
            manid,
            duration_randomizer=lambda average: np.random.poisson(average, None)):
        super().__init__(partnershipid, womanid, manid, duration_randomizer)

    def average_duration(self):
        return DUR_MARITAL

    def sex_acts(self):
        return SEX_PER_MONTH_MARITAL


class CasualRelationship(Partnership):
    def __init__(
            self,
            partnershipid,
            womanid,
            manid,
            duration_randomizer=lambda average: np.random.poisson(average, None)):
        super().__init__(partnershipid, womanid, manid, duration_randomizer)

    def average_duration(self):
        return DUR_CASUAL

    def sex_acts(self):
        return SEX_PER_MONTH_CASUAL


class ShortTermRelationship(Partnership):
    def __init__(
            self,
            partnershipid,
            womanid,
            manid,
            duration_randomizer=lambda average: np.random.poisson(average, None)):
        super().__init__(partnershipid, womanid, manid, duration_randomizer)

    def average_duration(self):
        return DUR_SHORT_TERM

    def sex_acts(self):
        return SEX_PER_MONTH_SHORT_TERM


class InstantaneousRelationship(Partnership):
    def __init__(
            self,
            partnershipid,
            womanid,
            manid,
            duration_randomizer=lambda average: np.random.poisson(average, None)):
        super().__init__(partnershipid, womanid, manid, duration_randomizer)

    def average_duration(self):
        return 0

    def sex_acts(self):
        return 1


class Tracer:
    Concurrency = []


class Individual:
    single = True
    numpartners = 0
    alive = True
    HPVinfections = dict()

    def __init__(self,
                 gender,
                 age,
                 propconc,
                 identifier):
        self.age = age
        self.month_age = age * 12
        self.gender = gender
        self.concurrency = propconc
        self.id = identifier

    def acquire_HPV(self, type):
        infection_id = uuid.uuid1()
        self.HPVinfections[infection_id] = HPVInfection(type)

    def natural_history(self, mortality):
        rand = random.random()
        if rand < mortality.iloc[self.age]["mASR"]:
            self.alive = False
        else:
            self.month_age += 1
            if self.month_age % 12 == 0:
                self.age += 1

    def add_partner(self, partnerid, relationshiptype):
        partnership_id = uuid.uuid1()
        Partnerships[partnership_id] = relationshiptype(partnership_id, self.id, partnerid)
        self.numpartners += 1
        Men[partnerid].numpartners += 1

    def create_partnership(self):
        for _, m in Men.items():
            if m.alive:
                alreadypartner = False
                for key, val in Partnerships.items():
                    if val.female_id == self.id and val.male_id == m.id:
                        alreadypartner = True
                if not alreadypartner:
                    if (AGE_OF_PARTNER.iloc[self.age]["mean"] + AGE_OF_PARTNER.iloc[self.age]["SD"]) >= m.age >= (
                            AGE_OF_PARTNER.iloc[self.age]["mean"] - AGE_OF_PARTNER.iloc[self.age]["SD"]):
                        if m.single:
                            relationship_type = self.assign_partnership_type(True)
                            self.add_partner(m.id, relationship_type)
                            m.single = False
                            self.single = False
                            self.numpartners += 1
                            m.numpartners += 1
                            break
                        else:
                            rand = random.random()
                            if rand < m.concurrency:
                                relationship_type = self.assign_partnership_type(False)
                                self.add_partner(m.id, relationship_type)
                                m.single = False
                                self.numpartners += 1
                                self.single = False
                                m.numpartners += 1
                                break

    @staticmethod
    def assign_partnership_type(single):
        if single:
            rand = random.random()
            if rand < PROB_CASUAL:
                return CasualRelationship
            elif rand < (PROB_CASUAL + PROB_MARITAL):
                return Marriage
            elif rand < (PROB_CASUAL + PROB_MARITAL + PROB_SHORT_TERM):
                return ShortTermRelationship
            else:
                return InstantaneousRelationship
        else:
            rand = random.random()
            if rand < PROB_CASUAL:
                return CasualRelationship
            else:
                return InstantaneousRelationship

    def run_partnerships(self):
        if self.alive:
            if self.age >= SEXUAL_DEBUT_AGE:
                if self.single:
                    rand = random.random()
                    if rand < PARTNERSHIP_FORMATION.iloc[self.age]["Female"]:
                        self.create_partnership()
                else:
                    rand = random.random()
                    if rand < self.concurrency:
                        self.create_partnership()


if __name__ == "__main__":
    # Initialize men and women
    NumMen = []
    NumWomen = []
    ModelAges = INITIAL_POPULATION.shape[0]

    for k in range(ModelAges):
        NumMen.append(int(INITIAL_POPULATION.iloc[k]["MALE"] * COHORT_SIZE))
        NumWomen.append(int(INITIAL_POPULATION.iloc[k]["FEMALE"] * COHORT_SIZE))

    age = 1
    for x in NumWomen:
        for i in range(x):
            woman_id = uuid.uuid1()
            Women[woman_id] = Individual(Gender.FEMALE, age, CONCURRENCY_FEMALE, woman_id)
        age += 1

    age = 1
    for x in NumMen:
        for i in range(x):
            man_id = uuid.uuid1()
            Men[man_id] = Individual(Gender.MALE, age, CONCURRENCY_MALE, man_id)
        age += 1

    # Run simulation

    for months in range(SIM_MONTHS):

        for _, w in Women.items():
            w.natural_history(BACKGROUND_MORTALITY_FEMALE)

        for _, m in Men.items():
            m.natural_history(BACKGROUND_MORTALITY_MALE)

        for _, w in Women.items():
            w.run_partnerships()

        for _, p in Partnerships.items():
            p.check_relationships()

        # Check who died in cycle, remove from dictionary, replace with new birth

        DeadWomen = []

        for j, w in Women.items():
            if not w.alive:
                DeadWomen.append(j)

        for w in DeadWomen:
            del Women[w]
            woman_id = uuid.uuid1()
            Women[woman_id] = Individual(Gender.FEMALE, 0, CONCURRENCY_FEMALE, woman_id)

        DeadMen = []

        for j, m in Men.items():
            if not m.alive:
                DeadMen.append(j)

        for m in DeadMen:
            del Men[m]
            man_id = uuid.uuid1()
            Men[man_id] = Individual(Gender.MALE, 0, CONCURRENCY_MALE, man_id)
