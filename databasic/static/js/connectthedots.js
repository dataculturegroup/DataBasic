(function() {
  var NODE_RADIUS = 6,
      NODE_STROKE = 1.5,
      EDGE_WIDTH = 1,
      TOOLTIP_LINE_HEIGHT = 1.1
      ROUNDING_PRECISION = 3;

  /**
   * Draw the network graph
   */
  function drawGraph(graph) {
    var svg = d3.select('svg'),
        width = +svg.attr('width'),
        height = +svg.attr('height');

    var simulation = d3.forceSimulation()
                       .force('charge', d3.forceManyBody())
                       .force('link', d3.forceLink().id(function(d) { return d.id; }))
                       .force('center', d3.forceCenter(width / 2, height / 2));

    var edge = svg.append('g')
                  .classed('edges', true)
                  .selectAll('line').data(graph.links)
                                    .enter().append('line').attr('stroke-width', EDGE_WIDTH);

    var node = svg.append('g')
                  .classed('nodes', true)
                  .selectAll('circle').data(graph.nodes)
                                      .enter().append('circle').attr('r', NODE_RADIUS)
                                                               .attr('stroke-width', NODE_STROKE)
                                                               .attr('id', function(d) { return d.id; })
                                                               .on('mouseover', showTooltip);

    var tooltip = svg.append('g')
                     .classed('ctd-tooltip', true);

    var tt_fields = [];
    tt_fields.name = tooltip.append('text')
                            .style('font-weight', 700);
    tt_fields.degree = tooltip.append('text')
                              .attr('dy', TOOLTIP_LINE_HEIGHT + 'em');
    tt_fields.centrality = tooltip.append('text')
                                  .attr('dy', 2 * TOOLTIP_LINE_HEIGHT + 'em');

    /**
     * Show the tooltip for a particular node
     */
    function showTooltip(node) {
      tooltip.datum(node)
             .attr('transform', 'translate('+ (node.x + NODE_RADIUS) + ', ' + (node.y - NODE_RADIUS) + ')');

      tt_fields.name.text(node.id);
      tt_fields.degree.text('Degree: ' + node.degree);
      tt_fields.centrality.text('Centrality: ' + parseFloat(node.centrality.toFixed(ROUNDING_PRECISION)));
    }

    /**
     * Updates positions of nodes/edges at each tick
     */
    function tickUpdate() {
      node.attr('cx', function(d) { return d.x; })
          .attr('cy', function(d) { return d.y; });

      edge.attr('x1', function(d) { return d.source.x; })
          .attr('y1', function(d) { return d.source.y; })
          .attr('x2', function(d) { return d.target.x; })
          .attr('y2', function(d) { return d.target.y; });

      tooltip.attr('transform', function(d) {
        return d ? 'translate('+ (d.x + NODE_RADIUS) + ', ' + (d.y - NODE_RADIUS) + ')' : '';
      });
    }

    simulation.nodes(graph.nodes)
              .on('tick', tickUpdate)
              .force('link').links(graph.links);
  }

  // map link data (indices) to node ids
  data.links.forEach(function(e) {
    e.source = data.nodes[e.source].id;
    e.target = data.nodes[e.target].id;
  });

  drawGraph(data);
})();