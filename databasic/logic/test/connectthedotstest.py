import json, logging, operator, os, unittest
import databasic.logic.connectthedots as ctd
import databasic.logic.filehandler as filehandler

logger = logging.getLogger(__name__)

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

    def test_clustering_score(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['clustering'], 0.5731367499320134) # not (easily) independently verifiable

    def test_clustering_score_star(self):
        test_data_path = os.path.join(self._fixtures_dir, 'simple-network.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['clustering'], 0)

    def test_clustering_score_clique(self):
        test_data_path = os.path.join(self._fixtures_dir, 'handshake-problem.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['clustering'], 1)

    def test_density_score(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['density'], 0.08680792891319207) # float(2 * self.count_edges()) /
                                                                  # count_nodes() * (self.count_nodes() - 1)

    def test_centrality_scores(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['centrality_scores'][0][0], u'Valjean')
        self.assertEqual(results['centrality_scores'][0][1], 0.5699890527836186) # not (easily) independently verifiable
        self.assertEqual(len(results['centrality_scores']), 40)

    def test_centrality_scores_simple(self):
        """
        Test betweenness centrality for simple (independently verifiable) case

        A       D
          > C <      All shortest paths go through C, connector score = 1
        B       E
        """
        test_data_path = os.path.join(self._fixtures_dir, 'simple-network.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['centrality_scores'][0][0], u'C')
        self.assertEqual(results['centrality_scores'][0][1], 1)
        for i in range(1, 5):
            self.assertEqual(results['centrality_scores'][i][1], 0)

    def test_degree_scores(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['degree_scores'][0][0], u'Valjean')
        self.assertEqual(results['degree_scores'][0][1], 36) # counted manually
        self.assertEqual(len(results['degree_scores']), 40)

    def test_degree_scores_simple(self):
        """
        Test degree scores for simple (independently verifiable) case

        A       D
          > C <      All nodes have degree 1 except for C, which has degree 4
        B       E
        """
        test_data_path = os.path.join(self._fixtures_dir, 'simple-network.csv')
        results = ctd.get_summary(test_data_path)
        self.assertEqual(results['degree_scores'][0][0], u'C')
        self.assertEqual(results['degree_scores'][0][1], 4)
        for i in range(1, 5):
            self.assertEqual(results['degree_scores'][i][1], 1)

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