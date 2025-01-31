from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.sql import functions
from graphframes import *
from pyspark.sql.functions import explode

sc=SparkContext("local", "degree.py")
sqlContext = SQLContext(sc)

def closeness(g):
	# Get list of vertices. We'll generate all the shortest paths at
	# once using this list.
	# YOUR CODE HERE
	lst_vertices = []
	for v in g.vertices.collect():
		lst_vertices.append(v['id'])
	
	# first get all the path lengths.
	path_length = g.shortestPaths(lst_vertices)
	# Break up the map and group by ID for summing
	new_gp = path_length.select(functions.explode('distances')).groupBy('key')
	# Sum by ID
	sumval = new_gp.agg(functions.sum('value').alias('sumval'))

	# Get the inverses and generate desired dataframe.
	ans = sumval.selectExpr("key as id", "1/sumval as closeness")

	return ans
print("Reading in graph for problem 2.")
graph = sc.parallelize([('A','B'),('A','C'),('A','D'),
	('B','A'),('B','C'),('B','D'),('B','E'),
	('C','A'),('C','B'),('C','D'),('C','F'),('C','H'),
	('D','A'),('D','B'),('D','C'),('D','E'),('D','F'),('D','G'),
	('E','B'),('E','D'),('E','F'),('E','G'),
	('F','C'),('F','D'),('F','E'),('F','G'),('F','H'),
	('G','D'),('G','E'),('G','F'),
	('H','C'),('H','F'),('H','I'),
	('I','H'),('I','J'),
	('J','I')])
	
e = sqlContext.createDataFrame(graph,['src','dst'])
v = e.selectExpr('src as id').unionAll(e.selectExpr('dst as id')).distinct()
print("Generating GraphFrame.")
g = GraphFrame(v,e)

print("Calculating closeness.")
ans = closeness(g).sort('closeness',ascending=False)
ans.show()
ans.toPandas().to_csv("centrality_out.csv")
