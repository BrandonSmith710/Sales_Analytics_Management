function plotSales(products, productCounts) {
    plot1 = document.getElementById('plot1');
    var layout = {
        xaxis: {range: [1, 5],
                title: {text: 'Product Sales'},
                visible: false},
        title: 'Top 5 Best Sellers: ' + products,
    };
    Plotly.newPlot( plot1, [{
    x: [1, 2, 3, 4, 5],
    y: productCounts,
    type: 'bar' ,
    marker: {color: 'brown'}
    }], 
    layout, {
    margin: { t: 0 } } );

};

function plotTimes(times, timeCounts) {
    plot2 = document.getElementById('plot2');
    var data = [{
        values: timeCounts,
        labels: times,
        type: 'pie'
      }];
      
      var layout = {
        height: 300,
        width: 751,
        title: 'Times of Sale Over Past Week'
      };
      
      Plotly.newPlot(plot2, data, layout);
};




function plotBubbleMap(element, latitudes, longitudes, cityVolume) {
    var scale = [];
    for (let i = 0; i < cityVolume.length; i++) {
        scale.push(cityVolume[i] ** 3);
    };
    var data = [{
        type: 'scattergeo',
        locationmode: 'USA-states',  //locationmode lat lon
        lat: latitudes,
        lon: longitudes,
        marker: {
            reversescale: true,
            autocolorscale: false,
            sizemax: 20,
            sizemode: 'diameter',
            line: {
                color: 'black',
                width: 2
            },
        },
    }];
    
    var layout = {
        geo: {
        scope: 'usa',
        projection: {
            type: 'albers usa'
        },
        showland: true,
        subunitwidth: 1,
        countrywidth: 1,
        subunitcolor: 'rgb(255,255,255)',
        countrycolor: 'rgb(255,255,255)',
        height: 520,
        width: 751
        }
    };
    
    Plotly.newPlot(element, data, layout, {showlink: false});
};

function plotDaysOfWeek(daysOfWeek, dayCounts) {
    plot4 = document.getElementById('plot4');
    var data = [{
        x: daysOfWeek,
        y: dayCounts,
        type: 'scatter',
        marker: {
            color: 'purple',
            size: 10
        }

    }];
    var layout = {
        yaxis: {
            title: 'Sales',
        },
        height: 320,
        width: 751,
        title: 'Monday(1) Through Sunday(7) - Past 4 Weeks',
    };
    Plotly.newPlot(plot4, data, layout);
};


function plotStateCounts(states, stateCounts) {
    plot5 = document.getElementById('plot5')
    var data = [{
        x: states,
        y: stateCounts,
        type: 'bar',
        marker: {
            color: 'orange',
        }
      }];

      var layout = {
        showlegend: false,
        height: 460,
        width: 751
      };
      
      Plotly.newPlot(plot5, data, layout);
};
