#!/usr/bin/python

"""
This module contains codes to extract information from a checklist evaluation to create a "traffic light" display

At its core is a SPARQL-driven templating engine, which will be used initially to create a JSON representation
of RDF information from the checklist evaluation, which can be used to easily construct an HTML rendering of
the required "traffic light"

Report definition structure:

report-defn     = { 'report': template-item }   // May add more later

template-item   = sequence | query-template     // Bindings to date are fed down into template-item processing

sequence        = [ template-item, ... ]

query-template  = { 'query':    sparql-query [None],
                    'output':   python-format-string [None],
                    'report':   template-item [None],
                    'sep':      python-format-string [None],
                    'alt':      python-format-string [None],
                    'max':      integer [no limit],
                  }
"""

import sys
import collections
import rdflib

def generate_report(repdefn, rdfgraph, initvars, outstr):
    """
    Generates a report defined to the supplied output stream.
    
    repdefn     is a structure that defines the report to be generated,
                whose structure is as outlined above.
    rdfgraph    is an RDF graph containing data that will be used to 
                populate the report
    initvars    an initial set of variable bindings that are fed into the
                report generation query process
    outstr      a stream to which the report is written
    """
    item = repdefn['report']
    process_item(repdefn['report'], rdfgraph, initvars, outstr)
    return

def process_item(repitem, rdfgraph, initvars, outstr):
    """
    Processes a report template item to the supplied output stream.
    
    repitem     is the report template item to be processed
    rdfgraph    is an RDF graph containing data that will be used to 
                populate the report
    initvars    an initial set of variable bindings that are fed into the
                report generation query process
    outstr      a stream to which the report is written
    """
    if isinstance(repitem, dict):
        # Single query template
        process_query(repitem, rdfgraph, initvars, outstr)
    elif isinstance(repitem, collections.Iterable):
        # Iterable list of items - join query results from sequence
        for q in repitem:
            process_query(q, rdfgraph, initvars, outstr)
    else:
        raise "Unexpected value for report template item %s"%(repr(repitem))
    return

def takefirst(n, iter):
    count = 0;
    for i in iter:
        count += 1
        if count > n: break
        yield i
    return

def process_query(qitem, rdfgraph, initvars, outstr):
    """
    Process a single query+template structure
    """
    # do query
    query       = qitem.get('query', None)
    newbindings = [initvars]
    if query:
        resp = rdfgraph.query(qitem['query'],initBindings=initvars)
        if resp.type == 'ASK':
            if not resp.askAnswer: newbindings = []
        elif resp.type == 'SELECT':
            newbindings = resp.bindings
        else:
            raise "Unexpected query response type %s"%resp.type
    # Apply limit to result set
    maxrepeat   = qitem.get('max', sys.maxsize)
    newbindings = takefirst(maxrepeat, newbindings)
    # Process each binding in rsult set
    output  = qitem.get('output', None)
    report  = qitem.get('report', None)
    alt     = qitem.get('alt', None)
    sep     = qitem.get('sep', None)
    nextsep = None
    for b in newbindings:
        newbinding = initvars
        for k in b:
            if not isinstance(k,rdflib.BNode):
                newbinding[str(k)] = str(b[k])
        if nextsep:
            outstr.write(nextsep%newbinding)
        if output:
            outstr.write(output%newbinding)
        if report:
            process_item(report, rdfgraph, newbinding, outstr)
        usealt  = False
        nextsep = sep
    if alt:
        outstr.write(alt%initvars)
    return

# End.