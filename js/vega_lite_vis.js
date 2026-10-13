var vg_1 = "js/chart01_generation_bar.vg.json?v=3";
var vg_2 = "js/chart02_cumulative_growth.vg.json?v=3";
var vg_3 = "js/chart03_waffle.vg.json?v=3";
var vg_4 = "js/chart04_type_heatmap.vg.json?v=3";
var vg_5 = "js/chart05_stats_boxplot.vg.json?v=3";
var vg_6 = "js/chart06_release_map.vg.json?v=3";


vegaEmbed("#generation_bar", vg_1, {
    actions: false
}).catch(console.error);


vegaEmbed("#cumulative_growth", vg_2, {
    actions: false
}).catch(console.error);


vegaEmbed("#waffle_chart", vg_3, {
    actions: false
}).catch(console.error);


vegaEmbed("#type_heatmap", vg_4, {
    actions: false
}).catch(console.error);


vegaEmbed("#stats_boxplot", vg_5, {
    actions: false
}).catch(console.error);


vegaEmbed("#release_map", vg_6, {
    actions: false
}).catch(console.error);