# author: Soma S Dhavala
# date: 25th December, 2019
# Ref: https://docs.google.com/document/d/1vyeHU3ahDZ-4WOnmpu6f02QTfPh3ngbq8rZIJ2o3zUI/edit?usp=sharing

import networkx as nx
import numpy as np


# simulate a complete graph db, with 10 nodes
n = 10

# want to go from src to dst
src = 0
dst = 9


def SimulateData(n=10):
	db = nx.complete_graph(n)
	for e in list(db.edges):
		db.edges[e]['dist'] = np.random.randint(1,5)
	return db



class Route():
	def __init__(self, src, dst, dist):
		self.src = src
		self.dst = dst
		self.dist = dist
	
# this is to be implemented by service providers
def GetRoutes(missing_links):
	routes = []
	for link in missing_links:
		src = link[0]
		dst = link[1]
		dist = db[src][dst]['dist']+0.5
		tmp = Route(src,dst,dist)
		routes.append(tmp)
	# add few other responses as well
	# select random edges add them to the list
	k = 2
	nodes = list(np.random.choice(range(n), k*2, replace=False))
	for i in range(k):
		src = nodes[i]
		dst = nodes[i+2]
		dist = db[src][dst]['dist']+0.5
		tmp = Route(src,dst,dist)
		routes.append(tmp)

	return routes


def UpdateGraph(routes):
	for route in routes:
		src = route.src
		dst = route.dst
		dist = route.dist
		G[src][dst]['dist'] = dist

def FilterRankSelectPaths(paths, by='dist'):
	# implement a filter, rank, select criteria
	# TBD
	return paths
		
def FilterRankSelectMissingLinks(by='dist'):
	# implement a filter, rank, select criteria

	# dummy missing_link generation
	n = len(G)
	k = 2
	nodes = list(np.random.choice(range(n), k*2, replace=False))
	missing_links = []
	for i in range(k):
		src = nodes[i]
		dst = nodes[i+2]
		missing_links.append([src,dst])
	# add filtering creiteria
	# TBD
	return missing_links



max_dist = 100
stop = False
counter = 0
missing_links = [[src,dst]]

db = SimulateData(n)
# current state of the graph
G = db.to_directed()

while not stop:
	valid_routes = []
	routes = GetRoutes(missing_links)
	UpdateGraph(routes)
	paths = list(nx.all_simple_paths(G, src, dst, cutoff=max_dist))
	journeys = FilterRankSelectPaths(paths)
	missing_links = FilterRankSelectMissingLinks()
	print('missing links',missing_links[0])
	print('journeys',journeys[0])
	counter += 1
	if counter > 10:
		stop = True