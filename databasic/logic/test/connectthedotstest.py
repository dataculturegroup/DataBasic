import codecs, json, networkx as nx, operator, os, unittest
import databasic.logic.connectthedots as ctd
import databasic.logic.filehandler as filehandler
from csvkit import table

class ConnectTheDotsTest(unittest.TestCase):
    """
    Unit testing suite for ConnectTheDots
    """

    def setUp(self):
        self._fixtures_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fixtures')

    def test_count_nodes(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['nodes'], 77) # len(set(self.table[0] + self.table[1]))

    def test_count_edges(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['edges'], 254) # self.table.count_rows()

    def test_import_xls(self):
        test_data_path = os.path.join(self._fixtures_dir, 'zachary-karate-club.xlsx')
        csv_file = filehandler.convert_to_csv(test_data_path)[0]
        results = ctd.get_summary(csv_file)
        self.assertEqual(results['nodes'], 34)
        self.assertEqual(results['edges'], 78)

    def test_import_no_header(self):
        test_data_path = os.path.join(self._fixtures_dir, 'handshake-problem.csv')
        results = ctd.get_summary(test_data_path, False)
        self.assertEqual(results['nodes'], 5)
        self.assertEqual(results['edges'], 10)

    def test_invalid_import(self):
        test_data_path = os.path.join(self._fixtures_dir, 'invalid-graph.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results, {})

    def test_clustering_score(self):
        """
        Test global clustering score with generalized formula

        This is the average of the local clustering scores for each node v:

                  2 Nv        where Kv = degree
        C(v) = ----------           Nv = number of edges between
               Kv (Kv - 1)               the neighbors of v
        """
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        graph = ctd.get_graph(test_data_path)

        local_scores = []
        for v in graph.nodes():
            k = graph.degree(v)
            neighbor_links = []
            for u in nx.all_neighbors(graph, v):
                neighbor_links += [tuple(sorted((u, w))) for w in nx.common_neighbors(graph, u, v)]
            n = len(list(set(neighbor_links)))
            local_scores.append(2 * n / float(k * (k - 1))) if k > 1 else local_scores.append(0)

        self.assertAlmostEqual(results['clustering'], sum(local_scores) / float(len(local_scores)))

    def test_clustering_score_star(self):
        test_data_path = os.path.join(self._fixtures_dir, 'simple-network.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['clustering'], 0) # no clusters, neighbors are never connected

    def test_clustering_score_clique(self):
        test_data_path = os.path.join(self._fixtures_dir, 'handshake-problem.csv')
        results = ctd.get_summary(test_data_path, False)
        self.assertEqual(results['clustering'], 1) # complete graph, all nodes connected

    def test_density_score(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['density'], 0.08680792891319207) # float(2 * self.count_edges()) /
                                                                  # (count_nodes() * (self.count_nodes() - 1))

    def test_as_json_nodes(self):
        test_data_path = os.path.join(self._fixtures_dir, 'simple-network.csv')
        results = ctd.get_summary(test_data_path)
        data = json.loads(results['json'])
        nodes = sorted(data['nodes'], key=operator.itemgetter('id')) # [A, B, C, D, E]

        self.assertEqual(len(nodes), 5)
        for n in [0, 1, 3, 4]:
            self.assertEqual(nodes[n]['degree'], 1)
            self.assertEqual(nodes[n]['centrality'], 0)
        self.assertEqual(nodes[2]['degree'], 4)
        self.assertEqual(nodes[2]['centrality'], 1)

    def test_as_json_edges(self):
        test_data_path = os.path.join(self._fixtures_dir, 'simple-network.csv')
        results = ctd.get_summary(test_data_path)
        data = json.loads(results['json'])
        nodes = data['nodes']
        edges = sorted(data['links'], key=lambda e: (nodes[e['source']]['id'], nodes[e['target']]['id']))

        self.assertEqual(len(edges), 4)
        self.assertEqual(nodes[edges[0]['source']]['id'], 'A')
        self.assertEqual(nodes[edges[0]['target']]['id'], 'C')

        targets = ['B', 'D', 'E']
        for n in range(1, 4):
            self.assertEqual(nodes[edges[n]['source']]['id'], 'C')
            self.assertEqual(nodes[edges[n]['target']]['id'], targets[n - 1])

    def test_as_gexf(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)

        test_gexf_path = os.path.join(self._fixtures_dir, 'graph.gexf')
        with open(test_gexf_path, 'r') as gexf:
            contents = gexf.read()

        self.assertEqual(contents, results['gexf'])

    def test_large_file(self):
        test_data_path = os.path.join(self._fixtures_dir, 'airline-routes.csv')
        results = ctd.get_summary(test_data_path)

        self.assertEqual(results['nodes'], 3425)
        self.assertEqual(results['edges'], 19257)

        # TODO: test approximation against table of actual centrality scores
