import sys
import time
import networkx as nx
from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.sql import functions
from graphframes import *
from copy import deepcopy

sc=SparkContext("local", "degree.py")
sqlContext = SQLContext(sc)

def articulations(g, usegraphframe=False):
	# Get the starting count of connected components
	# YOUR CODE HERE
	connected_comp = g.connectedComponents()
	count_connected_comp_1 = connected_comp.select("component").distinct().count()

	# Default version sparkifies the connected components process 
	# and serializes node iteration.
	list_articulation=[]
	if usegraphframe:
		# Get vertex list for serial iteration
		# YOUR CODE HERE
		vertices  = [item.id for item in g.vertices.collect()]

		# For each vertex, generate a new graphframe missing that vertex
		# and calculate connected component count. Then append count to
		# the output
		# YOUR CODE HERE
		for v in vertices:
			graph_vertices = g.vertices.filter("id !='"+v+"'")
			graph_edges = g.edges.filter("src !='"+v+"'").filter("dst!='"+v+"'")
			graph = GraphFrame(graph_vertices,graph_edges)
			graph_connected_component = graph.connectedComponents()
			count_connected_component_2 = graph_connected_component.select("component").distinct().count()
			if count_connected_component_2 > count_connected_comp_1:
				list_articulation.append((v,1))
			else:
				list_articulation.append((v,0))
				

		arti_points = sqlContext.createDataFrame(sc.parallelize(list_articulation), ['id','articulation'])
		return arti_points
	# Non-default version sparkifies node iteration and uses networkx 
	# for connected components count.
	else:
        # YOUR CODE HERE
		graph = nx.Graph()
        	graph.add_nodes_from(g.vertices.map(lambda x: x.id).collect())
        	graph.add_edges_from(g.edges.map(lambda x: (x.src, x.dst)).collect())
		vertices = [item.id for item in g.vertices.collect()]
	
		for v in vertices:
			t_g = deepcopy(graph)
			t_g.remove_node(v)
			t_cc_cnt = nx.number_connected_components(t_g)
			if t_cc_cnt>count_connected_comp_1:
				list_articulation.append((v,1))
			else:
				list_articulation.append((v,0))
		arti_points = sqlContext.createDataFrame(sc.parallelize(list_articulation), ['id','articulation'])
                return arti_points

filename = sys.argv[1]
lines = sc.textFile(filename)

pairs = lines.map(lambda s: s.split(","))
e = sqlContext.createDataFrame(pairs,['src','dst'])
e = e.unionAll(e.selectExpr('src as dst','dst as src')).distinct() # Ensure undirectedness 	

# Extract all endpoints from input file and make a single column frame.
v = e.selectExpr('src as id').unionAll(e.selectExpr('dst as id')).distinct()	

# Create graphframe from the vertices and edges.
g = GraphFrame(v,e)

#Runtime approximately 5 minutes
print("---------------------------")
print("Processing graph using Spark iteration over nodes and serial (networkx) connectedness calculations")
init = time.time()
df = articulations(g, False)
print("Execution time: %s seconds" % (time.time() - init))
print("Articulation points:")
df.filter('articulation = 1').show(truncate=False)
df.toPandas().to_csv("articulations_out.csv")
print("---------------------------")
'''
#Runtime for below is more than 2 hours
print("Processing graph using serial iteration over nodes and GraphFrame connectedness calculations")
init = time.time()
df = articulations(g, True)
print("Execution time: %s seconds" % (time.time() - init))
print("Articulation points:")
df.filter('articulation = 1').show(truncate=False)
'''
