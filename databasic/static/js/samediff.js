function renderSimilarityChart(elementSelector, dataset){

  console.log("renderSimilarityChart to "+elementSelector);

  var width = 520,
      height = 280,
      formatPercent = d3.format(".0%"),
      formatNumber = d3.format(".0f");

  var threshold = d3.scale.threshold()
      .domain([.5, 0.7, 0.8, 0.9])
      .range( ["#e66101", "#fdb863", "#999999", "#b2abd2", "#5e3c99"] );

  // A position encoding for the key only.
  var chartWidth = 450;

  var x = d3.scale.linear()
      .domain([0, 1])
      .range([0, chartWidth]); // the width of the chart

  var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom")
      .tickSize(13)
      .tickValues(threshold.domain())
      .tickFormat(function(d) { return d; });

  var svg = d3.select(elementSelector).append("svg")
      .attr("width", width)
      .attr("height", height);

  var g = svg.append("g")
      .attr("class", "key")
      .attr("transform", "translate(" + (width - chartWidth) / 2 + "," + 50 + ")");

  g.selectAll("rect")
      .data(threshold.range().map(function(color) {
        var d = threshold.invertExtent(color);
        if (d[0] == null) d[0] = x.domain()[0];
        if (d[1] == null) d[1] = x.domain()[1];
        return d;
      }))
    .enter().append("rect")
      .attr("height", 10)
      .attr("x", function(d) { return x(d[0]); })
      .attr("width", function(d) { return x(d[1]) - x(d[0]); })
      .style("fill", function(d) { return threshold(d[0]); });

  g.call(xAxis);

  g.append("text")
      .attr("class", "caption")
      .attr("y", -6)
      .text("Totally different");
  g.append("text")
      .attr("class", "caption")
      .attr("y", -6)
      .attr("x", x.range()[1])
      .text("Totally the same")
      .style("text-anchor", "end");

  var g2 = svg.append("g")
      .attr("class", "key")
      .attr("transform", "translate(40,100)");
  var yOffset = 0;
  var xOffset = 0;
  for(r=0;r<dataset.length;r++){
    docNames = dataset[r];
    var score = 0.97;
    if(r<threshold.domain().length){
      score = threshold.domain()[r]-0.01;
    } 
    var scoreColor = threshold(score);
    var maxTxtWidth = 0;
    for(d=0;d<docNames.length;d++){
      var txt = g2.append("text")
        .attr("y", yOffset)
          .attr("x", xOffset)
          .attr("class","doc-name")
          .text(docNames[d])
          .attr("fill",scoreColor);
      maxTxtWidth = Math.max(maxTxtWidth,txt.node().getBBox().width)
      yOffset += 20;
    }
    if(docNames.length>0){
      g2.append("line")
        .style("stroke",scoreColor)
        .attr("x1",x(score)-20)
        .attr("y1",-40)
        .attr("x2",x(score)-20)
        .attr("y2",yOffset-25);
      g2.append("line")
        .style("stroke",scoreColor)
        .attr("x1",xOffset+maxTxtWidth+10)
        .attr("y1",yOffset-25)
        .attr("x2",x(score)-20)
        .attr("y2",yOffset-25);
      yOffset += 10;
    }
    xOffset += 40;
  }
}

diffWordCloudDestination = null;

function renderDiffWordCloud(elementSelector, dataset){
  var maxScore = Math.max.apply(Math,dataset.map(function(o){return o.score;}))
  var fontSizeScale = d3.scale.linear()
      .domain([0, maxScore])
      .range([0, 40]); 
  console.log("renderDiffChart to "+elementSelector);
  diffWordCloudDestination = elementSelector;
  var layout =  d3.layout.cloud()
    .size([420, 250])
    .words(dataset)
    .padding(5)
    .rotate(0)
    .fontSize(function(d) { return fontSizeScale(d.score); })
    .on("end", drawDiffWordCloud);
  layout.start();
}

function drawDiffWordCloud(words) {
  console.log("drawDiffWordCloud to "+diffWordCloudDestination);
  var chartWidth = 520;
  d3.select(diffWordCloudDestination).append("svg")
      .attr("width", chartWidth)
      .attr("height", 260)
    .append("g")
      .attr("transform", "translate(" + chartWidth/2 + "," + 125 + ")")
    .selectAll("text")
      .data(words)
    .enter().append("text")
      .style("font-size", function(d) { return d.size + "px"; })
      .attr("text-anchor", "middle")
      .attr("transform", function(d) {
        return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
      })
      .text(function(d) { return d.text; });
}
