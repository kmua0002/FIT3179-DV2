var vg_1 = "js/chart01_generation_bar.vg.json?v=2";

vegaEmbed("#generation_bar", vg_1, {
    actions: false
}).then(function(result) {
    console.log("Vega-Lite visualisation loaded.");
}).catch(console.error);