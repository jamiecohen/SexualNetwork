import uuid
from enum import Enum
import random
import time
import numpy as np
import pandas as pd

np.seterr(divide='ignore', invalid='ignore')


class Gender(Enum):
    MALE = 1
    FEMALE = 2


class HPVType(Enum):
    HPV16 = 0
    HPV18 = 1
    HPVoHR = 2
    HPVLR = 3


class Data:

    def __init__(self, section):
        self.COHORT_SIZE: int = int(section["COHORT_SIZE"])
        self.SIM_YEARS: int = int(section["SIM_YEARS"])
        self.SIM_MONTHS = self.SIM_YEARS * 12
        self.CYCLE_LENGTH: int = int(section["CYCLE_LENGTH"])
        self.CONCURRENCY_MALE: float = float(section["CONCURRENCY_MALE"])
        self.CONCURRENCY_FEMALE: float = float(section["CONCURRENCY_FEMALE"])
        self.PROB_MARITAL: float = float(section["PROB_MARITAL"])
        self.PROB_CASUAL: float = float(section["PROB_CASUAL"])
        self.PROB_SHORT_TERM: float = float(section["PROB_SHORT_TERM"])
        self.PROB_INSTANTANEOUS: float = float(section["PROB_INSTANTANEOUS"])
        self.DUR_MARITAL: int = int(section["DUR_MARITAL"])
        self.DUR_CASUAL: int = int(section["DUR_CASUAL"])
        self.DUR_SHORT_TERM: int = int(section["DUR_SHORT_TERM"])
        self.SEX_PER_MONTH_MARITAL: int = int(section["SEX_PER_MONTH_MARITAL"])
        self.SEX_PER_MONTH_CASUAL: int = int(section["SEX_PER_MONTH_CASUAL"])
        self.SEX_PER_MONTH_SHORT_TERM: int = int(section["SEX_PER_MONTH_SHORT_TERM"])
        self.SEXUAL_DEBUT_AGE: int = int(section["SEXUAL_DEBUT_AGE"])
        self.TRANSMISSION_PER_SEX_ACT: float = float(section["TRANSMISSION_PER_SEX_ACT"])
        self.NATURAL_IMMUNITY_HPV16: float = float(section["NATURAL_IMMUNITY_HPV16"])
        self.NATURAL_IMMUNITY_HPV18: float = float(section["NATURAL_IMMUNITY_HPV18"])
        self.NATURAL_IMMUNITY_HPVoHR: float = float(section["NATURAL_IMMUNITY_HPVoHR"])
        self.NATURAL_IMMUNITY_HPVLR: float = float(section["NATURAL_IMMUNITY_HPVLR"])
        self.BACKGROUND_MORTALITY_FEMALE = pd.read_csv(section["BACKGROUND_MORTALITY_FEMALE_FILE"])
        self.BACKGROUND_MORTALITY_MALE = pd.read_csv(section["BACKGROUND_MORTALITY_MALE_FILE"])
        self.AGE_OF_PARTNER = pd.read_csv(section["AGE_OF_PARTNER_FILE"])
        self.PARTNERSHIP_FORMATION = pd.read_csv(section["PARTNERSHIP_FORMATION_FILE"])
        self.INITIAL_POPULATION = pd.read_csv(section["INITIAL_POPULATION_FILE"])
        self.HPV_CLEARANCE = pd.read_csv(section["HPV_CLEARANCE_FILE"])
        self.incidentinfections = [[0] * self.SIM_YEARS for _ in range(self.INITIAL_POPULATION.shape[0])]
        self.prevalentinfections = [[0] * self.SIM_YEARS for _ in range(self.INITIAL_POPULATION.shape[0])]
        self.noinfection = [[0] * self.SIM_YEARS for _ in range(self.INITIAL_POPULATION.shape[0])]
        self.totalalive = [[0] * self.SIM_YEARS for _ in range(self.INITIAL_POPULATION.shape[0])]

    def count_incident_infections(self, infection):
        self.incidentinfections[infection.InfectionAge][Individual.year] += 1

    def count_infection_denom(self, age):
        self.noinfection[age][Individual.year] += 1

    def count_prevalent_infections(self, age):
        self.prevalentinfections[age][Individual.year] += 1

    def count_total_alive(self, age):
        self.totalalive[age][Individual.year] += 1

    def write_infections(self, run):
        incidence = np.divide(self.incidentinfections, self.noinfection)
        prevalence = np.divide(self.prevalentinfections, self.totalalive)
        np.savetxt('incidence_' + run + '.csv', incidence, fmt='%f')
        np.savetxt('prevalence_' + run + '.csv', prevalence, fmt='%f')


class Infection:

    def __init__(self):
        self.Type = None
        self.Timer = 1
        self.HPVTransmission = None
        self.NaturalImmunity = None

    def get_clearance(self):
        return -1

    def check_serodiscordance(self, person, sexacts):
        discordant = True
        infection_keys = [key for key, value in person.Infections.items() if value.Type == self.Type]
        if len(infection_keys) > 0:
            discordant = False

        if discordant:
            self.transmit_infection(person, sexacts)

    def transmit_infection(self, person, sexacts):
        pass

    def get_hpv_transmission(self, person):
        infection_keys = [key for key, value in person.ClearedInfections.items() if value.Type == self.Type]
        if len(infection_keys) > 0:
            history = True
        else:
            history = False
        if history:
            return self.HPVTransmission * self.NaturalImmunity
        else:
            return self.HPVTransmission


class HPV16Infection(Infection):

    def __init__(self, data, age):
        super(HPV16Infection, self).__init__()
        self.Type = HPVType.HPV16
        self.HPVClearance = data.HPV_CLEARANCE["HPV16"]
        self.HPVTransmission = data.TRANSMISSION_PER_SEX_ACT
        self.InfectionAge = age
        self.NaturalImmunity = data.NATURAL_IMMUNITY_HPV16

    def get_clearance(self):
        return self.HPVClearance.iloc[self.Timer]

    def transmit_infection(self, person, sexacts):
        for _ in range(sexacts):
            rand = random.random()
            if rand < self.get_hpv_transmission(person):
                person.acquire_infection(HPV16Infection)
                break


class HPV18Infection(Infection):

    def __init__(self, data, age):
        super(HPV18Infection, self).__init__()
        self.Type = HPVType.HPV18
        self.HPVClearance = data.HPV_CLEARANCE["HPV18"]
        self.HPVTransmission = data.TRANSMISSION_PER_SEX_ACT
        self.InfectionAge = age
        self.NaturalImmunity = data.NATURAL_IMMUNITY_HPV18

    def get_clearance(self):
        return self.HPVClearance.iloc[self.Timer]

    def transmit_infection(self, person, sexacts):
        for _ in range(sexacts):
            rand = random.random()
            if rand < self.get_hpv_transmission(person):
                person.acquire_infection(HPV18Infection)
                break


class HPVoHRInfection(Infection):

    def __init__(self, data, age):
        super(HPVoHRInfection, self).__init__()
        self.Type = HPVType.HPVoHR
        self.HPVClearance = data.HPV_CLEARANCE["HPVoHR"]
        self.HPVTransmission = data.TRANSMISSION_PER_SEX_ACT
        self.InfectionAge = age
        self.NaturalImmunity = data.NATURAL_IMMUNITY_HPVoHR

    def get_clearance(self):
        return self.HPVClearance.iloc[self.Timer]

    def transmit_infection(self, person, sexacts):
        for _ in range(sexacts):
            rand = random.random()
            if rand < self.get_hpv_transmission(person):
                person.acquire_infection(HPVoHRInfection)
                break


class HPVLRInfection(Infection):

    def __init__(self, data, age):
        super(HPVLRInfection, self).__init__()
        self.Type = HPVType.HPVLR
        self.HPVClearance = data.HPV_CLEARANCE["HPVLR"]
        self.HPVTransmission = data.TRANSMISSION_PER_SEX_ACT
        self.InfectionAge = age
        self.NaturalImmunity = data.NATURAL_IMMUNITY_HPVLR

    def get_clearance(self):
        return self.HPVClearance.iloc[self.Timer]

    def transmit_infection(self, person, sexacts):
        for _ in range(sexacts):
            rand = random.random()
            if rand < self.get_hpv_transmission(person):
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
        self.partnership_id = partnershipid
        self.male = man
        self.male_id = man.id
        self.female = woman
        self.female_id = woman.id
        self.partnership_duration = 1
        self.maxdur = 12 * poisson_randomizer(self.average_duration())
        self.sexacts = poisson_randomizer(self.sex_acts())
        self.active = True

    def average_duration(self):
        # Kinda expected that we'd never instantiate this class directly, but instead instantiate the subclasses
        # So this really shouldn't be hit. Probably should make it error
        return -1

    def sex_acts(self):
        return -1

    def check_serodiscordance(self):
        for _, inf in self.male.Infections.items():
            inf.check_serodiscordance(self.female, self.sexacts)
        for _, inf in self.female.Infections.items():
            inf.check_serodiscordance(self.male, self.sexacts)

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
        self.female.partnershipid.remove(self.partnership_id)
        self.male.partnershipid.remove(self.partnership_id)
        self.male.numpartners -= 1
        self.active = False


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
    month = 0
    year = 0

    def __init__(self,
                 age,
                 identifier,
                 data):
        self.single = True
        self.numpartners = 0
        self.partnershipid = []
        self.alive = True
        self.Infections = dict()
        self.ClearedInfections = dict()
        self.age = age
        self.month_age = age * 12
        self.id = identifier
        self.data = data
        self.ageofpartner = data.AGE_OF_PARTNER
        self.sexualdebutage = data.SEXUAL_DEBUT_AGE
        self.partnershipformation = data.PARTNERSHIP_FORMATION

    def acquire_infection(self, infectiontype):
        infection_id = uuid.uuid1()
        self.Infections[infection_id] = infectiontype(self.data, self.age)
        self.data.count_incident_infections(self.Infections[infection_id])

    def clear_infection(self, infection_id):
        self.ClearedInfections[infection_id] = self.Infections[infection_id]
        del self.Infections[infection_id]

    def infection_natural_history(self):
        infections_to_clear = []
        for infid, inf in self.Infections.items():
            prob_clear = inf.get_clearance()
            rand = random.random()
            if rand < prob_clear:
                infections_to_clear.append(infid)
            else:
                inf.Timer += 1

        for inf in infections_to_clear:
            self.clear_infection(inf)

    def seed_infection(self):
        if 17 < self.age < 30:
            rand = random.random()
            if rand < 0.05:
                self.acquire_infection(HPVoHRInfection)
            elif rand < 0.15:
                self.acquire_infection(HPV16Infection)
            elif rand < 0.22:
                self.acquire_infection(HPV18Infection)
            elif rand < 0.3:
                self.acquire_infection(HPVLRInfection)

    def natural_history(self):
        rand = random.random()
        if rand < self.get_mortality():
            self.alive = False
        else:
            self.data.count_total_alive(self.age)
            if len(self.Infections) == 0:
                self.data.count_infection_denom(self.age)
            else:
                self.data.count_prevalent_infections(self.age)
            self.infection_natural_history()

    def get_mortality(self):
        pass


class Woman(Individual):
    def __init__(
            self,
            age,
            identifier,
            data):
        super(Woman, self).__init__(age, identifier, data)
        self.gender = Gender.FEMALE
        self.mortality = data.BACKGROUND_MORTALITY_FEMALE
        self.concurrency = data.CONCURRENCY_FEMALE

    def get_mortality(self):
        return self.mortality.iloc[self.age]["mASR"]

    def add_partner(self, man, relationshiptype, partnerships):
        partnership_id = uuid.uuid1()
        partnerships[partnership_id] = relationshiptype(partnership_id, self, man, self.data)
        self.numpartners += 1
        self.partnershipid.append(partnership_id)
        man.partnershipid.append(partnership_id)
        man.numpartners += 1

    def check_eligibility(self, man, partnerships):
        if man.alive:
            alreadypartner = False
            for key in self.partnershipid:
                if partnerships[key].female_id == self.id and partnerships[key].male_id == man.id:
                    if partnerships[key].active:
                        alreadypartner = True
            return not alreadypartner
        else:
            return False

    def get_age_of_partner(self):
        age = np.random.poisson(self.ageofpartner.iloc[self.age]["mean"], None)
        while age > 75:
            age = np.random.poisson(self.ageofpartner.iloc[self.age]["mean"], None)
        return age

    def create_partnership(self, lookup_table, partnerships):
        ageofpartner = self.get_age_of_partner()
        keys = list(lookup_table[ageofpartner].keys())
        random.shuffle(keys)
        # lookup by eligibility
        for m in keys:
            if self.check_eligibility(lookup_table[ageofpartner][m], partnerships):
                if lookup_table[ageofpartner][m].numpartners == 0:
                    relationship_type = self.assign_partnership_type(True)
                    self.add_partner(lookup_table[ageofpartner][m], relationship_type, partnerships)
                    lookup_table[ageofpartner][m].single = False
                    self.single = False
                    self.numpartners += 1
                    lookup_table[ageofpartner][m].numpartners += 1
                    break
                else:
                    rand = random.random()
                    if rand < lookup_table[ageofpartner][m].concurrency:
                        relationship_type = self.assign_partnership_type(False)
                        self.add_partner(lookup_table[ageofpartner][m], relationship_type, partnerships)
                        lookup_table[ageofpartner][m].single = False
                        self.numpartners += 1
                        self.single = False
                        lookup_table[ageofpartner][m].numpartners += 1
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

    def run_partnerships(self, lookup_table, partnerships):
        if self.sexualdebutage <= self.age <= 74:
            if self.numpartners == 0:
                rand = random.random()
                if rand < self.partnershipformation.iloc[self.age]["Female"]:
                    self.create_partnership(lookup_table, partnerships)
            else:
                rand = random.random()
                if rand < self.concurrency:
                    self.create_partnership(lookup_table, partnerships)


class Man(Individual):
    def __init__(
            self,
            age,
            identifier,
            data):
        super(Man, self).__init__(age, identifier, data)
        self.gender = Gender.MALE
        self.mortality = data.BACKGROUND_MORTALITY_MALE
        self.concurrency = data.CONCURRENCY_MALE

    def get_mortality(self):
        return self.mortality.iloc[self.age]["mASR"]


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class Timer:
    def __init__(self):
        self._start_time = None

    def start(self):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")
