/**
 * ConnectTheDots front-end code
 * Graph drawing adapted from https://bl.ocks.org/mbostock/4062045
 */
// (function() {
  var BACKGROUND_COLOR = '#fff',
      PRIMARY_COLORS = {default: '#10b0f7', hover: '#0076b3', active: '#41c0f9'},
      ALTERNATE_COLORS = {default: '#f75710', hover: '#b33d00', active: '#f97a41'},
      DISPLAY_RESOLUTION = 1.4,
      GRAPH_PADDING = .05,
      NODE_RADIUS = 6,
      NODE_STROKE = 2,
      EDGE_WIDTH = 1,
      ROUNDING_PRECISION = 3,
      TABLE_ROWS = 40,
      STICKY_OFFSET_TOP = -30,
      STICKY_OFFSET_BOTTOM = 80;

  // map link data (indices) to node ids, populate node neighbors
  data.nodes.forEach(function(n) {
    n.neighbors = [];
  });

  data.links.forEach(function(e) {
    data.nodes[e.source].neighbors.push(data.nodes[e.target].id);
    data.nodes[e.target].neighbors.push(data.nodes[e.source].id);

    e.source = data.nodes[e.source].id;
    e.target = data.nodes[e.target].id;
  });

  // setup SVG dimensions
  var svg = d3.select('svg'),
      container = d3.select('.ctd-container'),
      table = d3.select('.ctd-table');

  var padding = parseFloat(container.style('padding-left').slice(0, -2)),
      width = container.node().getBoundingClientRect().width - 2 * padding,
      height = width / DISPLAY_RESOLUTION,
      initWidth = width, initHeight = height,
      scale = {factor: 1, init: 1, dx: 0, dy: 0},
      menuHeight = document.querySelector('.ctd-menu').getBoundingClientRect().height;

  svg.attr('width', width)
     .attr('height', height)
     .style('background-color', BACKGROUND_COLOR);

  // setup simulation
  var center = d3.forceCenter(width / 2, height / 2),
      nodeDistance = d3.scaleLinear()
                       .domain([0, 0.1])
                       .range([25, 500])
                       .clamp(true); // maps density score to maximum node distance

  var simulation = d3.forceSimulation()
                     .force('charge', d3.forceManyBody().distanceMax(nodeDistance(density)))
                     .force('link', d3.forceLink().id(function(d) { return d.id; }))
                     .force('center', center);

  var ticksElapsed = 0,
      stableAt = Math.ceil(
                   Math.log(simulation.alphaMin()) / Math.log(1 - simulation.alphaDecay())
                 ); // number of ticks before graph reaches equilibrium

  // setup graphical elements and bind data
  var colorBy = bipartite ? 'column': 'community',
      communityColor = communities > 10 ? d3.scaleOrdinal(d3.schemeCategory20)
                                        : d3.scaleOrdinal(d3.schemeCategory10);

  var edge = svg.append('g')
                .classed('edges', true)
                .attr('aria-hidden', 'true')
                .selectAll('line').data(data.links)
                                  .enter().append('line')
                                  .style('opacity', 0)
                                  .attr('stroke-width', EDGE_WIDTH);

  var node = svg.append('g')
                .classed('nodes', true)
                .attr('role', 'group')
                .attr('aria-label', 'Network graph')
                .selectAll('circle').data(data.nodes)
                                    .enter().append('circle')
                                    .style('opacity', 0)
                                    .attr('r', NODE_RADIUS)
                                    .attr('stroke-width', NODE_STROKE)
                                    .attr('fill', function(d) { return fillColor(d); })
                                    .attr('id', function(d) { return d.id; })
                                    .attr('role', 'img')
                                    .attr('aria-label', function(d) {
                                      return 'Node ' + d.id + ' has a degree of ' + d.degree + 
                                      ' and a centrality of ' + parseFloat(d.centrality.toFixed(ROUNDING_PRECISION));
                                    });

  var row = table.append('tbody').selectAll('tr'),
      sort = {column: 'degree', order: -1};
  sortTable(sort.column, sort.order);

  var headers = table.select('thead').selectAll('th');
  headers.on('click', function() {
    var column = this.getAttribute('data-column');

    if (column === sort.column) {
      if (sort.order === 'asc') {
        sort.order = 'desc';
      } else {
        sort.order = 'asc';
      }
    } else {
      sort.column = column;
      sort.order = 'desc';
    }

    headers.classed('ctd-sort--asc', false)
           .classed('ctd-sort--desc', false);
    this.className = 'ctd-sort--' + sort.order;

    sortTable(sort.column, sort.order);
  });

  var progress = d3.select('.ctd-progress'),
      download = d3.select('.ctd-download > button'),
      colors = d3.select('.ctd-colors'), 
      tooltip = d3.select('.ctd-tooltip').style('display', 'none');

  var connector = d3.select('.ctd-meta--value');
  connector.datum(data.nodes.filter(function(d) { return d.id === connector.text().trim(); })[0]);

  // start simulation
  simulation.nodes(data.nodes)
            .on('tick', tickUpdate)
            .force('link').links(data.links);

  // event handlers for dragging and setting active node
  var activeNode;
  node.on('mouseover', mouseoverNode)
      .on('mouseout', mouseoutNode)
      .on('click', setActiveNode)
      .call(d3.drag().on('start', dragStart)
                     .on('drag', dragUpdate)
                     .on('end', dragEnd));

  svg.on('click', function() { if (d3.event.target.tagName !== 'circle') clearActiveNode(); });

  /**
   * Return node fill color
   */
  function fillColor(d, state) {
    var state = (typeof state !== 'undefined') ? state : 'default';

    if (colorBy === 'column') {
      return d.column === 0 ? PRIMARY_COLORS[state] : ALTERNATE_COLORS[state];
    } else if (colorBy === 'community') {
      if (state === 'hover') {
        return d3.color(communityColor(d.community)).darker() + '';
      } else if (state === 'active') {
        return d3.color(communityColor(d.community)).brighter() + '';
      } else {
        return communityColor(d.community);
      }
    } else {
      return PRIMARY_COLORS[state];
    }
  }

  /**
   * Highlight a node in the graph and table
   */
  function mouseoverNode(d) {
    if (!activeNode) {
      if (d3.event.target.tagName === 'circle') showTooltip(d);

      node.filter(function(n) { return n.id !== d.id && d.neighbors.indexOf(n.id) < 0; })
          .classed('blur', true);
      edge.filter(function(e) { return e.source.id !== d.id && e.target.id !== d.id; })
          .classed('blur', true);
    }

    node.filter(function(n) { return n.id === d.id; })
        .classed('hover', true)
        .attr('fill', function(d) {
          return activeNode !== d.id ? fillColor(d, 'hover') : fillColor(d, 'active')
        });
    row.filter(function(r) { return r.id === d.id; })
       .classed('hover', true);
  }

  /**
   * De-highlight a node in the graph and table
   */
  function mouseoutNode(d) {
    if (!activeNode) {
      tooltip.classed('in', false);
      node.classed('blur', false);
      edge.classed('blur', false);
    }

    node.classed('hover', false)
        .attr('fill', function(d) {
          return activeNode !== d.id ? fillColor(d) : fillColor(d, 'active');
        });
    row.classed('hover', false);
  }

  /**
   * Set the active node
   */
  function setActiveNode(d) {
    if (activeNode !== d.id) {
      clearActiveNode();
      activeNode = d.id;

      node.filter(function(d) {return d.id === activeNode; })
          .classed('active', true)
          .attr('fill', function(d) { return fillColor(d, 'active'); });
      row.filter(function(d) { return d.id === activeNode; })
         .classed('active', true);

      node.filter(function(n) { return n.id !== d.id && d.neighbors.indexOf(n.id) < 0; })
          .classed('blur', true);
      edge.filter(function(e) { return e.source.id !== d.id && e.target.id !== d.id; })
          .classed('blur', true);

      showTooltip(d);
      tooltip.style('width', getTooltipSize().width + 'px');
    }
  }

  /**
   * Clear the active node
   */
  function clearActiveNode() {
    activeNode = null;
    node.classed('active', false)
        .classed('blur', false)
        .attr('fill', function(d) { return fillColor(d); });
    edge.classed('blur', false);
    row.classed('active', false);
    tooltip.classed('in', false)
           .style('width', 'auto');
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
             return d ? d.y * scale.factor + scale.dy - getTooltipSize().height + menuHeight + 'px' : 0;
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
   * Sort table by column name and ascending/descending order
   */
  function sortTable(column, order) {
    var subset = data.nodes.sort(function(a, b) {
                   if (order === 'asc') {
                     return d3.ascending(a[column], b[column]) || d3.ascending(a.id, b.id);
                   } else {
                     return d3.descending(a[column], b[column]) || d3.ascending(a.id, b.id);
                   }
                 }).slice(0, TABLE_ROWS);

    var update = row.data(subset, function(d) { return d.id; });

    var enter = update.enter().append('tr')
                              .attr('id', function(d) { return d.id; })
                              .on('mouseover', mouseoverNode)
                              .on('mouseout', mouseoutNode)
                              .on('click', setActiveNode);

    enter.append('td').html(function(d) { return d.id; });
    enter.append('td').html(function(d) { return d.degree; });
    enter.append('td').html(function(d) { return parseFloat(d.centrality.toFixed(ROUNDING_PRECISION)); });

    update.exit().remove();

    row = enter.merge(update).order();
  }

  /**
   * Update positions of nodes/edges at each tick
   */
  function tickUpdate() {
    ticksElapsed++;
    if (ticksElapsed < stableAt) {
      progress.style('width', width * ticksElapsed / stableAt + 'px');
    } else if (ticksElapsed === stableAt) {
      rescaleGraph();

      progress.remove();
      node.style('opacity', 1);
      edge.style('opacity', 1);
      download.style('visibility', 'visible')
              .style('opacity', 1);
      colors.style('visibility', 'visible')
            .style('opacity', 1);
      tooltip.style('display', 'block');

      connector.on('mouseover', mouseoverNode)
               .on('mouseout', mouseoutNode)
               .on('click', setActiveNode);
    }

    // set node positions, bounded within graph area
    node.attr('cx', function(d) {
          var xMin = (NODE_RADIUS + width * GRAPH_PADDING - scale.dx) / scale.factor,
              xMax = (width * (1 - GRAPH_PADDING) - NODE_RADIUS - scale.dx) / scale.factor;
          return d.x = Math.max(xMin, Math.min(xMax, d.x));
        })
        .attr('cy', function(d) {
          var yMin = (NODE_RADIUS + height * GRAPH_PADDING - scale.dy) / scale.factor,
              yMax = (height * (1 - GRAPH_PADDING) - NODE_RADIUS - scale.dy) / scale.factor;
          return d.y = Math.max(yMin, Math.min(yMax, d.y));
        });

    // set edge positions
    edge.attr('x1', function(d) { return d.source.x; })
        .attr('y1', function(d) { return d.source.y; })
        .attr('x2', function(d) { return d.target.x; })
        .attr('y2', function(d) { return d.target.y; });

    positionTooltip();
  }

  /**
   * Rescale the graph to fit some proportion of the SVG bounds
   */
  function rescaleGraph(k) {
    if (k) {
      scale.factor = k;
    } else {
      var bbox = svg.select('.nodes').node().getBBox();
      scale.factor = Math.min(width / bbox.width, height / bbox.height) * (1 - 2 * GRAPH_PADDING);
      scale.init = scale.factor;
    }

    scale.dx = -width / 2 * (scale.factor - 1),
    scale.dy = -height / 2 * (scale.factor - 1);

    svg.selectAll('g')
       .attr('transform', 'translate(' + scale.dx + ', ' + scale.dy + ') scale(' + scale.factor + ')');
  }

  // rescale graph on window resize
  window.onresize = _.debounce(function() {
    padding = parseFloat(container.style('padding-left').slice(0, -2)),
    width = container.node().getBoundingClientRect().width - 2 * padding,
    height = width / DISPLAY_RESOLUTION;

    svg.attr('width', width)
       .attr('height', height);
  
    rescaleGraph(scale.init * width / initWidth);

    center.x(width / 2)
          .y(height / 2);

    simulation.restart();

    $('.ctd-meta').css('width', width);
  }, 250);

  $('.ctd-meta').css('width', width);

  // sticky scrolling behavior on graph/table
  if (document.querySelector('.ctd-table').getBoundingClientRect().height >
      document.querySelector('.ctd-container').getBoundingClientRect().height) {
    $('.ctd-container').affix({
      offset: {
        top: document.querySelector('.ctd-container').getBoundingClientRect().top +
        window.pageYOffset + STICKY_OFFSET_TOP,
        bottom: document.querySelector('.tool > .bottom-section').getBoundingClientRect().height +
        document.querySelector('footer > nav').getBoundingClientRect().height + STICKY_OFFSET_BOTTOM
      }
    });
  }

  $('.ctd-table').floatThead({
    floatContainerClass: 'ctd-thwrap',
    enableAria: true
  });

  // event handlers for export buttons
  document.querySelector('.btn-download--png').addEventListener('click', function() {
    clearActiveNode();
    saveSvgAsPng(document.querySelector('svg'), getFilename(filename, 'png'), {scale: 2.0});
  });

  document.querySelector('.btn-download--svg').addEventListener('click', function() {
    clearActiveNode();
    svgAsDataUri(document.querySelector('svg'), {}, function(uri) {
      var a = document.createElement('a');
      a.download = getFilename(filename, 'svg');
      a.href = uri;
      document.body.appendChild(a);
      a.click();
      a.parentNode.removeChild(a);
    });
  });

  document.querySelector('.btn-download--gexf').addEventListener('click', function() {
    var a = document.createElement('a');
    a.download = getFilename(filename, 'gexf');
    a.href = window.location.href.split(/[#?]/)[0] + '/graph.gexf';
    document.body.appendChild(a);
    a.click();
    a.parentNode.removeChild(a);
  });

  document.querySelector('.btn-download--table').addEventListener('click', function() {
    var a = document.createElement('a');
    a.download = getFilename(filename, 'csv');
    a.href = window.location.href.split(/[#?]/)[0] + '/table.csv';
    document.body.appendChild(a);
    a.click();
    a.parentNode.removeChild(a);
  });

  /**
   * Return a suggested filename for the exported graph
   */
  function getFilename(name, extension) {
    return name.replace(/[^a-z0-9]/gi, '-').toLowerCase() + '.' + extension;
  }

  // event handler for color switcher
  document.querySelectorAll('input[name="node-color"]').forEach(function(radio) {
    radio.addEventListener('click', function() {
      if (colorBy !== this.value) {
        colorBy = this.value;
        node.attr('fill', function(d) {
          return activeNode !== d.id ? fillColor(d) : fillColor(d, 'active');
        });
      }
    });
  })
// })();