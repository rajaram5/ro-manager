# ro_manifest.py

"""
Research Object manifest read, write, decode functions
"""

#import sys
#import os
#import os.path
#import re
#import urlparse
import logging

log = logging.getLogger(__name__)

#import rdflib
#import rdflib.namespace
#from rdflib import URIRef, Namespace, BNode
#from rdflib import Literal

from rocommand import ro_manifest
from rocommand.ro_manifest import RDF, RDFS, ORE
import ro_minim
from ro_minim import MINIM

def evaluate(rodir, minim, target, purpose):
    """
    Evaluate a RO against a minimuminformation model for a particular
    purpose with respect to a particular targetresource.

    rodir       is the name of a directory containing the RO to be analyzed
    minim       is a URI-reference (relative to the RO, or absolute) of the
                minim description to be used.
    target      is a URI-reference (relative to the RO, or absolute) of a 
                target resource with respect to which the evaluation is
                performed.
    purpose     is a string that identifies a purpose w.r.t. the target for
                which completeness will be evaluated.
                
    'target' and 'purpose' are ued together to select a particular minim Model
    that will be used for the evaluation.  For example, to evaluate whether an 
    RO is sufficiently complete to support creation (a purpose) of a specified
    output file (a target).
    
    There are two main steps to the evaluation process:
    1. locate the minim model constraint for the target resource and purpose
    2. evaluate the RO against the selected model.
    
    The result indicates a summary and details of the analysis; e.g.
    { 'summary':       [MINIM.fullySatisfies, MINIM.nominallySatisfies, MINIM.minimallySatisfies]
    , 'missingMust':   []
    , 'missingShould': []
    , 'missingMay':    []
    , 'rouri':          rouri
    , 'minimuri':       minim
    , 'target':         target
    , 'purpose':        purpose
    , 'constrainturi':  constraint['uri']
    , 'modeluri':       model['uri']
    }
    """
    # Locate the constraint model requirements
    rouri        = ro_manifest.getRoUri(rodir)
    rograph      = ro_manifest.readManifestGraph(rodir)
    minimuri     = ro_manifest.getComponentUri(rodir, minim)
    minimgraph   = ro_minim.readMinimGraph(minimuri)
    constraint   = ro_minim.getConstraint(minimgraph, rodir, target, purpose)
    assert constraint != None, "Missing minim:Constraint for target %s, purpose %s"%(target, purpose)
    model        = ro_minim.getModel(minimgraph, constraint['model'])
    assert model != None, "Missing minim:Model for target %s, purpose %s"%(target, purpose)
    requirements = ro_minim.getRequirements(minimgraph, model['uri'])
    # Evaluate the individual model requirements
    reqeval = []
    for r in requirements:
        if 'datarule' in r:
            satisfied = (rouri, ORE.aggregates, r['datarule']['aggregates']) in rograph
            reqeval.append((r,satisfied))
            log.debug("- %s: %s"%(repr((rouri, ORE.aggregates, r['datarule']['aggregates'])), satisfied))
    # Evaluate overall satisfaction of model
    sat_levels = (
        { 'MUST':   MINIM.minimallySatisfies
        , 'SHOULD': MINIM.nominallySatisfies
        , 'MAY':    MINIM.fullySatisfies
        })
    eval_result = (
        { 'summary':        []
        , 'missingMust':    []
        , 'missingShould':  []
        , 'missingMay':     []
        , 'rodir':          rodir
        , 'rouri':          rouri
        , 'minimuri':       minimuri
        , 'target':         target
        , 'purpose':        purpose
        , 'constrainturi':  constraint['uri']
        , 'modeluri':       model['uri']
        })
    for (r, satisfied) in reqeval:
        if not satisfied:
            if r['level'] == "MUST":
                eval_result['missingMust'].append(r)
                sat_levels['MUST']   = False
                sat_levels['SHOULD'] = False
                sat_levels['MAY']    = False
            elif r['level'] == "SHOULD":
                eval_result['missingShould'].append(r)
                sat_levels['SHOULD'] = False
                sat_levels['MAY']    = False
            elif r['level'] == "MAY":
                eval_result['missingMay'].append(r)
                sat_levels['MAY'] = False
    eval_result['summary'] = [ sat_levels[k] for k in sat_levels if sat_levels[k] ]
    return eval_result

def format(eval_result, options, ostr):
    """
    Formats a completeness evaluation report, and writes it to the supplied stream.
    
    eval_result is the result of evaluation from ro_eval_completeness.evaluate
    options     a dictionary that provides options to control the formatting (see below)
    ostr        is a stream to which the formatted result is written

    options currently has just one field:
    options['detail'] = "summary" or "full"
    
    More options may be introduced later.
    """
    any  = ["summary","full"]
    full = ["full"]
    def put(detail, line):
        if options['detail'] in detail:
            ostr.write(line)
            ostr.write("\n")
        return
    put(any, "Research Object %(rodir)s:"%eval_result)
    summary_text= ( "Fully complete"     if MINIM.fullySatisfies     in eval_result['summary'] else
                    "Nominally complete" if MINIM.nominallySatisfies in eval_result['summary'] else
                    "Minimally complete" if MINIM.minimallySatisfies in eval_result['summary'] else
                    "Incomplete")
    put(any, summary_text+" for %(purpose)s of resource %(target)s"%(eval_result))
    for m in eval_result['missingMust']:
        put(full, "Missing MUST resource:   %s"%(m['datarule']['aggregates']))
    for m in eval_result['missingShould']:
        put(full, "Missing SHOULD resource: %s"%(m['datarule']['aggregates']))
    for m in eval_result['missingMay']:
        put(full, "Missing MAY resource:    %s"%(m['datarule']['aggregates']))
    put(full, "Research object URI:     %(rouri)s"%(eval_result))
    put(full, "Minimum information URI: %(minimuri)s"%(eval_result))
    return

# End.