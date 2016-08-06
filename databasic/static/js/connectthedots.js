(function() {
  var DISPLAY_RESOLUTION = 1.6,
      NODE_RADIUS = 6,
      NODE_STROKE = 1.5,
      EDGE_WIDTH = 1,
      TOOLTIP_LINE_HEIGHT = 1.1
      ROUNDING_PRECISION = 3;

  /**
   * Draw the network graph
   * Adapted from https://bl.ocks.org/mbostock/4062045
   */
  function drawGraph(graph) {
    var svg = d3.select('svg'),
        container = d3.select('.ctd-container');

    var padding = parseFloat(container.style('padding-left').slice(0, -2)),
        width = container.node().offsetWidth - 2 * padding,
        height = width / DISPLAY_RESOLUTION;

    svg.attr('width', width)
       .attr('height', height)
       .style('background-color', '#fff');

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
                                                               .on('mouseover', function(d) {
                                                                 if (!activeNode) showTooltip(d);
                                                               })
                                                               .on('mouseout', function(d) {
                                                                 if (!activeNode) tooltip.classed('in', false);
                                                               })
                                                               .on('click', setActiveNode)
                                                               .call(d3.drag().on('start', dragStart)
                                                                              .on('drag', dragUpdate)
                                                                              .on('end', dragEnd));

    var tooltip = d3.select('.tooltip');

    var activeNode;
    svg.on('click', function() {
      if (d3.event.target.tagName !== 'circle') clearActiveNode();
    });

    /**
     * Set the active node
     */
    function setActiveNode(node) {
      activeNode = node.id;
      showTooltip(node);
    }

    /**
     * Clear the active node
     */
    function clearActiveNode() {
      activeNode = null;
      tooltip.classed('in', false);
    }

    /**
     * Show the tooltip for a particular node
     */
    function showTooltip(node) {
      tooltip.datum(node)
             .select('.tooltip-inner').html(function(d) {
               return '<strong>' + d.id + '</strong><br>Degree: ' + d.degree +
               '<br>Centrality: ' + parseFloat(d.centrality.toFixed(ROUNDING_PRECISION));
             });

      tooltip.classed('fade', true)
             .classed('in', true)
             .style('left', function(d) {
               return d.x - tooltip.node().getBoundingClientRect().width / 2 + padding + 'px';
             })
             .style('top', function(d) {
               return d.y - tooltip.node().getBoundingClientRect().height + 'px';
             });
    }

    /**
     * Update positions of nodes/edges at each tick
     */
    function tickUpdate() {
      node.attr('cx', function(d) { return d.x; })
          .attr('cy', function(d) { return d.y; });

      edge.attr('x1', function(d) { return d.source.x; })
          .attr('y1', function(d) { return d.source.y; })
          .attr('x2', function(d) { return d.target.x; })
          .attr('y2', function(d) { return d.target.y; });

      tooltip.style('left', function(d) {
               return d ? d.x - tooltip.node().getBoundingClientRect().width / 2 + padding + 'px' : 0;
             })
             .style('top', function(d) {
               return d ? d.y - tooltip.node().getBoundingClientRect().height + 'px' : 0;
             });
    }

    /**
     * Handle node drag events
     */
    function dragStart(d) {
      if (!d3.event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;

      activeNode = d.id;
      showTooltip(d);
    }

    function dragUpdate(d) {
      d.fx = d3.event.x;
      d.fy = d3.event.y;
    }

    function dragEnd(d) {
      if (!d3.event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
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