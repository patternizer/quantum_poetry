#! /usr/bin/ python

#-----------------------------------------------------------------------
# PROGRAM: app.py
#-----------------------------------------------------------------------
# Version 0.6
# 9 August, 2020
# Dr Michael Taylor
# https://patternizer.github.io
# patternizer AT gmail DOT com
#-----------------------------------------------------------------------

# ========================================================================
# SETTINGS
# ========================================================================
generate_anyons = True
generate_variants = True
generate_networkx_edges = True
generate_qubits = False
generate_erdos_parameter = False
generate_erdos_equivalence = False
generate_adjacency = False
qubit_logic = False
plot_branchpoint_table = False
plot_networkx_connections = False
plot_networkx_non_circular = False
plot_networkx_erdos_parameter = False
plot_networkx_erdos_equivalence = False
plot_networkx_connections_branchpoints = False
plot_networkx_connections_dags = False
plot_variants = False
machine_learning = False
write_log = False
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# IMPORT PYTHON LIBRARIES
#------------------------------------------------------------------------------
import numpy as np
import pandas as pd
import scipy as sp
# import math
# math.log(N,2) for entropy calculations
import random
from random import randint
from random import randrange
# Text Parsing libraries:
import re
from collections import Counter
# Network Graph libraries:
import networkx as nx
from networkx.algorithms import approximation as aprx
# Plotting libraries:
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib import colors as mcol
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from skimage import io
import glob
from PIL import Image
# Silence library version notifications
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
# NLP Libraries
# ML Libraries
# App Deployment Libraries
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from flask import Flask
import json
import os
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# METHODS
#------------------------------------------------------------------------------
def word_in_line(word, line):
    """
    Check if word is in line
    word, line - str
    returns    - True if word in line, False if not
    """
    pattern = r'(^|[^\w]){}([^\w]|$)'.format(word)
    pattern = re.compile(pattern, re.IGNORECASE)
    matches = re.search(pattern, text)
    return bool(matches)

def discrete_colorscale(values, colors):
    """
    values  - categorical values
    colors  - rgb or hex colorcodes for len(values)-1
    eeturn  - discrete colorscale, tickvals, ticktext
    """    
    if len(values) != len(colors)+1:
        raise ValueError('len(values) should be = len(colors)+1')
    values = sorted(values)     
    nvalues = [(v-values[0])/(values[-1]-values[0]) for v in values]  #normalized values
    colorscale = []
    for k in range(len(colors)):
        colorscale.extend([[nvalues[k], colors[k]], [nvalues[k+1], colors[k]]])        
    tickvals = [((values[k]+values[k+1])/2.0) for k in range(len(values)-1)] 
    ticktext = [f'{int(values[k])}' for k in range(len(values)-1)]
    return colorscale, tickvals, ticktext

def rgb2hex(colorin):
    """
    Convert (r,g,b) to hex
    """
    r = int(colorin.split('(')[1].split(')')[0].split(',')[0])
    g = int(colorin.split('(')[1].split(')')[0].split(',')[1])
    b = int(colorin.split('(')[1].split(')')[0].split(',')[2])
    return "#{:02x}{:02x}{:02x}".format(r,g,b)

def parse_poem(input_file):
    """
    Text parsing of poem and construction of branchpoint array
    """

    print('parsing poem ...')

    # Store lines in a list

    linelist = []
    with open (input_file, 'rt') as f:      
        for line in f:   
            if len(line)>1: # ignore empty lines                  
                linelist.append(line.strip())   
            else:
                continue

    # Store text as a single string

    textstr = ''
    for i in range(len(linelist)):
        if i < len(linelist) - 1:
            textstr = textstr + linelist[i] + ' '
        else:
            textstr = textstr + linelist[i]
        
    # extract sentences into list 
    # (ignore last entry which is '' due to final full stop)
            
    sentencelist = textstr.split('.')[0:-1] 

    # Clean text and lower case all words

    str = textstr
    for char in '-.,\n':
        str = str.replace(char,' ')

    str = str.lower() 
    wordlist = str.split()

    # Store unique words in an array

    uniquewordlist = []
    for word in wordlist:           
        if word not in uniquewordlist:
            uniquewordlist.append(word)
                    
    # Word frequencies
        
    wordfreq = Counter(wordlist).most_common() # --> wordfreq[0][0] = 'the' and wordfreq[0][1] = '13'

    # Find branchpoints having word frequency > 1

    branchpointlist = []
    for word in range(len(wordfreq)-1):
        if wordfreq[word][1] > 1:
            branchpointlist.append(wordfreq[word][0])
        else:
            continue

    # Branchpoint index array

    maxbranches = wordfreq[0][1]
    branchpointarray = np.zeros((len(branchpointlist), maxbranches), dtype='int')
    for k in range(len(branchpointlist)):  
        index = []
        for i, j in enumerate(wordlist):
            if j == branchpointlist[k]:
                index.append(i)            
        branchpointarray[k,0:len(index)] = index

    # Filter out multiple branchpoint in single line only occurences
    # using word indices of branchpoints and line start and end indices

    lineindices = []    
    wordcount = 0
    for i in range(len(linelist)):
        linelen = len(linelist[i].split())
        lineindices.append([i, wordcount, wordcount+linelen-1])
        wordcount += linelen
                    
    mask = []
    branchlinearray = []        
    for i in range(np.size(branchpointarray, axis=0)): # i.e. nbranchpoints        
        branchpointindices = branchpointarray[i,:][branchpointarray[i,:]>0]
        linecounter = 0 
        for j in range(len(linelist)):                     
            branchpointcounter = 0
            for k in range(len(branchpointindices)):
                if branchpointindices[k] in np.arange(lineindices[j][1],lineindices[j][2]+1):
                    branchpointcounter += 1
                    branchlinearray.append([j,i,lineindices[j][1],branchpointindices[k],lineindices[j][2]])            
            if branchpointcounter > 0:
                linecounter += 1                    
        if linecounter < 2:
            mask.append(i)            

    a = np.array(branchpointarray)
    b = branchpointlist
    for i in range(len(mask)):
        a = np.delete(a,mask[i]-i,0)        
        b = np.delete(b,mask[i]-i,0)        
    branchpointarray = a
    branchpointlist = list(b)
 
    db = pd.DataFrame(branchpointarray)
    db.to_csv('branchpointarray.csv', sep=',', index=False, header=False, encoding='utf-8')

    return textstr, sentencelist, linelist, wordlist, uniquewordlist, wordfreq, branchpointlist, branchpointarray

def generate_branchpoint_colormap(wordfreq, nbranchpoints, nwords, branchpointarray):
    """
    Generate colormap using hexcolors for all branchpoints
    """

    print('generating branchpoint_colormap ...')

    freq = [ wordfreq[i][1] for i in range(len(wordfreq)) ]
    nlabels = nbranchpoints
    cmap = px.colors.diverging.Spectral
    cmap_idx = np.linspace(0,len(cmap)-1, nlabels, dtype=int)
    colors = [cmap[i] for i in cmap_idx]
    hexcolors = [ rgb2hex(colors[i]) for i in range(len(colors)) ]
    
    branchpoint_colormap = []
    for k in range(nwords):    
        branchpoint_colormap.append('lightgrey')              

    for j in range(np.size(branchpointarray, axis=0)): # i.e. nbranchpoints            
        for i in range(np.size(branchpointarray, axis=1)): # i.e. maxfreq
            branchpoint_colormap[branchpointarray[j,i]] = hexcolors[j] 

    return  branchpoint_colormap, hexcolors

def compute_networkx_edges(nwords, wordlist, branchpointarray):
            
    print('computing_networkx_edges ...')
    
    # Construct edgelist, labellist
    
    edgelist = [(i,i+1) for i in range(nwords-1)]
    labellist = [{i : wordlist[i]} for i in range(nwords)]

    df = pd.DataFrame()
    
    G = nx.Graph()
    G.add_edges_from(edgelist)
    for node in G.nodes():
        G.nodes[node]['label'] = labellist[node]

    edge_colormap = []
    for k in range(nwords-1):
        edge_colormap.append('lightgrey')              
        
    for j in range(np.size(branchpointarray, axis=0)): # i.e. nbranchpoints        
        branchpointedges = []
        for i in range(np.size(branchpointarray, axis=1)): # i.e. maxfreq
            branchpointindices = branchpointarray[j,:]
            connections = branchpointindices[(branchpointindices != branchpointindices[i]) & (branchpointindices > 0)]
            for k in range(len(connections)):
                if branchpointindices[i] > 0:
                    branchpointedges.append([branchpointindices[i], connections[k]])
        G.add_edges_from(branchpointedges)        

#        for l in range(int(len(branchpointedges)/2)): # NB 2-driectional edges
#            edge_colormap.append(hexcolors[j])
    nedges = len(G.edges)

    # Generate non-circular form of the networkx graph

    N = nx.Graph()
    N.add_edges_from(edgelist)
    for j in range(np.size(branchpointarray, axis=0)): # i.e. nbranchpoints        
        branchpointedges = []
        for i in range(np.size(branchpointarray, axis=1)): # i.e. maxfreq
            branchpointindices = branchpointarray[j,:]
            connections = branchpointindices[(branchpointindices != branchpointindices[i]) & (branchpointindices > 0)]
            for k in range(len(connections)):
                if branchpointindices[i] > 0:
                    branchpointedges.append([branchpointindices[i], connections[k]])
        N.add_edges_from(branchpointedges)        
    N.remove_edges_from(edgelist)
    N_degrees = [degree for node,degree in dict(N.degree()).items()] # degree of nodes
    notbranchpoints = [ node for node,degree in dict(N.degree()).items() if degree == 0 ] # each node in circular graph has 2 neighbours at start
            
    return nedges, notbranchpoints, G, N
    
def compute_erdos_parameter(nwords, nedges):
    """
    Compute Erdos-Renyi parameter estimate
    """
    
    print('computing_erdos_parameter ...')

    edgelist = [(i,i+1) for i in range(nwords-1)]
    for connectivity in np.linspace(0,1,1000001):
        random.seed(42)
        E = nx.erdos_renyi_graph(nwords, connectivity)
        erdosedges = len(E.edges)
        if erdosedges == (nedges-len(edgelist)):            
#            print("{0:.6f}".format(connectivity))
#            print("{0:.6f}".format(erdosedges))
            nerdosedges = len(E.edges)
            return nerdosedges, connectivity, E
#            break
    nerdosedges = len(E.edges)    
   
    return nerdosedges, connectivity, E

def compute_erdos_equivalence(nwords, nedges, N, notbranchpoints):
    """
    Compute Erdos-Renyi equivalence probability
    """

    print('computing_erdos_equivalence ...')

    # Compare Erdos-Renyi graph edges in reduced networks (branchpoint network)

    N.remove_nodes_from(notbranchpoints)
    mapping = { np.array(N.nodes)[i]:i for i in range(len(N.nodes)) }
    H = nx.relabel_nodes(N,mapping)                
    maxdiff = len(H.edges)
    iterations = 100000
    for i in range(iterations+1):

        E = nx.erdos_renyi_graph(len(H.nodes), connectivity)
        diff = H.edges - E.edges        
        if len(diff) < maxdiff:
            maxdiff = len(diff)
            commonedges = H.edges - diff      
            pEquivalence = i/iterations
            Equivalence = E
            
    return commonedges, pEquivalence, Equivalence

def compute_anyons(linelist, wordlist, branchpointarray):
    """
    Anyon construction: braiding
    """

    print('generating_anyons ...')

    # Compute start and end word indices for each line of the poem

    lineindices = []    
    wordcount = 0
    for i in range(len(linelist)):
        linelen = len(linelist[i].split())
        lineindices.append([i, wordcount, wordcount+linelen-1])
        wordcount += linelen
                    
    # For each branchpoint find line index and word indices of line start, branchpoint and line end
    # branchlinearray: [line, branchpoint, wordstart, wordbranchpoint, wordend] 

    branchlinearray = []        
    for i in range(np.size(branchpointarray, axis=0)): # i.e. nbranchpoints        
        branchpointindices = branchpointarray[i,:][branchpointarray[i,:]>0]
        for j in range(len(linelist)):                     
            for k in range(len(branchpointindices)):
                if branchpointindices[k] in np.arange(lineindices[j][1],lineindices[j][2]+1):                   
                    branchlinearray.append([j,i,lineindices[j][1],branchpointindices[k],lineindices[j][2]])
    
    # Filter out multiple branchpoint in single line only occurences

    a = np.array(branchlinearray)
    mask = []
    for i in range(len(branchlinearray)-2):
        if (a[i,0] == a[i+1,0]) & (a[i,1] == a[i+1,1]) & (a[i+2,1]!=a[i,1]):
            mask.append(i)
            mask.append(i+1)
    for i in range(len(mask)):
        a = np.delete(a,mask[i]-i,0)        
    branchlinearray = a[a[:,0].argsort()]

    # Filter out start of line and end of line occurring branchpoints

    a = np.array(branchlinearray)
    mask = []
    for i in range(len(branchlinearray)):
        if ((a[i,2] == a[i,3]) | (a[i,3] == a[i,4])):
            mask.append(i)
    for i in range(len(mask)):
        a = np.delete(a,mask[i]-i,0)        
    branchlinearray = a[a[:,0].argsort()]

    # Anyons
    
    anyonarray = []
    for i in range(len(linelist)):
        a = branchlinearray[branchlinearray[:,0]==i] 
        if len(a) == 0:
            break
        for j in range(len(a)):    
            anyon_pre = wordlist[a[j,2]:a[j,3]+1]
            b = branchlinearray[(branchlinearray[:,1]==a[j,1]) & (branchlinearray[:,0]!=a[j,0])]             

            #######################################################
            # For > 1 swaps, add additional anyon segment code here
            # + consider case of forward in 'time' constraint
            # + consider return to start line occurrence
            #######################################################

            if len(b) == 0:
                break
            for k in range(len(b)):
                anyon_post = wordlist[b[k,3]+1:b[k,4]+1]
                anyon = anyon_pre + anyon_post
                anyonarray.append( [i, b[k,0], branchpointlist[a[j,1]], anyon, a[j,2], a[j,3], a[j,4] ])

    df = pd.DataFrame(anyonarray)
    df.to_csv('anyonarray.csv', sep=',', index=False, header=False, encoding='utf-8')

    return anyonarray
    
def compute_variants(linelist, anyonarray):
    """
    Variant construction
    """

    print('generating_variants ...')

    # generate variants of the poem
    
    df = pd.DataFrame(anyonarray)

    allpoemsidx = []
    allpoems = []
    allidx = []
    nvariants = 0

    for i in range(len(linelist)):      
                
        a = df[df[0]==i]
        for j in range(len(a)):

            poem = []
            lineidx = []    
            lines = np.arange(len(linelist))    
        
            while len(lines)>0:
        
                # print(nvariants,i,j)
                
                if len(lines) == len(linelist):
                    linestart = a[0].values[j]
                    lineend = a[1].values[j]
                    branchpoint = a[2].values[j]                    
                else:
                    b = df[df[0]==lines[0]]
                    linestart = b[0].values[0]                
                    lineend = np.setdiff1d( np.unique(b[1].values), lineidx )[0]   
                    branchpoint = df[ (df[0]==linestart) & (df[1]==lineend) ][2].values[0]
                    
                lineidx.append(linestart)    
                lineidx.append(lineend)
                branchpointstartpre = df[ (df[0]==linestart) & (df[1]==lineend) & (df[2]==branchpoint) ][4].values[0]
                branchpointstart = df[ (df[0]==linestart) & (df[1]==lineend) & (df[2]==branchpoint) ][5].values[0]
                branchpointstartpro = df[ (df[0]==linestart) & (df[1]==lineend) & (df[2]==branchpoint) ][6].values[0]
                branchpointendpre = df[ (df[0]==lineend) & (df[1]==linestart) & (df[2]==branchpoint) ][4].values[0]
                branchpointend = df[ (df[0]==lineend) & (df[1]==linestart) & (df[2]==branchpoint) ][5].values[0]
                branchpointendpro = df[ (df[0]==lineend) & (df[1]==linestart) & (df[2]==branchpoint) ][6].values[0]                
                allidx.append([nvariants, linestart, lineend, branchpoint, branchpointstartpre, branchpointstart, branchpointstartpro])
                allidx.append([nvariants, lineend, linestart, branchpoint, branchpointendpre, branchpointend, branchpointendpro])
                poem.append(df[ (df[0]==linestart) & (df[1]==lineend) & (df[2]==branchpoint) ][3].values[0])
                poem.append(df[ (df[0]==lineend) & (df[1]==linestart) & (df[2]==branchpoint) ][3].values[0])
                lines = np.setdiff1d(lines,lineidx)   
         
            nvariants += 1                                         
            poemsorted = []
            for k in range(len(lineidx)):
                poemsorted.append(poem[lineidx.index(k)])
            allpoems.append(poemsorted)
            allpoemsidx.append(lineidx)                 
            dp = pd.DataFrame(poemsorted)
            dp.to_csv('poem'+'_'+"{0:.0f}".format(nvariants-1).zfill(3)+'.csv', sep=',', index=False, header=False, encoding='utf-8')
 
    di = pd.DataFrame(allpoemsidx)    
    di.to_csv('poem_allidx.csv', sep=',', index=False, header=False, encoding='utf-8')
    da = pd.DataFrame(allpoems)
    da.to_csv('poem_all.csv', sep=',', index=False, header=False, encoding='utf-8')
    dl = pd.DataFrame(allidx)
    dl.to_csv('allidx.csv', sep=',', index=False, header=False, encoding='utf-8')

    return nvariants, allpoemsidx, allpoems, allidx

def generate_qubits():
    """
    Qubit contruction
    """    

    print('generating_qubits ...')

def qubit_logic():
    """
    Apply gates to Bell states
    """    

    print('applying logic gates ...')

def machine_learning():
    """
    Feature extraction
    """    

    print('extracting features ...')
#------------------------------------------------------------------------------

#----------------------------
# LOAD POEM
#----------------------------
"""
Poem to generate quantum variants from
"""
#input_file = 'poem.txt'
input_file = 'poem-v1.txt'

textstr, sentencelist, linelist, wordlist, uniquewordlist, wordfreq, branchpointlist, branchpointarray = parse_poem(input_file)

# Counts
        
nsentences = len(sentencelist)    # --> 4    
nlines = len(linelist)            # --> 8
nwords = len(wordlist)            # --> 98
nunique = len(uniquewordlist)     # --> 59
nbranchpoints = len(branchpointlist)            # --> 20

if generate_networkx_edges == True:
    nedges, notbranchpoints, G, N = compute_networkx_edges(nwords, wordlist, branchpointarray)
if generate_anyons == True:
    anyonarray = compute_anyons(linelist, wordlist, branchpointarray)
if generate_variants == True:
    nvariants, allpoemsidx, allpoems, allidx = compute_variants(linelist, anyonarray)
if generate_qubits == True:
    print('generating_qubits ...')
if generate_erdos_parameter == True:
    nerdosedges, connectivity, E = compute_erdos_parameter(nwords, nedges)
if compute_erdos_equivalence == True:
    commonedges, pEquivalence, Equivalence = compute_erdos_equivalence(nwords, nedges, N, notbranchpoints)
if qubit_logic == True:
    print('applying logic gates ...')
if machine_learning == True:
    print('extracting features ...')
     
# -----------------------------------------------------------------------------
branchpoint_colormap, hexcolors = generate_branchpoint_colormap(wordfreq, nbranchpoints, nwords, branchpointarray)
# -----------------------------------------------------------------------------

if plot_branchpoint_table == True:
    
    print('plotting_branchpoint_table ...')

    fig, ax = plt.subplots(figsize=(15,10))
    plt.plot(np.arange(0,len(wordlist)), np.zeros(len(wordlist)))
    for k in range(len(branchpointlist)):  
        plt.plot(np.arange(0,len(wordlist)), np.ones(len(wordlist))*k, color='black')
        a = branchpointarray[k,:]
        vals = a[a>0]
        plt.scatter(vals, np.ones(len(vals))*k, label=branchpointlist[k], s=100, facecolors=hexcolors[k], edgecolors='black') 
        
    xticks = np.arange(0, len(wordlist)+0, step=10)
    xlabels = np.array(np.arange(0, len(wordlist), step=10).astype('str'))
    yticks = np.arange(0, len(branchpointlist), step=1)
    ylabels = np.array(np.arange(0, len(branchpointlist), step=1).astype('str'))
    plt.xticks(ticks=xticks, labels=xlabels)  # Set label locations
    plt.yticks(ticks=yticks, labels=ylabels)  # Set label locations
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.xlabel('word n in text', fontsize=20)
    plt.ylabel('branchpoint k in text (>1 connection)', fontsize=20)
    plt.title('Branch Analysis Plot', fontsize=20)
    plt.gca().invert_yaxis()    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=12)
    plt.savefig('branchplot.png')
    plt.close(fig)

if plot_networkx_connections == True:

    print('plotting_networkx_connections ...')
    
    fig, ax = plt.subplots(figsize=(15,10))    
    nx.draw_circular(G, node_color=branchpoint_colormap, node_size=300, linewidths=0.5, font_size=12, font_weight='normal', with_labels=True)
    plt.title('Networkx (circularly connected): N(edges)=' + "{0:.0f}".format(len(G.edges)), fontsize=20)
    plt.savefig('networkx.png')
    plt.close(fig)

if plot_networkx_non_circular == True:

    print('plotting_networkx_non_circular ...')

    fig, ax = plt.subplots(figsize=(15,10))
    nx.draw_circular(N, node_color=branchpoint_colormap, node_size=300, linewidths=0.5, font_size=12, font_weight='normal', with_labels=True)
    plt.title('Networkx (non-circularly connected): N(edges)=' + "{0:.0f}".format(len(N.edges)), fontsize=20)
    plt.savefig('networkx_non_circular.png')

if plot_networkx_erdos_parameter == True:
    
    print('plotting_networkx_erdos ...')

    fig, ax = plt.subplots(figsize=(15,10))
    nx.draw_circular(E, node_color=branchpoint_colormap, node_size=300, linewidths=0.5, font_size=12, font_weight='normal', with_labels=True)
    plt.title('Erdős-Rényi Model: p=' + "{0:.6f}".format(connectivity) + ', N(edges)=' + "{0:.0f}".format(nerdosedges), fontsize=20)
    plt.savefig('networkx_erdos.png')
    plt.close(fig)
        
if plot_networkx_erdos_equivalence == True:
    
    print('plotting_networkx_erdos_equivalence ...')

    fig, ax = plt.subplots(figsize=(15,10))
    nx.draw_circular(Eequivalence, node_color='lightgrey', node_size=300, linewidths=0.5, font_size=12, font_weight='normal', with_labels=True)
    plt.title('Erdős-Rényi Model (equivalent): N(common edges)=' + "{0:.0f}".format(len(N.edges)-len(diff)), fontsize=20)
    plt.savefig('networkx_erdos_equivalence.png')
        
if plot_variants == True:

    print('plotting_variants ...')
    
    di = pd.DataFrame(allpoemsidx)
    da = pd.DataFrame(allpoems)
    dl = pd.DataFrame(allidx)

    for i in range(nvariants):

        connectorstart = []
        connectorend = []

        fig, ax = plt.subplots(figsize=(15,10))
        for k in range(len(linelist)):  
            
            branchpoint = dl[(dl[0]==i)&(dl[1]==k)][3].values[0]                
            linestart = dl[(dl[0]==i)&(dl[1]==k)][1].values[0]
            lineend = dl[(dl[0]==i)&(dl[1]==k)][2].values[0]
            plt.scatter(np.arange(0,len(linelist[k].split())), np.ones(len(linelist[k].split()))*k, color='black')
            if linestart < lineend:
                x1 = np.arange(0, dl[(dl[0]==i)&(dl[1]==k)][5].values[0] - dl[(dl[0]==i)&(dl[1]==k)][4].values[0]+1)
                x2 = np.arange(dl[(dl[0]==i)&(dl[1]==k)][5].values[0] - dl[(dl[0]==i)&(dl[1]==k)][4].values[0]+1, dl[(dl[0]==i)&(dl[1]==k)][6].values[0]-dl[(dl[0]==i)&(dl[1]==k)][4].values[0]+1)                               
                y1 = np.ones(len(x1))*k
                y2 = np.ones(len(x2))*k    
                plt.plot(x1,y1,'blue')
                plt.plot(x2,y2,'red')
                plt.scatter(x1[-1], y1[-1], s=100, facecolors=hexcolors[branchpointlist.index(branchpoint)], edgecolors='black')      
                connectorstart.append([linestart, x1[-1], y1[-1]])                
                connectorend.append([lineend, x2[0], y2[0]])     
            else:
                x3 = np.arange(dl[(dl[0]==i)&(dl[1]==k)][5].values[0] - dl[(dl[0]==i)&(dl[1]==k)][4].values[0]+1, dl[(dl[0]==i)&(dl[1]==k)][6].values[0]-dl[(dl[0]==i)&(dl[1]==k)][4].values[0]+1)                               
                x4 = np.arange(0, dl[(dl[0]==i)&(dl[1]==k)][5].values[0] - dl[(dl[0]==i)&(dl[1]==k)][4].values[0]+1)               
                y3 = np.ones(len(x3))*k
                y4 = np.ones(len(x4))*k
                plt.plot(x3,y3,'blue')
                plt.plot(x4,y4,'red')       
                plt.scatter(x4[-1], y4[-1], s=100, facecolors=hexcolors[branchpointlist.index(branchpoint)], edgecolors='black')                
                connectorstart.append([linestart, x3[0], y3[0]])                
                connectorend.append([lineend, x4[-1], y4[-1]])     

        for k in range(len(linelist)):  
            
            branchpoint = dl[(dl[0]==i)&(dl[1]==k)][3].values[0]                
            linestart = dl[(dl[0]==i)&(dl[1]==k)][1].values[0]
            lineend = dl[(dl[0]==i)&(dl[1]==k)][2].values[0]
            print(k, linestart, lineend)
            if linestart < lineend:
                x1 = connectorstart[linestart][1]
                y1 = connectorstart[linestart][2]
                x2 = connectorend[lineend][1]+1
                y2 = connectorend[lineend][2]
                x = [x1,x2]
                y = [y1,y2]                
                plt.plot(x,y,'blue')
            else:
                x1 = connectorend[lineend][1]
                y1 = connectorend[lineend][2]
                x2 = connectorstart[linestart][1]-1
                y2 = connectorstart[linestart][2]
                x = [x1,x2]
                y = [y1,y2]                
                plt.plot(x,y,'red')
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.xlabel('word in anyon', fontsize=20)
        plt.ylabel('line in text', fontsize=20)
        plt.title('Anyon Plot for variant: ' + i.__str__(), fontsize=20)
        plt.gca().invert_yaxis()    
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        plt.savefig('variant_anyons_' + i.__str__().zfill(3) +'.png')        
        plt.close(fig)
    
    # Generate animated GIF

    fp_in = "variant_anyons_*.png"
    fp_out = "variant_anyons.gif"

    img, *imgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
#    img, *imgs = [Image.open(f) for f in sorted(glob.glob(fp_in), key=os.path.getmtime)]        
    img.save(fp=fp_out, format='GIF', append_images=imgs,
         save_all=True, duration=1000, loop=0)
    
if plot_networkx_connections_branchpoints == True:
    
    print('plotting_networkx_connections_branchpoints ...')
    
    # Construct edgelist, labellist
    
    edgelist = [(i,i+1) for i in range(nwords-1)]
    labellist = [{i : wordlist[i]} for i in range(nwords)]

    for j in range(np.size(branchpointarray, axis=0)): # i.e. nbranchpoints        
        
    # Plot wordfreq colour-coded networkx graph of connectivity
     
        fig, ax = plt.subplots(figsize=(15,10))    
        G = nx.DiGraph()
        G.add_edges_from(edgelist)
        for node in G.nodes():
            G.nodes[node]['label'] = labellist[node]

        branchpointedges = []
        for i in range(np.size(branchpointarray, axis=1)): # i.e. maxfreq
            branchpointindices = branchpointarray[j,:]
            connections = branchpointindices[(branchpointindices != branchpointindices[i]) & (branchpointindices > 0)]
            for k in range(len(connections)):
                if branchpointindices[i] > 0:
                    branchpointedges.append([branchpointindices[i], connections[k]])
        G.add_edges_from(branchpointedges)

        # Colormap per branchpoint
    
        colormap = []
        for k in range(nwords):
            colormap.append('lightgrey')              
        for i in range(np.size(branchpointarray, axis=1)): # i.e. maxfreq
            branchpointindices = branchpointarray[j,:]
            connections = branchpointindices[(branchpointindices != branchpointindices[i]) & (branchpointindices > 0)]
            if branchpointindices[i] > 0:
                colormap[branchpointarray[j,i]] = hexcolors[j] 
        
        plt.title('Branchpoint connectivity for the word: ' + '"' + branchpointlist[j] + '"', fontsize=20)
        nx.draw_circular(G, node_color=colormap, node_size=300, linewidths=0.5, font_size=12, font_weight='normal', with_labels=True)
        plt.savefig('networkx_branchpoint_' + j.__str__().zfill(3) +'.png')
        plt.close(fig)

    # Generate animated GIF

    fp_in = "networkx_branchpoint_*.png"
    fp_out = "networkx_branchpoints.gif"

    img, *imgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
    img.save(fp=fp_out, format='GIF', append_images=imgs,
         save_all=True, duration=1000, loop=0)
    
    
if plot_networkx_connections_dags == True:

    print('plotting_networkx_connections_dags ...')

    # Construct edgelist, labellist
    
    edgelist = [(i,i+1) for i in range(nwords-1)]
    labellist = [{i : wordlist[i]} for i in range(nwords)]

    for j in range(np.size(branchpointarray, axis=0)): # i.e. nbranchpoints        
        
        fig, ax = plt.subplots(figsize=(15,10))    
        G = nx.DiGraph()
        G.add_edges_from(edgelist)
        for node in G.nodes():
            G.nodes[node]['label'] = labellist[node]

        branchpointedges = []
        for i in range(np.size(branchpointarray, axis=1)): # i.e. maxfreq
            branchpointindices = branchpointarray[j,:]
            connections = branchpointindices[(branchpointindices != branchpointindices[i]) & (branchpointindices > 0)]
            for k in range(len(connections)):
                if branchpointindices[i] > 0:
                    branchpointedges.append([branchpointindices[i], connections[k]])
        G.add_edges_from(branchpointedges)

        # Colormap per branchpoint
    
        colormap = []
        for k in range(nwords):
            colormap.append('lightgrey')              
        for i in range(np.size(branchpointarray, axis=1)): # i.e. maxfreq
            branchpointindices = branchpointarray[j,:]
            connections = branchpointindices[(branchpointindices != branchpointindices[i]) & (branchpointindices > 0)]
            if branchpointindices[i] > 0:
                colormap[branchpointarray[j,i]] = hexcolors[j] 
        
        plt.title('Directed acyclic graph for the word: ' + '"' + branchpointlist[j] + '"', fontsize=20)
        pos = nx.spring_layout(G,iterations=200)       
        nx.draw_networkx(G, pos=pos, node_color=colormap, node_size=300, linewidths=0.5, font_size=12, font_weight='normal', with_labels=True)
        plt.savefig('networkx_dag_' + j.__str__().zfill(3) +'.png')        
        plt.close(fig)

    # Generate animated GIF

    fp_in = "networkx_dag_*.png"
    fp_out = "networkx_dags.gif"

    img, *imgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
    img.save(fp=fp_out, format='GIF', append_images=imgs,
         save_all=True, duration=1000, loop=0)
            
# -----------------------------------------------------------------------------
if write_log:
            
    print('writing_log ...')

    text_file = open("log.txt", "w")
    text_file.write('TEXT STRING: %s' % textstr)
    text_file.write('\n\n')
    text_file.write('SENTENCES: %s' % sentencelist)
    text_file.write('\n\n')
    text_file.write('LINES: %s' % linelist)
    text_file.write('\n\n')
    text_file.write('WORDLIST: %s' % wordlist)
    text_file.write('\n\n')
    text_file.write('UNIQUE WORDS: %s' % uniquewordlist)
    text_file.write('\n\n')
    text_file.write('BRANCHPOINTS (>1 connection): %s' % branchpointlist)
    text_file.write('\n\n')
    text_file.write('N(sentences)=%s' % nsentences)
    text_file.write('\n')
    text_file.write('N(lines)=%s' % nlines)
    text_file.write('\n')
    text_file.write('N(words)=%s' % nwords)
    text_file.write('\n')
    text_file.write('N(unique)=%s' % nunique)
    text_file.write('\n')
    text_file.write('N(branchpoints)=%s' % nbranchpoints)    
    text_file.write('\n')
    text_file.write('N(variants)=%s' % nvariants)    
    text_file.close()
#--------------------------------------------------------------------------

dropdown_variants = [{'label' : i, 'value' : i} for i in np.arange(nvariants)]

# ========================================================================
# Start the App
# ========================================================================

server = Flask(__name__)
server.secret_key = os.environ.get('secret_key', str(randint(0, 1000000)))
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)
app.config.suppress_callback_exceptions = True


app.layout = html.Div(children=[

    html.H1(children='Transdisciplinary Quantum Poetry',
        style={'padding' : '10px', 'width': '100%', 'display': 'inline-block'},
    ),

    html.P([

#        html.Label( html.Em(html.Strong("World Lines: A Quantum Supercomputer Poem")) ),         
        html.H5([ html.A(html.Em(html.Strong('World Lines: A Quantum Supercomputer Poem (2018)')), href='https://www.amycatanzano.com/world-lines')]),
#        html.Br(),    
        html.Label("A poem by Amy Catanzano based on a theoretical model of a topological quantum computer"),         
        html.Br(),
        html.Label(["Formats: print publication (complete), computational and web-based interactive (underway), 3D art installation (anticipated)"]),
        html.Br(),
        html.Label(["Collaborator for Phase 2: Dr. Michael Taylor, applied mathematician and senior research associate in climate science at the University of East Anglia (Norwich, United Kingdom)"]),
        html.Br(),       
        html.Label(["Description: ", html.Em("World Lines: A Quantum Supercomputer Poem"), " is a poem and poetic form invented by Amy Catanzano that is based on a theoretical model of a topological quantum computer. Phase 1 of the project is complete and was presented by the Simons Center for Geometry and Physics at Stony Brook University. Additional poems by Catanzano in this poetic form being developed."]),
        html.Br(),                   
        html.Label(["In Phase 2 of the project, currently underway, Michael Taylor is using the Python computer programming language and machine learning (artificial intelligence) to develop an algorithm and quantum script that computationally expresses all possible versions of ", html.Em("World Lines"), ". After parsing each sentence in the poem and identifying branch points, words that are in common, Dr. Taylor is training a linguistic processor to choose world lines that are semantically logical to track how different topological paths move through a text map into different versions of the poem. A web interface will be generated where, after a text is loaded, a ", html.Em("World Lines"), " algorithm can find the branch points and do one of two things: 1) allow the reader to manually navigate along a world line, creating a new poem as a re-structured sample of the text that could be stored and studied, and 2) run a simulation and generate world lines that the reader can choose between in order to render new poems. Visual poetry and artwork are also being generated from the data."]),
        html.Br(),                   
        html.Label("Phase 3 of the poem will involve creating a 3D art installation based on the poem."),
        html.Br(),                         
        html.Label(["Anticipated outcomes for Phases 2-3: computational poetry, visual poetry and artwork, evolution of quantum script writing, interactive web interface, investigation of quantum linguistics and information theory in relation to principles in poetics, educational tool for both poetry and physics, 3D art installation."]),
    ],
    style={'padding' : '10px', 'width': '100%', 'display': 'inline-block'},
    ),

# ------------
    html.Div([            

        html.P([html.H3(children=html.Em('World Lines')),
#        html.P([
        
            html.Label(html.Strong("A Quantum Supercomputer Poem (2018)") ),         
#            html.Label([ html.A('World Lines: A Quantum Supercomputer Poem (2018)', href='https://www.amycatanzano.com/world-lines')]),
#            html.Br(),                  
#            html.Label("by Amy Catanzano"),
#            html.Label("(one version of many possible)"),
            html.Label("by Amy Catanzano (one version of many possible)"),
            html.Br(),                  
            html.Blockquote([
            html.Label("When we think as far as our world lines, our thoughts become movements"),
            html.Label("in space, motions, time, threads curved as thoughts recording the mind writing relative,"),
            html.Br(),            
            html.Label("tangled motions, knotting intricate paths like strands of DNA intertwined."),
            html.Label("The mind of a knot is a continuous curve through space, writing woven"),
            html.Br(),            
            html.Label("locations of particles traveling as their orbits in spacetime knot particles"),
            html.Label("of indefinite location. The world mind is a record that orbits its knotted history."),
            html.Br(),            
            html.Label("The poem, an indefinite knot threaded in a continuous curve of mind's space,"),
            html.Label("computes qubits, its world lines the braided motions of mind's memory."),
            ]),
        ],
        style = {'padding' : '10px', 'display': 'inline-block'}),

        html.P([html.H3(children='Topological Quantum Variant'),
#        html.P([
       
            html.Label(["Reactive app coded in ", html.A("Plotly Dash Python", href="https://plotly.com/dash/"), " by ", html.A("Michael Taylor", href="https://patternizer.github.io")]),                                                
        ],
        style = {'padding' : '10px', 'display': 'inline-block'}),
                
        dcc.Graph(id='poem-graphic', style = {'width': '100%'}),

        # Hidden variable to cache poem
        html.Div(id='cache-poem', style={'display': 'none'}),

    ],
    style={'columnCount': 2}),
# ------------
              
# ------------
    html.Div([      
                                          
        html.P([html.H3(children='Quantum Poetry Machine'),
            html.Label(["Select a topological quantum variant of ", html.Em(html.Strong("World Lines: A Quantum Supercomputer Poem"))]),
        ],               
        style = {'padding' : '10px', 'display': 'inline-block'}),
        
#        html.P([
#            html.Br(),    
#        ],
#        style={'padding' : '10px', 'width': '100%', 'display': 'inline-block'}),        
        
        dcc.Dropdown(
            id = 'input-variant',
            options = dropdown_variants,   
            value = 0,
            style = {'padding' : '10px', 'width': '100px', 'fontSize' : '15px', 'display': 'inline-block'}
        ),    
        
        dcc.Graph(id='poem-variant', style = {'width': '100%'}),
    ],    
    style={'columnCount': 1}), 

# ------------


# ------------
    html.Div([      
                                          
        html.P([html.H3(children='Technical Description'),
            html.Br(),                
            html.Label(["An algorithm and quantum script has been written in the Python computer programming language to compute all possible versions of ", html.Em(html.Strong("World Lines")),". The first step of the algorithm parses each line of the text and identifies branch points, words that occur on another line, and stores their location indices. In the second step, these indices are used to compute the directed acylic graph (DAG) through the text, associated with each unique branch point. The set of DAGs forms a topological map that forms the basis for the quantum script in step three of the algorithm. The quantum nature of this step is implicit in the entanglement of all variants of the text in the topological map. Step three of the algorithm proceeds by disentanglement of unique variants of the text. This is achieved by extracting anyons, reconstructed lines of the text formed from prior and posterior segments of a path through a DAG passing through a branchpoint."]),
            html.Br(),            
            html.Label(["So for example, the word 'continuous' in line 4 of ", html.Em(html.Strong("World Lines")), " is a branchpoint as it occurs again on line 7. Two anyons associated with this connectivity in the DAG for 'continuous' then lead to a 'braiding' of lines 4 and 7 such that the prior segment of line 4 up to and including 'continuous' continues with the posterior segment of line 7 afer the recurrence of 'continuous'. Its entangled partner comprises the prior segment of line 7 up to and including 'continuous' and continues with the posterior segment of line 4 following 'continuous'. Each variant of the poem is extracted by retaining the original line order in prior segments and then braiding once per branchpoint. For the 8 lines of ", html.Em(html.Strong("World Lines")),", the quantum script disentangles 94 variants from the poem's topological map."]),
            html.Br(),            
            html.Label(["This leads to four interesting potential applications. The first is the development of a linguistic processor trained to select variants that are semantically logical. As such, meaningful text is self-generated from a text allowing exploration of the nature of imagination itself. The second is the calculation of a statistical measure of the complexity of a text by joining its ends and using the branch point topology to cast it in the form of a G(n,p) Erdős–Rényi model. An optimisation algorithm has been written to deduce the value of the degree of randomness parameter, p for ", html.Em(html.Strong("World Lines")),". The third is the calculation of information entropy associated with each variant. Due to anyon braiding, each line of the text has a distinct and computable probability of ending on a different line. This enables the information entropy for each variant to be calculated. This may open a path for studying the relationship of imagined variations of a text and information theory. The fourth is as a quantum linguistic laboratory. Qubits are quantum bits formed from pairs of anyons. Start-of-line qubits are effectively entangled, in the quantum sense, with end-of-line qubits. The topological map encodes all text variants and therefore all entangled states in the one to many mapping of the original poem to its variants."]),
            html.Br(),            
            html.Label(["The algorithm and quantum script, by retaining linguistic continuity, creates a space and time for exploration of quantum entanglement and the visual imagination. Imagine a reader tracing a path through the text and interactively switching between variants dynamically by choosing the next braiding operation. The text is then reactive and many world."]),
        ],               
        style = {'padding' : '10px', 'display': 'inline-block'}),                
    ],    
    style={'columnCount': 1}), 
                
# ------------


# ------------
    html.Div([            

        html.P([html.H3(children='Branchpoint Analysis')], style = {'padding' : '10px', 'display': 'inline-block'}),
        dcc.Graph(id='poem-branchpoints', style = {'width': '100%'}),

        html.P([html.H3(children='Network Analysis')], style = {'padding' : '10px', 'display': 'inline-block'}),
        dcc.Graph(id='poem-networkx', style = {'width': '100%'}),

    ],
    style={'columnCount': 2}),
# ------------

# ------------
    html.Div([            

        html.P([html.H3(children='Anyons: Directed Acyclic Graphs')], style = {'padding' : '10px', 'display': 'inline-block'}),
        dcc.Graph(id='poem-anyon-dags', style = {'width': '100%'}),

        html.P([html.H3(children='Anyons: Branchpoint Connectivity')], style = {'padding' : '10px', 'display': 'inline-block'}),
        dcc.Graph(id='poem-anyon-branchpoints', style = {'width': '100%'}),

    ],
    style={'columnCount': 2}),
# ------------
                       
    ],
    style={'columnCount': 1})

# ----------------------------------------------------------------------------
# App callbacks
# ----------------------------------------------------------------------------

@app.callback(
    Output('cache-poem', 'children'), 
    [Input(component_id='input-variant', component_property='value')],
)
def update_poem(value):
    poem = allpoems[value]
    return json.dumps(poem)
              
              
#@app.callback(
#    Output(component_id='container-button', component_property='children'),
#    [Input(component_id='button', component_property='n_clicks')], 
#)
#def update_forecast_button(n_clicks, nvariants):    
#    if n_clicks == 1:
#        value = randrange(nvariants)
#        return    
#    else:    
#        n_clicks = 0
#        return


@app.callback(
    Output(component_id='poem-graphic', component_property='figure'),
    [Input(component_id='input-variant', component_property='value')]
    )
def update_title_image(value):
    fig = go.Figure()
#    img_width = 1000
#    img_height = 584
    img_width = 1500
    img_height = 1000
    scale_factor = 0.4
    fig.add_trace( 
        go.Scatter(
            x=[0, img_width * scale_factor],
            y=[0, img_height * scale_factor],
            mode="markers",
            marker_opacity=0
        )
    )
    fig.update_xaxes( visible=False, range=[0, img_width * scale_factor])
    fig.update_yaxes( visible=False, range=[0, img_height * scale_factor], scaleanchor="x")
    fig.add_layout_image(
        dict(
            x=0,
            sizex=img_width * scale_factor,
            y=img_height * scale_factor,
            sizey=img_height * scale_factor,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            sizing="stretch",
            source="https://raw.githubusercontent.com/patternizer/quantum_poetry/master/anyon_variants/variant_anyons_" + (value).__str__().zfill(3) + ".png"
        )
    )
    fig.update_layout(
        width=img_width * scale_factor,
        height=img_height * scale_factor,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return fig


@app.callback(
    Output(component_id='poem-branchpoints', component_property='figure'),
    [Input(component_id='input-variant', component_property='value')]
    )
def update_poem_branchpoints(value):
#    textstr, sentencelist, linelist, wordlist, uniquewordlist, wordfreq, branchpointlist, branchpointarray = parse_poem(input_file)
#    nvariants, allpoemsidx, allpoems, allidx = compute_variants(linelist, anyonarray)
#    branchpoint_colormap, hexcolors = generate_branchpoint_colormap(wordfreq, nbranchpoints, nwords, branchpointarray)
    data = []
    for k in range(len(branchpointlist)):  
        a = branchpointarray[k,:]
        vals = a[a>0]
        trace = [
            go.Scatter(
                x = np.arange(0,len(wordlist)), 
                y = np.ones(len(wordlist))*k, 
                mode="lines",
                showlegend=False,
                marker=dict(size=12, line=dict(width=0.5), color="black"),
                name="Trace k",
                hoverinfo='none',
            ),
            go.Scatter(
                x = vals,
                y = np.ones(len(vals))*k, 
                mode = "markers",
                showlegend = True,
                marker = dict(size=10, line=dict(width=0.5), color=hexcolors[k]),
                name = branchpointlist[k],
            ),                
        ]
        data = data + trace
    layout = go.Layout( 
        xaxis=dict(title='word n in text'),
        yaxis=dict(title='branchpoint k in text (>1 connection)'),
        margin=dict(r=60, l=60, b=60, t=60),                  
    ) 
    return {'data': data, 'layout':layout} 


@app.callback(
    Output(component_id='poem-networkx', component_property='figure'),
    [Input(component_id='input-variant', component_property='value')]
    )
def update_poem_networkx(value):
    # nx.draw_circular(G, node_color=branchpoint_colormap, node_size=300, linewidths=0.5, font_size=12, font_weight='normal', with_labels=True)    
    fig = go.Figure()
    img_width = 1500
    img_height = 1000
    scale_factor = 0.45
    fig.add_trace( 
        go.Scatter(
            x=[0, img_width * scale_factor],
            y=[0, img_height * scale_factor],
            mode="markers",
            marker_opacity=0
        )
    )
    fig.update_xaxes( visible=False, range=[0, img_width * scale_factor])
    fig.update_yaxes( visible=False, range=[0, img_height * scale_factor], scaleanchor="x")
    fig.add_layout_image(
        dict(
            x=0,
            sizex=img_width * scale_factor,
            y=img_height * scale_factor,
            sizey=img_height * scale_factor,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            sizing="stretch",
            source="https://raw.githubusercontent.com/patternizer/quantum_poetry/master/networkx_non_circular.png"
        )
    )
    fig.update_layout(
        width=img_width * scale_factor,
        height=img_height * scale_factor,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return fig


@app.callback(
    Output(component_id='poem-anyon-dags', component_property='figure'),
    [Input(component_id='input-variant', component_property='value')]
    )
def update_poem_anyon_dags(value):
    fig = go.Figure()
    img_width = 1500
    img_height = 1000
    scale_factor = 0.45
    fig.add_trace( 
        go.Scatter(
            x=[0, img_width * scale_factor],
            y=[0, img_height * scale_factor],
            mode="markers",
            marker_opacity=0
        )
    )
    fig.update_xaxes( visible=False, range=[0, img_width * scale_factor])
    fig.update_yaxes( visible=False, range=[0, img_height * scale_factor], scaleanchor="x")
    fig.add_layout_image(
        dict(
            x=0,
            sizex=img_width * scale_factor,
            y=img_height * scale_factor,
            sizey=img_height * scale_factor,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            sizing="stretch",
            source="https://raw.githubusercontent.com/patternizer/quantum_poetry/master/networkx_dags.gif"
        )
    )
    fig.update_layout(
        width=img_width * scale_factor,
        height=img_height * scale_factor,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return fig


@app.callback(
    Output(component_id='poem-anyon-branchpoints', component_property='figure'),
    [Input(component_id='input-variant', component_property='value')]
    )
def update_poem_anyon_branchpoints(value):
    fig = go.Figure()
    img_width = 1500
    img_height = 1000
    scale_factor = 0.45
    fig.add_trace( 
        go.Scatter(
            x=[0, img_width * scale_factor],
            y=[0, img_height * scale_factor],
            mode="markers",
            marker_opacity=0
        )
    )
    fig.update_xaxes( visible=False, range=[0, img_width * scale_factor])
    fig.update_yaxes( visible=False, range=[0, img_height * scale_factor], scaleanchor="x")
    fig.add_layout_image(
        dict(
            x=0,
            sizex=img_width * scale_factor,
            y=img_height * scale_factor,
            sizey=img_height * scale_factor,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            sizing="stretch",
            source="https://raw.githubusercontent.com/patternizer/quantum_poetry/master/networkx_branchpoints.gif"
        )
    )
    fig.update_layout(
        width=img_width * scale_factor,
        height=img_height * scale_factor,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return fig


@app.callback(
    Output(component_id='poem-variants', component_property='figure'),
    [Input(component_id='input-variant', component_property='value')]
    )
def update_poem_variants(value):
    fig = go.Figure()
    img_width = 1500
    img_height = 1000
    scale_factor = 0.45
    fig.add_trace( 
        go.Scatter(
            x=[0, img_width * scale_factor],
            y=[0, img_height * scale_factor],
            mode="markers",
            marker_opacity=0
        )
    )
    fig.update_xaxes( visible=False, range=[0, img_width * scale_factor])
    fig.update_yaxes( visible=False, range=[0, img_height * scale_factor], scaleanchor="x")
    fig.add_layout_image(
        dict(
            x=0,
            sizex=img_width * scale_factor,
            y=img_height * scale_factor,
            sizey=img_height * scale_factor,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            sizing="stretch",
            source="https://raw.githubusercontent.com/patternizer/quantum_poetry/master/anyon_variants/variant_anyons_007.png"
        )
    )
    fig.update_layout(
        width=img_width * scale_factor,
        height=img_height * scale_factor,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )
    return fig


@app.callback(
    Output(component_id='poem-variant', component_property='figure'),
    [Input(component_id='cache-poem', component_property='children')],
    )
def update_parameters(poem):
    linelist = json.loads(poem)    
    ncol = 0
    for i in range(len(linelist)):
        n = len(linelist[i])
        if n > ncol:
            ncol = n
    columnheaders = ['Word<Br>' + (i+1).__str__() for i in range(ncol)]    
    rowheaders = ['Line ' + (i+1).__str__() for i in range(len(linelist))]
    values = []
    for j in range(ncol):
        colj = []
        for i in range(len(linelist)):   
            if j > (len(linelist[i])-1):
                colj.append(' ')                
            else:
                colj.append(linelist[i][j])
        values.append(colj)        
    data = [
        go.Table(
            header=dict(values=columnheaders,                        
                line_color='darkslategray',
                fill_color='lightgrey',
                font_size=9,
                align='left'),
            cells=dict(values=values, 
                line_color='white',
                fill_color='white',
                font_size=9,
                align='left')
        ),
    ]
    layout = go.Layout(  height=300, width=1300, margin=dict(r=10, l=10, b=0, t=10))
    return {'data': data, 'layout':layout} 


##################################################################################################
# Run the dash app
##################################################################################################

# html.Ul([html.Li(x) for x in my_list])

if __name__ == "__main__":
    app.run_server(debug=True)

print('Python code end')


