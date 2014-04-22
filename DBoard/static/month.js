nv.addGraph(function() {
    var chart = nv.models.multiBarChart()
      .transitionDuration(350)
      .reduceXTicks(true)   //If 'false', every single x-axis tick label will be rendered.
      .rotateLabels(0)      //Angle to rotate x-axis labels.
      .showControls(false)   //Allow user to switch between 'Grouped' and 'Stacked' mode.
      .groupSpacing(0.1)    //Distance between each group of bars.
      .stacked(true)
    ;

  chart.xAxis     //Chart x-axis settings
      .axisLabel('Month')
      .tickFormat(function(d) {
          return d3.time.format('%b-%d')(new Date(d))
    });

    chart.yAxis
        .tickFormat(d3.format(',.1f'));

    d3.select('#chart svg')
        .datum({{data | safe}})
        .call(chart);

    nv.utils.windowResize(chart.update);

    return chart;
});
