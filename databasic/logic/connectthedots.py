import codecs, community, json, logging, math, networkx as nx, operator, StringIO
import filehandler
from csvkit import table
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)

def get_summary(input_path, has_header_row=True):
    """
    Publicly access data summary
    """
    ctd = ConnectTheDots(input_path, has_header_row)
    return ctd.get_summary()

def get_graph(input_path, has_header_row=True):
    """
    Return the graph for testing purposes
    """
    ctd = ConnectTheDots(input_path, has_header_row)
    return ctd.as_graph()

class ConnectTheDots():
    def __init__(self, input_path, has_header_row=True):
        """
        Initialize the object
        """
        utf8_file_path = filehandler.convert_to_utf8(input_path)
        input_file = codecs.open(utf8_file_path, 'r', filehandler.ENCODING_UTF_8)
        try:
            self.table = table.Table.from_csv(input_file,
                                              no_header_row=not has_header_row,
                                              snifflimit=0)
            if (len(self.table) != 2):
                raise ValueError('File has more than two columns')
            else:
                self.graph = nx.from_edgelist(self.table.to_rows())
        except Exception as e:
            logger.error('[CTD] Unable to make table from csv: %s' % e)

    def get_summary(self):
        """
        Return a summary of the network data
        """
        results = {}

        if hasattr(self, 'graph'):
            node_count = self.count_nodes()
            if (node_count > 1000):
              k = int(math.log(node_count)) # TODO: determine best values for k/whether multiple trials are needed
              logger.debug('[CTD] Using k = %s to approximate betweenness centrality' % k)
            else:
              k = None

            nodes = nx.nodes_iter(self.graph)
            bc = nx.betweenness_centrality(self.graph, k=k)
            partition = community.best_partition(self.graph)
            results['bipartite'] = self.is_bipartite_candidate()
            results['communities'] = len(set(partition.values()))

            if results['bipartite']:
                self.nodes = [{'id': n, 'degree': self.graph.degree(n), 'centrality': bc[n], 'community': partition[n], 'column': 0 if n in self.col0 else 1} for n in nodes]
            else:
                self.nodes = [{'id': n, 'degree': self.graph.degree(n), 'centrality': bc[n], 'community': partition[n]} for n in nodes]

            results['nodes'] = node_count
            results['edges'] = self.count_edges()

            results['clustering'] = self.get_clustering_score()
            results['density'] = self.get_density_score()

            results['table'] = self.as_table()
            results['json'] = self.as_json()
            results['gexf'] = self.as_gexf()

        return results

    def count_nodes(self):
        """
        Count the number of (unique) nodes in the dataset
        """
        return nx.number_of_nodes(self.graph)

    def count_edges(self):
        """
        Count the number of edges in the dataset
        """
        return nx.number_of_edges(self.graph)

    def get_clustering_score(self):
        """
        Return the graph's global clustering/"clique-ishness" score
        """
        return nx.average_clustering(self.graph) # using default # of trials: 1000

    def get_density_score(self):
        """
        Return the graph's global density/"connectedness" score
        """
        return nx.density(self.graph)

    def as_graph(self):
        """
        Return the networkx graph object
        """
        return self.graph

    def as_table(self):
        """
        Return the table of degree/centrality scores
        """
        return sorted(self.nodes, key=operator.itemgetter('centrality'), reverse=True)

    def as_json(self):
        """
        Return the graph as JSON for D3 visualization
        """
        output = json_graph.node_link_data(self.graph)
        output['nodes'] = self.nodes
        return json.dumps(output)

    def as_gexf(self):
        """
        Return the graph as GEXF for download
        """
        sio = StringIO.StringIO()
        nx.write_gexf(self.graph, sio)
        return sio.getvalue()

    def is_bipartite_candidate(self):
        """
        Return true if network might be bipartite (unique values per column)
        """
        self.col0 = {}
        for val in list(set(self.table[0])):
            self.col0[val] = True
        for val in list(set(self.table[1])):
            if val in self.col0:
                return False
        return True