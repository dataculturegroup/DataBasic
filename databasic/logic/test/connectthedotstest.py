import json, networkx as nx, operator, os, unittest
import databasic.logic.connectthedots as ctd
import databasic.logic.filehandler as filehandler

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

    def test_centrality_scores(self):
        """
        Test betweenness centrality with generalized formula

        For a node v and every other node pair (s, t), we take the proportion of shortest paths s => t that include
        v and then normalize the sum of all the proportions by dividing (N - 1)(N - 2) / 2, the number of node pairs
        """
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        graph = ctd.get_graph(test_data_path)

        self.assertEqual(len(results['centrality_scores']), 40)
        self.assertEqual(results['centrality_scores'][0][0], u'Valjean')

        nodes = graph.nodes()
        nodes.remove(u'Valjean')

        betweenness_centrality = 0
        visited_paths = []

        for u in nodes:
            for v in nodes:
                current_path = tuple(sorted((u, v)))
                if u == v or current_path in visited_paths:
                    continue
                else:
                    visited_paths.append(current_path)
                    paths = list(nx.all_shortest_paths(graph, u, v))
                    total_paths = len(paths)
                    paths_with_valjean = reduce(lambda n, path: n + 1 if u'Valjean' in path else n, paths, 0)
                    betweenness_centrality += paths_with_valjean / float(total_paths)

        node_pairs = len(nodes) * (len(nodes) - 1) / float(2)
        normalized_score = betweenness_centrality / node_pairs

        self.assertAlmostEqual(results['centrality_scores'][0][1], normalized_score)

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
        self.assertEqual(len(results['degree_scores']), 40)
        self.assertEqual(results['degree_scores'][0][0], u'Valjean')
        self.assertEqual(results['degree_scores'][0][1], 36) # counted manually

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

    def test_as_gexf(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_gexf(test_data_path)

        test_gexf_path = os.path.join(self._fixtures_dir, 'graph.gexf')
        with open(test_gexf_path, 'r') as gexf:
            contents = gexf.read()

        self.assertEqual(contents, results)