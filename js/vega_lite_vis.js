var vg_1 = "js/chart01_generation_bar.vg.json?v=2";
var vg_2 = "js/chart02_cumulative_growth.vg.json?v=2";
var vg_3 = "js/chart03_waffle.vg.json?v=2";


vegaEmbed("#generation_bar", vg_1, {
    actions: false
}).catch(console.error);


vegaEmbed("#cumulative_growth", vg_2, {
    actions: false
}).catch(console.error);


vegaEmbed("#waffle_chart", vg_3, {
    actions: false
}).catch(console.error);