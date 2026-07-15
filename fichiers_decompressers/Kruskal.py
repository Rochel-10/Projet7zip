edges = [
    (2, 'A', 'D'),
    (6, 'A', 'B'),
    (8, 'A', 'G'),
    (1, 'B', 'D'),
    (1, 'D', 'E'),
    (2, 'B', 'G'),
    (2, 'F', 'H'),
    (4, 'B', 'C'),
    (3, 'G', 'C'),
    (2, 'B', 'E'),
    (8, 'E', 'C'),
    (1, 'C', 'F'),
    (9, 'E', 'F'),
]

#listes des sommets
vertices = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

#structure union -find
parent = {}
rank = {}

def make_set(vertex):
    parent[vertex] = vertex
    rank[vertex] = 0

def find(vertex):
    if parent[vertex] != vertex:

