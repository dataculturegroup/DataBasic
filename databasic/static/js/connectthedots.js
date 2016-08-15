(function() {
  var BACKGROUND_COLOR = '#fff',
      DISPLAY_RESOLUTION = 1.4,
      BOUNDARY_PROPORTION = .85,
      NODE_RADIUS = 6,
      NODE_STROKE = 1.5,
      EDGE_WIDTH = 1,
      ROUNDING_PRECISION = 3,
      STICKY_OFFSET_TOP = 280,
      STICKY_OFFSET_BOTTOM = 80;

  /**
   * Draw the network graph
   * Adapted from https://bl.ocks.org/mbostock/4062045
   */
  function drawGraph(graph) {
    // setup SVG dimensions
    var svg = d3.select('svg'),
        container = d3.select('.ctd-container');

    var padding = parseFloat(container.style('padding-left').slice(0, -2)),
        width = container.node().offsetWidth - 2 * padding,
        height = width / DISPLAY_RESOLUTION,
        scale = {factor: 1, dx: 0, dy: 0};

    svg.attr('width', width)
       .attr('height', height)
       .style('background-color', BACKGROUND_COLOR);

    // setup simulation
    var center = d3.forceCenter(width / 2, height / 2);

    var simulation = d3.forceSimulation()
                       .force('charge', d3.forceManyBody())
                       .force('link', d3.forceLink().id(function(d) { return d.id; }))
                       .force('center', center);

    var ticksElapsed = 0,
        stableAt = Math.ceil(
                     Math.log(simulation.alphaMin()) / Math.log(1 - simulation.alphaDecay())
                   ); // number of ticks before graph reaches equilibrium

    // setup graphical elements and bind data
    var edge = svg.append('g')
                  .classed('edges', true)
                  .attr('aria-hidden', 'true')
                  .selectAll('line').data(graph.links)
                                    .enter().append('line')
                                    .style('opacity', 0)
                                    .attr('stroke-width', EDGE_WIDTH);

    var node = svg.append('g')
                  .classed('nodes', true)
                  .attr('role', 'group')
                  .attr('aria-label', 'Network graph')
                  .selectAll('circle').data(graph.nodes)
                                      .enter().append('circle')
                                      .style('opacity', 0)
                                      .attr('r', NODE_RADIUS)
                                      .attr('stroke-width', NODE_STROKE)
                                      .attr('id', function(d) { return d.id; })
                                      .attr('role', 'img')
                                      .attr('aria-label', function(d) {
                                        return 'Node ' + d.id + ' has a degree of ' + d.degree + 
                                        ' and a centrality of ' + parseFloat(d.centrality.toFixed(ROUNDING_PRECISION));
                                      });

    var progress = d3.select('.ctd-progress'),
        tooltip = d3.select('.ctd-tooltip').style('display', 'none'),
        tableRow = d3.selectAll('.ctd-table > tbody > tr').attr('id', function() {
          return this.childNodes[1].textContent;
        });

    // start simulation
    simulation.nodes(graph.nodes)
              .on('tick', tickUpdate)
              .force('link').links(graph.links);

    // event handlers for dragging and setting active node
    var activeNode;
    node.on('mouseover', mouseoverNode)
        .on('mouseout', mouseoutNode)
        .on('click', setActiveNode)
        .call(d3.drag().on('start', dragStart)
                       .on('drag', dragUpdate)
                       .on('end', dragEnd));

    svg.on('click', function() { if (d3.event.target.tagName !== 'circle') clearActiveNode(); });
    tableRow.on('mouseover', function() { mouseoverNode(findAssociatedNode(this.id).data()[0]) })
            .on('mouseout', function() { mouseoutNode(findAssociatedNode(this.id).data()[0]) })
            .on('click', function() { setActiveNode(findAssociatedNode(this.id).data()[0]) });

    /**
     * Find associated node by id
     */
    function findAssociatedNode(id) {
      return node.filter(function(d) { return d.id === id });
    }

    /**
     * Highlight a node in the graph and table
     */
    function mouseoverNode(d) {
      if (!activeNode) showTooltip(d);

      node.filter(function(c) { return c.id === d.id; }).classed('hover', true);
      tableRow.filter(function() { return this.id === d.id; }).classed('hover', true);
    }

    /**
     * De-highlight a node in the graph and table
     */
    function mouseoutNode(d) {
      if (!activeNode) tooltip.classed('in', false);

      node.classed('hover', false);
      tableRow.classed('hover', false);
    }

    /**
     * Set the active node
     */
    function setActiveNode(d) {
      if (activeNode !== d.id) {
        activeNode = d.id;

        node.classed('active', false);
        tableRow.classed('active', false);

        node.filter(function(d) { return d.id === activeNode; }).classed('active', true);
        tableRow.filter(function() { return this.id === activeNode; }).classed('active', true);

        showTooltip(d);
      }
    }

    /**
     * Clear the active node
     */
    function clearActiveNode() {
      activeNode = null;
      node.classed('active', false);
      tableRow.classed('active', false);
      tooltip.classed('in', false);
    }

    /**
     * Handle node drag events
     */
    function dragStart(d) {
      if (!d3.event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
      setActiveNode(d);
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

    /**
     * Show the tooltip for a particular node
     */
    function showTooltip(d) {
      tooltip.datum(d)
             .select('.tooltip-inner').html(function(d) {
               return '<strong>' + d.id + '</strong><br>Degree: ' + d.degree +
               '<br>Centrality: ' + parseFloat(d.centrality.toFixed(ROUNDING_PRECISION));
             });

      tooltip.classed('fade', true)
             .classed('in', true);

      positionTooltip();
    }

    /**
     * Position the tooltip based on the currently bound node
     */
    function positionTooltip() {
      tooltip.style('left', function(d) {
               return d ? d.x * scale.factor + scale.dx - getTooltipSize().width / 2 + padding + 'px' : 0;
             })
             .style('top', function(d) {
               return d ? d.y * scale.factor + scale.dy - getTooltipSize().height + 'px' : 0;
             });
    }

    /**
     * Return the current dimensions of the tooltip
     */
    function getTooltipSize() {
      var bbox = tooltip.node().getBoundingClientRect();
      return {width: bbox.width, height: bbox.height};
    }

    /**
     * Update positions of nodes/edges at each tick
     */
    function tickUpdate() {
      ticksElapsed++;
      if (ticksElapsed < stableAt) {
        progress.style('width', width * ticksElapsed / stableAt + 'px');
      } else if (ticksElapsed === stableAt) {
        progress.remove();
        rescaleGraph();
        node.style('opacity', 1);
        edge.style('opacity', 1);
        tooltip.style('display', 'block');
      }

      node.attr('cx', function(d) {
            return d.x = Math.max(NODE_RADIUS, Math.min(width - NODE_RADIUS, d.x));
          })
          .attr('cy', function(d) {
            return d.y = Math.max(NODE_RADIUS, Math.min(height - NODE_RADIUS, d.y));
          });

      edge.attr('x1', function(d) { return d.source.x; })
          .attr('y1', function(d) { return d.source.y; })
          .attr('x2', function(d) { return d.target.x; })
          .attr('y2', function(d) { return d.target.y; });

      positionTooltip();
    }

    /**
     * Rescale the graph to fit some proportion of the SVG bounds
     */
    function rescaleGraph() {
      var bbox = svg.select('.nodes').node().getBBox();

      scale.factor = Math.min(width * BOUNDARY_PROPORTION / bbox.width,
                              height * BOUNDARY_PROPORTION / bbox.height);

      scale.dx = -width / 2 * (scale.factor - 1),
      scale.dy = -height / 2 * (scale.factor - 1);

      svg.selectAll('g')
         .attr('transform', 'translate(' + scale.dx + ', ' + scale.dy + ') scale(' + scale.factor + ')');
    }

    // rescale graph on window resize
    window.onresize = _.debounce(function() {
      padding = parseFloat(container.style('padding-left').slice(0, -2)),
      width = container.node().offsetWidth - 2 * padding,
      height = width / DISPLAY_RESOLUTION;

      svg.attr('width', width)
         .attr('height', height);
    
      rescaleGraph();

      center.x(width / 2)
            .y(height / 2);

      simulation.restart();
    }, 250);
  }

  // map link data (indices) to node ids
  data.links.forEach(function(e) {
    e.source = data.nodes[e.source].id;
    e.target = data.nodes[e.target].id;
  });

  drawGraph(data);

  // toggle affix.js on graph
  $('.ctd-container').affix({
    offset: {
      top: STICKY_OFFSET_TOP,
      bottom: document.querySelector('.tool > .container-fluid').getBoundingClientRect().height +
      document.querySelector('footer > nav').getBoundingClientRect().height + STICKY_OFFSET_BOTTOM
    }
  });

  // event handlers for export buttons
  document.querySelector('.btn-export--png').addEventListener('click', function() {
    saveSvgAsPng(document.querySelector('svg'), getFilename(filename, 'png'), {scale: 2.0});
  });

  document.querySelector('.btn-export--svg').addEventListener('click', function() {
    svgAsDataUri(document.querySelector('svg'), {}, function(uri) {
      var a = document.createElement('a');
      a.download = getFilename(filename, 'svg');
      a.href = uri;
      document.body.appendChild(a);
      a.click();
      a.parentNode.removeChild(a);
    });
  });

  document.querySelector('.btn-export--gexf').addEventListener('click', function() {
    var a = document.createElement('a');
    a.download = getFilename(filename, 'gexf');
    url = window.location.href.split('?')[0];
    url += '/graph.gexf';
    a.href = url;
    document.body.appendChild(a);
    a.click();
    a.parentNode.removeChild(a);
  });

  /**
   * Return a suggested filename for the exported graph
   */
  function getFilename(name, extension) {
    return name.replace(/[^a-z0-9]/gi, '-').toLowerCase() + '-graph.' + extension;
  }
})();