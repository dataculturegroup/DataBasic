import math, networkx as nx, timeit, unittest

class ConnectTheDotsBigDataTest(unittest.TestCase):
    """
    Benchmarking suite for ConnectTheDots (large datasets)
    """

    def test_bc_runtime(self):
        """
        Test time needed to calculate betweenness centrality
        """

        TEST_CASES = [] # add (V, E) tuples

        NUM_TRIALS = 10

        def generate_graph(V, E):
            """
            Return a random Barabasi-Albert graph with V nodes and E edges
            """
            m = (V - math.sqrt(V ** 2 - 4 * E)) / 2
            return nx.barabasi_albert_graph(V, int(m))

        def calculate_bc(G):
            """
            Calculate betweenness centrality for graph G
            """
            return nx.betweenness_centrality(G)

        if len(TEST_CASES) > 0:
            print '\n\n[ Runtime ]\n'

        for (V, E) in TEST_CASES:
            print 'V = ' + str(V) + ', E = ' + str(E) + '\n'
            G = generate_graph(V, E)
            for i in xrange(NUM_TRIALS):
                start = timeit.default_timer()
                calculate_bc(G)
                stop = timeit.default_timer()
                print stop - start
            print ''
        
    def test_bc_estimation(self):
        """
        Test accuracy of different k-values for betweenness centrality estimation
        """

        TEST_CASES = [] # add (V, E, k) tuples

        NUM_TRIALS = 1

        def generate_graph(V, E):
            """
            Return a random Barabasi-Albert graph with V nodes and E edges
            """
            m = (V - math.sqrt(V ** 2 - 4 * E)) / 2
            return nx.barabasi_albert_graph(V, int(m))

        def calculate_bc(G, k=None):
            """
            Calculate betweenness centrality for graph G using k pivots
            """
            return nx.betweenness_centrality(G, k)

        def round_float(n):
            """
            Return string representation of float n rounded to six decimal places
            """
            return '{:f}'.format(n)

        def error_pct(error, actual):
            """
            Return string representation of error % of estimate from actual
            """
            if actual > 0:
                return '{:.1%}'.format(error / actual)
            else:
                return '--'

        if len(TEST_CASES) > 0:
            print '\n\n[ Estimation ]\n'

        for (V, E, k) in TEST_CASES:
            print 'V = ' + str(V) + ', E = ' + str(E) + ', k = ' + str(k) + '\n'
            G = generate_graph(V, E)
            bc = calculate_bc(G)

            for i in xrange(NUM_TRIALS):
                # estimate = calculate_bc(G, key)
                # print 'node   estimate   actual     error      % error'
                # print '----   --------   --------   --------   --------'
                # for key, val in estimate.iteritems():
                #     error = abs(bc[key] - val)
                #     print '   '.join(['{:04}'.format(key), round_float(val), round_float(bc[key]), round_float(error), error_pct(error, bc[key])])
                # print ''

                start = timeit.default_timer()
                estimate = calculate_bc(G, k)
                stop = timeit.default_timer()
                runtime = stop - start
                max_error = 0
                max_error_pct = 0
                for key, val in estimate.iteritems():
                    error = abs(bc[key] - val)
                    max_error = max(max_error, error)
                    if bc[key] > 0:
                        max_error_pct = max(max_error_pct, error / bc[key])
                print ', ' .join([round_float(max_error), '{:.1%}'.format(max_error_pct), str(runtime)])
            print ''
