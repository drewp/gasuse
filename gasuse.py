
from rdflib import URIRef, Literal, BNode, Namespace

DC = Namespace("http://purl.org/dc/elements/1.1/")
DATE = URIRef("http://www.w3.org/2001/XMLSchema#date")
GAS = Namespace("http://bigasterisk.com/2005/11/gasuse/")

# should be standard datatypes, but I can't find any
DOLLAR = GAS["type/dollar"]
MILE = GAS["type/mile"]
GALLON = GAS["type/gallon"]

def dateFromAmerican(mm_dd_yyyy):
    return Literal("%s-%s-%s" % (mm_dd_yyyy[6:10],
                                 mm_dd_yyyy[:2],
                                 mm_dd_yyyy[3:5]), datatype=DATE)
