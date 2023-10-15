""" The maturity of a typical speaker required for expected mastery of a term. """
from enum import Enum

class Level(Enum):
    """ The maturity of a typical speaker required for expected mastery of a term. """
    TO = 'toddlers'
    PS = 'pre-school'
    KG = 'kindergarten'
    G1 = 'grade 1'
    G2 = 'grade 2'
    G3 = 'grade 3'
    G4 = 'grade 4'
    G5 = 'grade 5'
    G6 = 'grade 6'
    G7 = 'grade 7'
    G8 = 'grade 8'
    G9 = 'grade 9'
    G10 = 'grade 10'
    G11 = 'grade 11'
    G12 = 'grade 12'
    CO = 'college student'
    AD = 'adult'
    PR = 'professional'
    EX = 'expert'