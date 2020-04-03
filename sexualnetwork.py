import uuid
from enum import Enum
import random
import sys
import configparser
import numpy as np
import pandas as pd


class Gender(Enum):
    MALE = 1
    FEMALE = 2


class HPVType(Enum):
    HPV16 = 0
    HPV18 = 1
    HPVoHR = 2
    HPVLR = 3


class Data:
    def __init__(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        run001 = config['run001']
        self.COHORT_SIZE: int = int(run001["COHORT_SIZE"])
        self.SIM_YEARS: int = int(run001["SIM_YEARS"])
        self.SIM_MONTHS = self.SIM_YEARS * 12
        self.CYCLE_LENGTH: int = int(run001["CYCLE_LENGTH"])
        self.CONCURRENCY_MALE: float = float(run001["CONCURRENCY_MALE"])
        self.CONCURRENCY_FEMALE: float = float(run001["CONCURRENCY_FEMALE"])
        self.PROB_MARITAL: float = float(run001["PROB_MARITAL"])
        self.PROB_CASUAL: float = float(run001["PROB_CASUAL"])
        self.PROB_SHORT_TERM: float = float(run001["PROB_SHORT_TERM"])
        self.PROB_INSTANTANEOUS: float = float(run001["PROB_INSTANTANEOUS"])
        self.DUR_MARITAL: int = int(run001["DUR_MARITAL"])
        self.DUR_CASUAL: int = int(run001["DUR_CASUAL"])
        self.DUR_SHORT_TERM: int = int(run001["DUR_SHORT_TERM"])
        self.SEX_PER_MONTH_MARITAL: int = int(run001["SEX_PER_MONTH_MARITAL"])
        self.SEX_PER_MONTH_CASUAL: int = int(run001["SEX_PER_MONTH_CASUAL"])
        self.SEX_PER_MONTH_SHORT_TERM: int = int(run001["SEX_PER_MONTH_SHORT_TERM"])
        self.SEXUAL_DEBUT_AGE: int = int(run001["SEXUAL_DEBUT_AGE"])
        self.TRANSMISSION_PER_SEX_ACT: float = float(run001["TRANSMISSION_PER_SEX_ACT"])
        self.BACKGROUND_MORTALITY_FEMALE = pd.read_csv(run001["BACKGROUND_MORTALITY_FEMALE_FILE"])
        self.BACKGROUND_MORTALITY_MALE = pd.read_csv(run001["BACKGROUND_MORTALITY_MALE_FILE"])
        self.AGE_OF_PARTNER = pd.read_csv(run001["AGE_OF_PARTNER_FILE"])
        self.PARTNERSHIP_FORMATION = pd.read_csv(run001["PARTNERSHIP_FORMATION_FILE"])
        self.INITIAL_POPULATION = pd.read_csv(run001["INITIAL_POPULATION_FILE"])
        self.HPV_CLEARANCE = pd.read_csv(run001["HPV_CLEARANCE_FILE"])


class Infection:

    def __init__(self):
        self.Type = None
        self.Timer = 1

    def get_clearance(self):
        return -1

    def check_serodiscordance(self, person):
        discordant = True
        for id, inf in person.Infections.items():
            if inf.Type == self.Type:
                discordant = False
                break

        if discordant:
            self.transmit_infection(person)

    def transmit_infection(self, person):
        pass


class HPV16Infection(Infection):

    def __init__(self, data):
        super(HPV16Infection, self).__init__()
        self.Type = HPVType.HPV16
        self.HPVClearance = data.HPV_CLEARANCE["HPV16"]
        self.HPVTransmission = data.TRANSMISSION_PER_SEX_ACT

    def get_clearance(self):
        return self.HPVClearance.iloc[self.Timer]

    def transmit_infection(self, person):
        for sex in range(person.sexacts):
            rand = random.random()
            if rand < self.HPVTransmission:
                person.acquire_infection(HPV16Infection)
                break


class HPV18Infection(Infection):

    def __init__(self, data):
        super(HPV18Infection, self).__init__()
        self.Type = HPVType.HPV18
        self.HPVClearance = data.HPV_CLEARANCE["HPV18"]
        self.HPVTransmission = data.TRANSMISSION_PER_SEX_ACT

    def get_clearance(self):
        return self.HPVClearance.iloc[self.Timer]

    def transmit_infection(self, person):
        for sex in range(person.sexacts):
            rand = random.random()
            if rand < self.HPVTransmission:
                person.acquire_infection(HPV18Infection)
                break


class HPVoHRInfection(Infection):

    def __init__(self, data):
        super(HPVoHRInfection, self).__init__()
        self.Type = HPVType.HPVoHR
        self.HPVClearance = data.HPV_CLEARANCE["HPVoHR"]
        self.HPVTransmission = data.TRANSMISSION_PER_SEX_ACT

    def get_clearance(self):
        return self.HPVClearance.iloc[self.Timer]

    def transmit_infection(self, person):
        for sex in range(person.sexacts):
            rand = random.random()
            if rand < self.HPVTransmission:
                person.acquire_infection(HPVoHRInfection)
                break
                

class HPVLRInfection(Infection):

    def __init__(self, data):
        super(HPVLRInfection, self).__init__()
        self.Type = HPVType.HPVLR
        self.HPVClearance = data.HPV_CLEARANCE["HPVLR"]
        self.HPVTransmission = data.TRANSMISSION_PER_SEX_ACT

    def get_clearance(self):
        return self.HPVClearance.iloc[self.Timer]
        
    def transmit_infection(self, person):
        for sex in range(person.sexacts):
            rand = random.random()
            if rand < self.HPVTransmission:
                person.acquire_infection(HPVLRInfection)
                break


class PartnershipType(Enum):
    MARITAL = 1
    SHORT_TERM = 2
    CASUAL = 3
    INSTANTANEOUS = 4


class Partnership:

    def __init__(
            self,
            partnershipid,
            woman,
            man,
            data,
            poisson_randomizer=lambda average: np.random.poisson(average, None)):
        self.data = data
        self.unique_m_infections = []
        self.unique_f_infections = []
        self.partnership_id = partnershipid
        self.male = man
        self.female = woman
        self.partnership_duration = 1
        self.maxdur = 12 * poisson_randomizer(self.average_duration())
        self.sexacts = poisson_randomizer(self.sex_acts())

    def average_duration(self):
        # Kinda expected that we'd never instantiate this class directly, but instead instantiate the subclasses
        # So this really shouldn't be hit. Probably should make it error
        return -1

    def sex_acts(self):
        return -1

    def check_serodiscordance(self):
        for id, inf in self.male.Infections.items():
            inf.check_serodiscordance(self.female)
        for id, inf in self.female.Infections.items():
            inf.check_serodiscordance(self.male)

    def check_relationships(self):
        if self.female.alive and self.male.alive:
            self.check_serodiscordance()
            if self.partnership_duration < self.maxdur:
                self.partnership_duration += 1
            else:
                self.dissolve_relationship()
        else:
            self.dissolve_relationship()

    def dissolve_relationship(self):
        self.female.numpartners -= 1
        self.male.numpartners -= 1
        del self


class Marriage(Partnership):
    def __init__(
            self,
            partnershipid,
            woman,
            man,
            duration_randomizer=lambda average: np.random.poisson(average, None)):
        super().__init__(partnershipid, woman, man, duration_randomizer)

    def average_duration(self):
        return self.data.DUR_MARITAL

    def sex_acts(self):
        return self.data.SEX_PER_MONTH_MARITAL


class CasualRelationship(Partnership):
    def __init__(
            self,
            partnershipid,
            woman,
            man,
            duration_randomizer=lambda average: np.random.poisson(average, None)):
        super().__init__(partnershipid, woman, man, duration_randomizer)

    def average_duration(self):
        return self.data.DUR_CASUAL

    def sex_acts(self):
        return self.data.SEX_PER_MONTH_CASUAL


class ShortTermRelationship(Partnership):
    def __init__(
            self,
            partnershipid,
            woman,
            man,
            duration_randomizer=lambda average: np.random.poisson(average, None)):
        super().__init__(partnershipid, woman, man, duration_randomizer)

    def average_duration(self):
        return self.data.DUR_SHORT_TERM

    def sex_acts(self):
        return self.data.SEX_PER_MONTH_SHORT_TERM


class InstantaneousRelationship(Partnership):
    def __init__(
            self,
            partnershipid,
            woman,
            man,
            duration_randomizer=lambda average: np.random.poisson(average, None)):
        super().__init__(partnershipid, woman, man, duration_randomizer)

    def average_duration(self):
        return 0

    def sex_acts(self):
        return 1


class Individual:
    single = True
    numpartners = 0
    alive = True
    Infections = dict()

    def __init__(self,
                 gender,
                 age,
                 identifier,
                 data,
                 men,
                 partnerships):
        self.age = age
        self.month_age = age * 12
        self.gender = gender
        self.id = identifier
        self.data = data
        if self.gender == Gender.MALE:
            self.mortality = data.BACKGROUND_MORTALITY_MALE
            self.concurrency = data.CONCURRENCY_MALE
        else:
            self.mortality = data.BACKGROUND_MORTALITY_FEMALE
            self.concurrency = data.CONCURRENCY_FEMALE
        self.ageofpartner = data.AGE_OF_PARTNER
        self.sexualdebutage = data.SEXUAL_DEBUT_AGE
        self.partnershipformation = data.PARTNERSHIP_FORMATION
        self.list_of_men = men
        self.list_of_partnerships = partnerships

    def acquire_infection(self, hpvtype):
        infection_id = uuid.uuid1()
        self.Infections[infection_id] = hpvtype(self.data)

    def clear_hpv(self, infection_id):
        del self.Infections[infection_id]

    def hpv_natural_history(self):
        for infid, inf in self.Infections.items():
            prob_clear = inf.get_clearance()
            rand = random.random()
            if rand < prob_clear:
                self.clear_hpv(infid)
            else:
                inf.Timer += 1

    def natural_history(self):
        rand = random.random()
        if rand < self.mortality.iloc[self.age]["mASR"]:
            self.alive = False
        else:
            self.hpv_natural_history()
            self.month_age += 1
            if self.month_age % 12 == 0:
                self.age += 1

    def add_partner(self, man, relationshiptype):
        partnership_id = uuid.uuid1()
        self.list_of_partnerships[partnership_id] = relationshiptype(partnership_id, self, man, self.data)
        self.numpartners += 1
        man.numpartners += 1

    def create_partnership(self):
        for _, m in self.list_of_men.items():
            if m.alive:
                alreadypartner = False
                for key, val in self.list_of_partnerships.items():
                    if val.female_id == self.id and val.male_id == m.id:
                        alreadypartner = True
                if not alreadypartner:
                    if (self.ageofpartner.iloc[self.age]["mean"] + self.ageofpartner.iloc[self.age]["SD"]) >= m.age >= (
                            self.ageofpartner.iloc[self.age]["mean"] - self.ageofpartner.iloc[self.age]["SD"]):
                        if m.single:
                            relationship_type = self.assign_partnership_type(True)
                            self.add_partner(m, relationship_type)
                            m.single = False
                            self.single = False
                            self.numpartners += 1
                            m.numpartners += 1
                            break
                        else:
                            rand = random.random()
                            if rand < m.concurrency:
                                relationship_type = self.assign_partnership_type(False)
                                self.add_partner(m, relationship_type)
                                m.single = False
                                self.numpartners += 1
                                self.single = False
                                m.numpartners += 1
                                break

    def assign_partnership_type(self, single):
        if single:
            rand = random.random()
            if rand < self.data.PROB_CASUAL:
                return CasualRelationship
            elif rand < (self.data.PROB_CASUAL + self.data.PROB_MARITAL):
                return Marriage
            elif rand < (self.data.PROB_CASUAL + self.data.PROB_MARITAL + self.data.PROB_SHORT_TERM):
                return ShortTermRelationship
            else:
                return InstantaneousRelationship
        else:
            rand = random.random()
            if rand < self.data.PROB_CASUAL:
                return CasualRelationship
            else:
                return InstantaneousRelationship

    def run_partnerships(self):
        if self.alive:
            if self.age >= self.sexualdebutage:
                if self.single:
                    rand = random.random()
                    if rand < self.partnershipformation.iloc[self.age]["Female"]:
                        self.create_partnership()
                else:
                    rand = random.random()
                    if rand < self.concurrency:
                        self.create_partnership()


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
        for i in range(x):
            woman_id = uuid.uuid1()
            Women[woman_id] = Individual(Gender.FEMALE, age, woman_id, Model_Data, Men, Partnerships)
            # Seed HPV
            if 17 < age < 30:
                rand = random.random()
                if rand < 0.3:
                    Women[woman_id].acquire_infection(HPV16Infection)
        age += 1

    age = 1
    for x in NumMen:
        for i in range(x):
            man_id = uuid.uuid1()
            Men[man_id] = Individual(Gender.MALE, age, man_id, Model_Data, Men, Partnerships)
            # Seed HPV
            if 17 < age < 30:
                rand = random.random()
                if rand < 0.3:
                    Men[man_id].acquire_infection(HPV16Infection)
        age += 1

    # Run simulation

    for months in range(Model_Data.SIM_MONTHS):

        for _, w in Women.items():
            w.natural_history()

        for _, m in Men.items():
            m.natural_history()

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
            Women[woman_id] = Individual(Gender.FEMALE, 0, woman_id, Model_Data, Men, Partnerships)

        DeadMen = []

        for j, m in Men.items():
            if not m.alive:
                DeadMen.append(j)

        for m in DeadMen:
            del Men[m]
            man_id = uuid.uuid1()
            Men[man_id] = Individual(Gender.MALE, 0, man_id, Model_Data, Men, Partnerships)


if __name__ == "__main__":
    main()
