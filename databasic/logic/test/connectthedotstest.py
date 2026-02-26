import codecs, json, networkx as nx, operator, os, unittest
import databasic.logic.connectthedots as ctd
import databasic.logic.filehandler as filehandler
import agate
from functools import reduce
import tempfile
import networkx as nx

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

        table = results['table']
        self.assertEqual(table[0]['id'], 'Valjean')

        nodes = list(graph.nodes())
        nodes.remove('Valjean')

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
                    paths_with_valjean = reduce(lambda n, path: n + 1 if 'Valjean' in path else n, paths, 0)
                    betweenness_centrality += paths_with_valjean / float(total_paths)

        node_pairs = len(nodes) * (len(nodes) - 1) / float(2)
        normalized_score = betweenness_centrality / node_pairs

        self.assertAlmostEqual(table[0]['centrality'], normalized_score)

    def test_centrality_scores_simple(self):
        """
        Test betweenness centrality for simple (independently verifiable) case

        A       D
          > C <      All shortest paths go through C, connector score = 1
        B       E
        """
        test_data_path = os.path.join(self._fixtures_dir, 'simple-network.csv')
        results = ctd.get_summary(test_data_path)
        table = results['table']

        self.assertEqual(table[0]['id'], 'C')
        self.assertEqual(table[0]['centrality'], 1)
        for i in range(1, 5):
            self.assertEqual(table[i]['centrality'], 0)

    def test_degree_scores(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')
        results = ctd.get_summary(test_data_path)
        table = sorted(results['table'], key=operator.itemgetter('degree'), reverse=True)

        self.assertEqual(table[0]['id'], 'Valjean')
        self.assertEqual(table[0]['degree'], 36) # counted manually

    def test_degree_scores_simple(self):
        """
        Test degree scores for simple (independently verifiable) case

        A       D
          > C <      All nodes have degree 1 except for C, which has degree 4
        B       E
        """
        test_data_path = os.path.join(self._fixtures_dir, 'simple-network.csv')
        results = ctd.get_summary(test_data_path)
        table = sorted(results['table'], key=operator.itemgetter('degree'), reverse=True)

        self.assertEqual(table[0]['id'], 'C')
        self.assertEqual(table[0]['degree'], 4)
        for i in range(1, 5):
            self.assertEqual(table[i]['degree'], 1)

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

        self.assertIsInstance(data['links'], list)

        # Compare edges as undirected pairs of node IDs
        edges = sorted({tuple(sorted((e['source'], e['target']))) for e in data['links']})

        self.assertEqual(len(edges), 4)
        self.assertEqual(edges, [('A', 'C'), ('B', 'C'), ('C', 'D'), ('C', 'E')])

    def test_as_gexf(self):
        test_data_path = os.path.join(self._fixtures_dir, 'les-miserables.csv')

        results = ctd.get_summary(test_data_path)
        original_graph = ctd.get_graph(test_data_path)

        # write GEXF to temp file so nx can read it back
        fd, path = tempfile.mkstemp(suffix='.gexf')
        try:
            with open(path, 'w') as f:
                f.write(results['gexf'])

            g = nx.read_gexf(path)

            # nodes/edges preserved
            self.assertEqual(set(original_graph.nodes()), set(g.nodes()))
            self.assertEqual(
                set(tuple(sorted(e)) for e in original_graph.edges()),
                set(tuple(sorted(e)) for e in g.edges())
            )

            # node attributes preserved (compare against results['table'])
            table_by_id = {row['id']: row for row in results['table']}

            for node_id in original_graph.nodes():
                # degree is deterministic
                self.assertEqual(int(g.nodes[node_id].get('degree')), int(table_by_id[node_id]['degree']))

                # betweenness centrality is float-ish; allow minor formatting diffs
                self.assertAlmostEqual(
                    float(g.nodes[node_id].get('betweenness centrality')),
                    float(table_by_id[node_id]['centrality']),
                    places=10
                )

                # community color is a string; if present, it should match exactly
                # (your code sets 'community' in gexf to the color name)
                self.assertEqual(
                    str(g.nodes[node_id].get('community')),
                    str(table_by_id[node_id]['community'])
                )
        finally:
            os.close(fd)
            try:
                os.remove(path)
            except Exception:
                pass

    def test_is_bipartite_candidate(self):
        test_data_path = os.path.join(self._fixtures_dir, 'southern-women.csv')
        results = ctd.get_summary(test_data_path)
        data = json.loads(results['json'])
        nodes = data['nodes']
        cols = {'BRENDA': 0, 'CHARLOTTE': 0, 'DOROTHY': 0, 'ELEANOR': 0, 'EVELYN': 0, 'FLORA': 0,
                'FRANCES': 0, 'HELEN': 0, 'KATHERINE': 0, 'LAURA': 0, 'MYRNA': 0, 'NORA': 0,
                'OLIVIA': 0, 'PEARL': 0, 'RUTH': 0, 'SYLVIA': 0, 'THERESA': 0, 'VERNE': 0,
                'E1': 1, 'E10': 1, 'E11': 1, 'E12': 1, 'E13': 1, 'E14': 1, 'E2': 1, 'E3': 1,
                'E4': 1, 'E5': 1, 'E6': 1, 'E7': 1, 'E8': 1, 'E9': 1}

        self.assertTrue(results['bipartite'])
        for n in nodes:
            self.assertEqual(n['column'], cols[n['id']])

    def test_is_not_bipartite_candidate(self):
        test_data_path = os.path.join(self._fixtures_dir, 'simple-network.csv')
        results = ctd.get_summary(test_data_path)
        data = json.loads(results['json'])
        nodes = data['nodes']
        
        self.assertFalse(results['bipartite'])
        for n in nodes:
            self.assertNotIn('column', n)

    def test_large_file(self):
        test_data_path = os.path.join(self._fixtures_dir, 'airline-routes.csv')
        results = ctd.get_summary(test_data_path)

        self.assertEqual(results['nodes'], 3425)
        self.assertEqual(results['edges'], 19257)

        table_path = os.path.join(self._fixtures_dir, 'airline-routes-centralities.csv')
        with codecs.open(table_path, 'r', encoding='utf-8') as table_file:
            bc_table = agate.Table.from_csv(table_file, header=True, sniff_limit=0)

        expected = {}
        for r in bc_table.rows:
            node_id = str(r[0]).strip()
            expected[node_id] = float(r[1])

        expected_top = [k for k, _ in sorted(expected.items(), key=lambda kv: kv[1], reverse=True)[:40]]
        actual_top = [str(r['id']).strip() for r in results['table'][:40]]

        overlap = len(set(expected_top) & set(actual_top))
        self.assertGreaterEqual(overlap, 30)

        # Small numeric sanity check (robust for approximated BC)
        top_node = str(results['table'][0]['id']).strip()
        self.assertIn(top_node, expected)
        self.assertAlmostEqual(
            float(results['table'][0]['centrality']),
            expected[top_node],
            places=1
        )