var vg_1 = "js/test_chart.vg.json";

vegaEmbed("#test_chart", vg_1, {
    actions: false
}).then(function(result) {
    console.log("Vega-Lite visualisation loaded.");
}).catch(console.error);