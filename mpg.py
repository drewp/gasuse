#!/usr/bin/python

"""
sort fillups better, using odometer
"""

import optparse, datetime
from rdflib.sparql.bison import GraphPattern
from rdflib.sparql import Debug
import rdflib.sparql.sparqlOperators as op
from rdflib import URIRef, Literal, Variable, BNode, Namespace, FileInputSource
from rdflib import RDF, RDFS

from gasuse import DC, DATE, GAS, DOLLAR, MILE, GALLON, TYPE

# http://wiki.python.org/moin/PythonDecoratorLibrary#EasyDumpofFunctionArguments
def dump_args(func):
    "This decorator dumps out the arguments passed to a function before calling it"
    argnames = func.func_code.co_varnames[:func.func_code.co_argcount]
    fname = func.func_name
    def echo_func(*args,**kwargs):
        print fname, ":", ', '.join(
            '%s=%r' % entry
            for entry in zip(argnames,args) + kwargs.items())
        ret = func(*args, **kwargs)
        print " ->", ret
        return ret
    return echo_func

def fillUps(graph, car):
    """sorted list of (date, fillUp)

    should sort by odometer if date is missing
    """
    ret = list(graph.queryd("""
      SELECT ?date ?odo ?fillUp WHERE { 
        ?fillUp a gas:FillUp ;
          gas:odometer ?odo ;
          dc:date ?date ;
          gas:car ?car .
      }""", initBindings={"car" : car}))
    ret.sort(key=lambda r: (str(r['date']), str(r['odo']))) # alpha sort on odo

    print "return %s fillups for %s" % (len(ret), car)
    return [(f['date'], f['fillUp']) for f in ret]

def shorten(graph, uri):
    for prefix, namespace in graph.namespaces():
        if uri.startswith(namespace):
            return "%s:%s" % (prefix, uri[len(namespace):])
    return uri

def dump(graph, subject):
    for p,o in sorted(graph.predicate_objects(f)):
        print "  %s: %s" % (shorten(graph, p), shorten(graph, o))

def milesOnFillup(graph, f, prevFillup):
    """
    number of miles driven between the last fillup and this one
    """
    val = graph.value
    try:
        # prefer odometer since it should have less per-reading error
        miles = (int(val(f, GAS['odometer'])) -
                 int(val(prevFillup, GAS['odometer'])))
        if miles < 1 or miles > 600:
            raise ValueError(miles)
        return miles
    except (ValueError, TypeError), e:
        return val(f, GAS['tripMeter'])

def floatVal(graph, subj, pred):
    v = graph.value(subj, pred)
    if v is None:
        raise TypeError(v)
    v = v.strip().rstrip('?')
    try:
        return float(v)
    except TypeError:
        print "%s %s %s" % (subj, pred, v)
        raise

def fillupStatements(graph, fillup, prevFillup):
    """
    statements about this fillup
    """
    stmts = set()
    val = graph.value
    miles = milesOnFillup(graph, fillup, prevFillup)

    if miles is not None:
        stmts.add((prevFillup, GAS['milesOnThisTank'],
                   Literal(miles, datatype=MILE)))
    else:
        miles = floatVal(graph, prevFillup, GAS['milesOnThisTank'])

    try:
        mpg = (miles / floatVal(graph, prevFillup, GAS['gallons']))
        stmts.add((prevFillup, GAS['mpgOnThisTank'],
                   Literal(mpg, datatype=TYPE['mpg'])))
    except (ValueError, TypeError), e:
        print vars()
        raise

    try:
        dpm = (float(val(val(prevFillup, GAS["gasPrice"]),
                         GAS["pricePerGallon"])) / mpg)
        stmts.add((prevFillup, GAS['dollarsPerMile'],
                   Literal(dpm, datatype=DOLLAR)))
    except (ValueError, TypeError), e:
        print vars()
        raise
    return stmts

def calcMpg(graph, car):
    prevFillup = None
    val = graph.value
        
    stmts = set()
    for d,f in fillUps(graph, car):
        if prevFillup is not None:
            try:
                stmts.update(fillupStatements(graph, f, prevFillup))
            except TypeError, e:
                print "skip prevFillup=%s, %s" % (prevFillup, e)
        prevFillup = f
        # these get queried in the next loop
        graph.add(stmts, context=GAS['computed'])

def clearComputed(graph):
    graph.subgraphClear(GAS['computed'])

if __name__ == '__main__':
    from rdflib.sparql.sparqlGraph import SPARQLGraph as Graph
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
