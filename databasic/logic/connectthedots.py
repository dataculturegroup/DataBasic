import codecs, json, logging, networkx as nx, operator, os
import filehandler
from csvkit import table
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)

def get_summary(input_path, has_header_row=True):
    """
    Publicly access data summary
    """
    ctd = ConnectTheDots(input_path, has_header_row)
    results = ctd.get_summary()
    return results

class ConnectTheDots():
    def __init__(self, input_path, has_header_row=True):
        """
        Initialize the object
        """
        utf8_file_path = filehandler.convert_to_utf8(input_path)
        input_file = codecs.open(utf8_file_path, 'r', filehandler.ENCODING_UTF_8)
        try:
            self.table = table.Table.from_csv(input_file, no_header_row=not has_header_row)
            self.graph = nx.from_edgelist(self.table.to_rows())
        except Exception as e:
            logger.debug('[CTD] Unable to make table from csv')

    def get_summary(self):
        """
        Return a summary of the network data
        """
        results = {}

        if hasattr(self, 'graph'):
            results['nodes'] = self.count_nodes()
            results['edges'] = self.count_edges()

            results['clustering'] = self.get_clustering_score()
            results['density'] = self.get_density_score()

            results['centrality_scores'] = self.get_centrality_scores()
            results['degree_scores'] = self.get_degree_scores()

            if os.environ['APP_MODE'] == 'development':
                results['graph'] = self.graph # testing purposes only
            
            results['json'] = self.as_json()

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

    def get_centrality_scores(self, n=40):
        """
        Return the n most central nodes in the graph as a list of tuples
        """
        centrality_scores = sorted(nx.betweenness_centrality(self.graph).items(), key=operator.itemgetter(1), reverse=True)
        return centrality_scores[0:n]

    def get_degree_scores(self, n=40):
        """
        Return the n most directly connected nodes in the graph as a list of tuples
        """
        degree_scores = sorted(self.graph.degree().items(), key=operator.itemgetter(1), reverse=True)
        return degree_scores[0:n]

    def as_json(self):
        """
        Return the graph as JSON for D3 visualization
        """
        output = json_graph.node_link_data(self.graph)
        bc = nx.betweenness_centrality(self.graph)
        for node in output['nodes']:
            node['centrality'] = bc[node['id']]
            node['degree'] = self.graph.degree(node['id'])
        return json.dumps(output)