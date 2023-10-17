import sys
from clang.cindex import Index, CursorKind
from collections import defaultdict, Counter
import json
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import matplotlib.pyplot as plt
import numpy as np

def extract_symbols_from_file(filename):
    index = Index.create()
    tu = index.parse(filename)
    if not tu:
        print(f"Unable to parse input file {filename}")
        return set()

    symbols = set()

    def visit_node(node):
        if node.kind.is_reference() or node.kind == CursorKind.TYPEDEF_DECL:
            canonical = node.get_definition()
            if canonical:
                name = canonical.spelling
                symbols.add(name)
        for child in node.get_children():
            visit_node(child)

    visit_node(tu.cursor)
    return symbols

def compute_proximity(header_filename, c_filenames):
    with open(c_filenames) as json_data:
        header_symbols = extract_symbols_from_file(header_filename)
        proximity = defaultdict(int)
        data = json.load(json_data)
        for row in data:
            c_file = row["file"]
            c_file_symbols = extract_symbols_from_file(c_file)
            relevant_symbols = header_symbols.intersection(c_file_symbols)

            for sym1 in relevant_symbols:
                for sym2 in relevant_symbols:
                    if sym1 != sym2:
                        proximity[(sym1, sym2)] += 1

    return proximity

def create_distance_matrix(proximity, symbols):
    n = len(symbols)
    LARGE_VALUE = 1e6
    matrix = np.full((n, n), LARGE_VALUE)
    
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0
            else:
                pair = (symbols[i], symbols[j])
                if pair in proximity:
                    matrix[i][j] = 1 / proximity[pair]

    max_distance = matrix[matrix != LARGE_VALUE].max()
    matrix[matrix == LARGE_VALUE] = max_distance + 1

    return matrix


def hierarchical_clustering(proximity):
    symbols = list(extract_symbols_from_file(header_filename))
    distance_matrix = create_distance_matrix(proximity, symbols)
    linked = linkage(distance_matrix, method='average')
    
    plt.figure(figsize=(10, 7))
    dendrogram(linked, orientation='top', labels=symbols, distance_sort='descending')
    plt.show()

    clusters = fcluster(linked, 2, criterion='maxclust')
    symbol_to_cluster = {symbols[i]: cluster_id for i, cluster_id in enumerate(clusters)}

    return symbol_to_cluster

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <header_filename> <compile_commands.json>")
        sys.exit(1)

    header_filename = sys.argv[1]
    c_filenames = sys.argv[2]
    proximity = compute_proximity(header_filename, c_filenames)

    sorted_data = sorted([(count, sym1, sym2) for (sym1, sym2), count in proximity.items()], reverse=True)
    for count, sym1, sym2 in sorted_data:
        print(f"Proximity {sym1}-{sym2}: {count}")

    clusters = hierarchical_clustering(proximity)
    for symbol, cluster_id in clusters.items():
        print(f"Symbol {symbol} is in cluster {cluster_id}")
