#!/usr/bin/python

"""
sort fillups better, using odometer
"""

import optparse, datetime
from rdflib.sparql.sparqlGraph import SPARQLGraph as Graph
from rdflib.sparql.bison import GraphPattern
from rdflib.sparql import Debug
import rdflib.sparql.sparqlOperators as op
from rdflib import URIRef, Literal, Variable, BNode, Namespace, FileInputSource
from rdflib import RDF, RDFS

from gasuse import DC, DATE, GAS, DOLLAR, MILE, GALLON, TYPE

def fillUps(graph, car):
    """sorted list of (date, fillUp)

    should sort by odometer if date is missing
    """
    ret = list(graph.query("""SELECT ?date ?odo ?fillUp WHERE { 
                      ?fillUp a gas:FillUp; gas:odometer ?odo; dc:date ?date; gas:car ?car .
   }""", initNs=dict(gas=GAS, dc=DC), initBindings={Variable("?car") : car}))
    ret.sort() # alpha sort on odo
    print "return %s fillups for %s" % (len(ret), car)
    return [(f[0], f[2]) for f in ret]

def shorten(graph, uri):
    for prefix, namespace in graph.namespaces():
        if uri.startswith(namespace):
            return "%s:%s" % (prefix, uri[len(namespace):])
    return uri

def dump(graph, subject):
    for p,o in sorted(graph.predicate_objects(f)):
        print "  %s: %s" % (shorten(graph, p), shorten(graph, o))

def calcMpg(graph, car):
    prevFillup = None
    val = graph.value
    for d,f in fillUps(graph, car):
        if prevFillup is not None:
            miles = None
            try:
                # prefer odometer since it should have less per-reading error
                miles = (int(val(f, GAS['odometer'])) -
                         int(val(prevFillup, GAS['odometer'])))
                if miles < 1 or miles > 600:
                    raise ValueError
            except (ValueError, TypeError), e:
                try:
                    miles = val(f, GAS['tripMeter'])
                except (ValueError, TypeError), e:
                    pass
            if miles is not None:
                graph.add((prevFillup, GAS['milesOnThisTank'],
                           Literal(miles, datatype=MILE)))

            try:
                mpg = (float(val(prevFillup,
                                 GAS['milesOnThisTank'])) /
                       float(val(prevFillup, GAS['gallons'])))
                graph.add((prevFillup, GAS['mpgOnThisTank'],
                           Literal(mpg, datatype=TYPE['mpg'])))
            except (ValueError, TypeError), e:
                pass

            try:
                dpm = (float(val(val(prevFillup, GAS["gasPrice"]),
                                 GAS["pricePerGallon"])) /
                       float(val(prevFillup, GAS["mpgOnThisTank"])))
                graph.add((prevFillup, GAS['dollarsPerMile'],
                           Literal(dpm, datatype=DOLLAR)))
            except (ValueError, TypeError), e:
                pass
        prevFillup = f
    

if __name__ == '__main__':
    graph = Graph()
    graph.parse(FileInputSource(open("gas.rdf")))

    print "parsed"

    knownNames = graph.query("?shortName",
                             GraphPattern([
        ("?station", RDFS.Class, GAS['Station']),
        ("?station", GAS['shortName'], "?shortName"),
        ("?station", GAS['shortAddress'], "?shortAddress"),
        ]))

    print "known stations:",
    for name in knownNames:
        res = graph.query("?station",
                          GraphPattern([("?station", GAS['shortName'], name)]))
        print "%s (%d)," % (name, len(res)),
    print

    #print "%d known stations: %s" % (len(knownStations), 

    Debug = True

    car = GAS['car/drewCivicHybrid']

    calcMpg(graph, car)

    for d,f in fillUps(graph, car):
        print d, shorten(graph, graph.value(f, GAS['gasStation']))
        dump(graph, f)

    #    pattern.addConstraint(op.ge("?date", datetime.date(2004, 11, 1)))
    #    pattern.addConstraint(op.le("?date", datetime.date(2004, 12, 31)))
