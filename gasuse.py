
from rdflib import URIRef, Literal, BNode, Namespace

DC = Namespace("http://purl.org/dc/elements/1.1/")
DATE = URIRef("http://www.w3.org/2001/XMLSchema#date")
GAS = Namespace("http://bigasterisk.com/2005/11/gasuse/")
SIOC = Namespace("http://rdfs.org/sioc/ns#")

# should be standard datatypes, but I can't find any

# they're in SUMO; see #swig logs from 2006-02-11. also use fragments
# for datatypes to avoid breaking cwm

TYPE = Namespace("http://bigasterisk.com/2005/11/gasuse/type#")
DOLLAR = TYPE["dollar"]
MILE = TYPE["mile"]
GALLON = TYPE["gallon"]

def dateFromAmerican(mm_dd_yyyy):
    return Literal("%s-%s-%s" % (mm_dd_yyyy[6:10],
                                 mm_dd_yyyy[:2],
                                 mm_dd_yyyy[3:5]), datatype=DATE)
